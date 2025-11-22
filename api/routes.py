"""
API Routes - REST Endpoints

Defines all API endpoints for the Browser Isolation system.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import (
    RenderRequest,
    RenderResponse,
    RenderStatus,
    PolicyCheckRequest,
    PolicyCheckResponse,
    AuditLogResponse,
    HealthResponse,
    PolicySummaryResponse,
    ErrorResponse,
)
from engine import RemoteFetcher, DOMSanitizer, RemoteRenderer, PolicyChecker
from logging_mod.events import AuditLogger

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["isolation"])

from typing import Dict, Any, TypedDict


class Stats(TypedDict):
    total_renders: int
    active_renders: int
    start_time: datetime


# Global state (in production, use proper state management)
render_jobs: Dict[str, Any] = {}
stats: Stats = {"total_renders": 0, "active_renders": 0, "start_time": datetime.now()}

# Initialize components
policy_checker = PolicyChecker()
audit_logger = AuditLogger()


@router.post("/render", response_model=RenderResponse)
async def render_url(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render a URL in isolated browser and return safe DOM.

    This endpoint:
    1. Checks URL against policies
    2. Fetches URL in headless browser
    3. Sanitizes DOM
    4. Returns safe content
    """
    logger.info(f"Render request received for: {request.url}")

    try:
        # Check policy first
        policy_decision = policy_checker.check_url(request.url)

        if not policy_decision.allowed:
            audit_logger.log_event(
                event_type="render_blocked",
                url=request.url,
                action="block",
                details={
                    "reason": policy_decision.reason,
                    "risk_level": policy_decision.risk_level,
                    "matched_rules": policy_decision.matched_rules,
                },
            )

            raise HTTPException(
                status_code=403, detail=f"URL blocked by policy: {policy_decision.reason}"
            )

        # Update stats with proper type conversion
        stats["active_renders"] = int(stats["active_renders"]) + 1
        stats["total_renders"] = int(stats["total_renders"]) + 1

        # Fetch URL
        fetcher = RemoteFetcher(timeout=request.timeout * 1000)
        async with fetcher:
            fetch_result = await fetcher.fetch(request.url, wait_for_load=request.wait_for_load)

        # Sanitize DOM
        sanitizer = DOMSanitizer(remove_trackers=request.block_trackers)
        sanitization_result = sanitizer.sanitize(fetch_result.html)

        # Render safe DOM
        renderer = RemoteRenderer()
        safe_dom = renderer.render(
            url=request.url,
            sanitized_html=sanitization_result.safe_html,
            sanitization_result=sanitization_result,
            fetch_result=fetch_result,
        )

        # Log audit event
        audit_logger.log_event(
            event_type="render_success",
            url=request.url,
            render_id=safe_dom.metadata.render_id,
            action="render",
            details={
                "risk_score": safe_dom.metadata.risk_score,
                "removed_scripts": sanitization_result.removed_scripts,
                "removed_event_handlers": sanitization_result.removed_event_handlers,
                "removed_iframes": sanitization_result.removed_iframes,
                "fetch_time": fetch_result.fetch_time,
                "original_size": sanitization_result.original_size,
                "sanitized_size": sanitization_result.sanitized_size,
            },
            risk_score=safe_dom.metadata.risk_score,
        )

        # Update stats with proper type conversion
        stats["active_renders"] = max(0, int(stats["active_renders"]) - 1)

        # Build response
        return RenderResponse(
            render_id=safe_dom.metadata.render_id,
            url=request.url,
            status="completed",
            html=safe_dom.html,
            metadata=safe_dom.metadata.to_dict(),
            warnings=safe_dom.warnings,
            blocked_content=safe_dom.blocked_content,
            risk_score=safe_dom.metadata.risk_score,
            timestamp=datetime.now(),
        )

    except HTTPException:
        stats["active_renders"] = max(0, int(stats["active_renders"]) - 1)
        raise

    except Exception as e:
        stats["active_renders"] = max(0, int(stats["active_renders"]) - 1)
        logger.error(f"Error rendering {request.url}: {e}", exc_info=True)

        audit_logger.log_event(
            event_type="render_error", url=request.url, action="error", details={"error": str(e)}
        )

        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.post("/check-url", response_model=PolicyCheckResponse)
async def check_url_policy(request: PolicyCheckRequest):
    """
    Check if a URL is allowed by policy without rendering.
    """
    logger.info(f"Policy check for: {request.url}")

    decision = policy_checker.check_url(request.url)

    audit_logger.log_event(
        event_type="policy_check",
        url=request.url,
        action="check",
        details={
            "allowed": decision.allowed,
            "reason": decision.reason,
            "risk_level": decision.risk_level,
        },
    )

    return PolicyCheckResponse(
        url=request.url,
        allowed=decision.allowed,
        reason=decision.reason,
        risk_level=decision.risk_level,
        matched_rules=decision.matched_rules,
    )


@router.get("/audit", response_model=AuditLogResponse)
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
):
    """
    Retrieve audit logs.
    """
    logger.info(f"Audit log request: limit={limit}, offset={offset}")

    logs = audit_logger.get_logs(limit=limit, offset=offset, event_type=event_type)

    # Convert dicts to AuditLogEntry objects
    entries = [
        AuditLogEntry(
            timestamp=datetime.fromisoformat(log["timestamp"]),
            event_type=log["event_type"],
            url=log.get("url"),
            render_id=log.get("render_id"),
            user=log.get("user"),
            action=log["action"],
            details=log["details"],
            risk_score=log.get("risk_score"),
        )
        for log in logs
    ]

    return AuditLogResponse(total=len(entries), entries=entries)


@router.get("/policies", response_model=PolicySummaryResponse)
async def get_policies():
    """
    Get active policy configuration summary.
    """
    summary = policy_checker.get_policy_summary()
    return PolicySummaryResponse(**summary)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    """
    uptime = (datetime.now() - stats["start_time"]).total_seconds()

    # Check if Playwright/Chromium is available
    chromium_available = True
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        chromium_available = False

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=float(uptime),  # Convert to float to match the expected type
        chromium_available=chromium_available,
        active_renders=int(stats["active_renders"]),  # Ensure int type
        total_renders=int(stats["total_renders"]),  # Ensure int type
    )


@router.get("/status/{render_id}", response_model=RenderStatus)
async def get_render_status(render_id: str):
    """
    Get status of a render operation (for async implementations).
    """
    # Placeholder for async render tracking
    if render_id not in render_jobs:
        raise HTTPException(status_code=404, detail=f"Render job {render_id} not found")

    return render_jobs[render_id]
