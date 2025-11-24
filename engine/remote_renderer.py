"""
Remote Renderer - Safe DOM Snapshot Generator

Builds a safe, serialized representation of the sanitized DOM
that can be transmitted to the client for display.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RenderMetadata:
    """Metadata about the rendered page."""

    url: str
    timestamp: str
    render_id: str
    original_size: int
    sanitized_size: int
    fetch_time: float
    sanitization_time: float
    risk_score: float
    removed_elements: Dict[str, int]
    status: str  # 'success', 'partial', 'failed'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SafeDOM:
    """Safe DOM snapshot for client rendering."""

    html: str
    metadata: RenderMetadata
    resources: List[Dict[str, Any]]
    warnings: List[str]
    blocked_content: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "html": self.html,
            "metadata": self.metadata.to_dict(),
            "resources": self.resources,
            "warnings": self.warnings,
            "blocked_content": self.blocked_content,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class RemoteRenderer:
    """
    Creates safe DOM snapshots from sanitized HTML.

    This component packages the sanitized content with metadata
    and resources for safe transmission to the client.
    """

    def __init__(
        self,
        include_metadata: bool = True,
        include_resources: bool = True,
        include_warnings: bool = True,
        max_html_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """
        Initialize remote renderer.

        Args:
            include_metadata: Include render metadata
            include_resources: Include resource information
            include_warnings: Include security warnings
            max_html_size: Maximum allowed HTML size in bytes
        """
        self.include_metadata = include_metadata
        self.include_resources = include_resources
        self.include_warnings = include_warnings
        self.max_html_size = max_html_size

    def render(
        self,
        url: str,
        sanitized_html: str,
        sanitization_result: Any,
        fetch_result: Optional[Any] = None,
        render_id: Optional[str] = None,
    ) -> SafeDOM:
        """
        Create a safe DOM snapshot from sanitized HTML.

        Args:
            url: Original URL
            sanitized_html: Sanitized HTML content
            sanitization_result: Result from DOMSanitizer
            fetch_result: Optional FetchResult from RemoteFetcher
            render_id: Optional unique render ID

        Returns:
            SafeDOM object ready for transmission

        Raises:
            ValueError: If HTML exceeds size limit
        """
        logger.info(f"Rendering safe DOM snapshot for: {url}")

        # Check size limit
        html_size = len(sanitized_html)
        if html_size > self.max_html_size:
            raise ValueError(
                f"Sanitized HTML size ({html_size} bytes) exceeds "
                f"maximum allowed ({self.max_html_size} bytes)"
            )

        # Generate render ID if not provided
        if not render_id:
            render_id = self._generate_render_id(url)

        # Build metadata
        metadata = self._build_metadata(
            url=url,
            render_id=render_id,
            sanitization_result=sanitization_result,
            fetch_result=fetch_result,
            html_size=html_size,
        )

        # Extract resources
        resources = []
        if self.include_resources and fetch_result:
            resources = self._extract_resources(fetch_result)

        # Build warnings
        warnings = []
        if self.include_warnings:
            warnings = self._build_warnings(sanitization_result)

        # Build blocked content list
        blocked_content = self._build_blocked_content(sanitization_result)

        # Create SafeDOM
        safe_dom = SafeDOM(
            html=sanitized_html,
            metadata=metadata,
            resources=resources,
            warnings=warnings,
            blocked_content=blocked_content,
        )

        logger.info(
            f"Safe DOM rendered successfully - "
            f"ID: {render_id}, Size: {html_size} bytes, "
            f"Risk: {metadata.risk_score}/10, "
            f"Warnings: {len(warnings)}, Blocked: {len(blocked_content)}"
        )

        return safe_dom

    def _generate_render_id(self, url: str) -> str:
        """Generate unique render ID."""
        import hashlib

        timestamp = datetime.now().isoformat()
        unique_string = f"{url}:{timestamp}"
        hash_digest = hashlib.sha256(unique_string.encode()).hexdigest()
        return f"render-{hash_digest[:16]}"

    def _build_metadata(
        self,
        url: str,
        render_id: str,
        sanitization_result: Any,
        fetch_result: Optional[Any],
        html_size: int,
    ) -> RenderMetadata:
        """Build render metadata."""

        # Extract removed elements counts
        removed_elements = {
            "scripts": sanitization_result.removed_scripts,
            "event_handlers": sanitization_result.removed_event_handlers,
            "iframes": sanitization_result.removed_iframes,
            "trackers": sanitization_result.removed_trackers,
        }

        # Calculate times
        fetch_time = fetch_result.fetch_time if fetch_result else 0.0
        sanitization_time = 0.0  # Could be tracked in sanitizer

        # Determine status
        status = "success"
        if sanitization_result.risk_score >= 7.0:
            status = "partial"  # High risk, might have issues

        return RenderMetadata(
            url=url,
            timestamp=datetime.now().isoformat(),
            render_id=render_id,
            original_size=sanitization_result.original_size,
            sanitized_size=html_size,
            fetch_time=fetch_time,
            sanitization_time=sanitization_time,
            risk_score=sanitization_result.risk_score,
            removed_elements=removed_elements,
            status=status,
        )

    def _extract_resources(self, fetch_result: Any) -> List[Dict[str, Any]]:
        """Extract resource information from fetch result."""
        resources = []

        if hasattr(fetch_result, "resources"):
            # Limit number of resources to prevent bloat
            max_resources = 100
            for resource in fetch_result.resources[:max_resources]:
                resources.append(
                    {
                        "type": resource.get("type", "unknown"),
                        "url": resource.get("url", ""),
                        "status": resource.get("status", ""),
                        "resource_type": resource.get("resource_type", ""),
                    }
                )

        return resources

    def _build_warnings(self, sanitization_result: Any) -> List[str]:
        """Build security warnings based on sanitization results."""
        warnings = []

        # High script count warning
        if sanitization_result.removed_scripts > 10:
            warnings.append(
                f"High JavaScript usage: Removed {sanitization_result.removed_scripts} scripts. "
                "Page may not function correctly in isolated mode."
            )

        # Event handlers warning
        if sanitization_result.removed_event_handlers > 50:
            warnings.append(
                f"Heavy event handler usage: Removed {sanitization_result.removed_event_handlers} handlers. "
                "Interactive features disabled."
            )

        # Suspicious content warning
        if sanitization_result.suspicious_content:
            warnings.append(
                f"Suspicious patterns detected: {len(sanitization_result.suspicious_content)} instances. "
                "This page may have contained malicious code."
            )

        # High risk score warning
        if sanitization_result.risk_score >= 7.0:
            warnings.append(
                f"HIGH RISK PAGE (Score: {sanitization_result.risk_score}/10). "
                "This page contained significant threats. View with caution."
            )
        elif sanitization_result.risk_score >= 5.0:
            warnings.append(
                f"Medium risk page (Score: {sanitization_result.risk_score}/10). "
                "Some threats were detected and removed."
            )

        # Blocked URLs warning
        if len(sanitization_result.blocked_urls) > 5:
            warnings.append(
                f"Multiple dangerous URLs blocked: {len(sanitization_result.blocked_urls)} instances."
            )

        # Tracker warning
        if sanitization_result.removed_trackers > 0:
            warnings.append(
                f"Privacy protection: Removed {sanitization_result.removed_trackers} tracking elements."
            )

        return warnings

    def _build_blocked_content(self, sanitization_result: Any) -> List[Dict[str, str]]:
        """Build list of blocked content items."""
        blocked = []

        # Add scripts
        if sanitization_result.removed_scripts > 0:
            blocked.append(
                {
                    "type": "scripts",
                    "count": str(sanitization_result.removed_scripts),
                    "description": "JavaScript code removed for security",
                    "risk": "high",
                }
            )

        # Add event handlers
        if sanitization_result.removed_event_handlers > 0:
            blocked.append(
                {
                    "type": "event_handlers",
                    "count": str(sanitization_result.removed_event_handlers),
                    "description": "Interactive event handlers stripped",
                    "risk": "medium",
                }
            )

        # Add iframes
        if sanitization_result.removed_iframes > 0:
            blocked.append(
                {
                    "type": "iframes",
                    "count": str(sanitization_result.removed_iframes),
                    "description": "Embedded frames blocked",
                    "risk": "high",
                }
            )

        # Add trackers
        if sanitization_result.removed_trackers > 0:
            blocked.append(
                {
                    "type": "trackers",
                    "count": str(sanitization_result.removed_trackers),
                    "description": "Tracking and analytics removed",
                    "risk": "low",
                }
            )

        # Add blocked URLs
        for url in sanitization_result.blocked_urls[:10]:  # Limit to 10
            blocked.append(
                {
                    "type": "dangerous_url",
                    "count": "1",
                    "description": f"Malicious URL: {url[:100]}",
                    "risk": "high",
                }
            )

        return blocked

    def render_error_page(
        self, url: str, error_message: str, error_type: str = "fetch_error"
    ) -> SafeDOM:
        """
        Render an error page when fetch or sanitization fails.

        Args:
            url: URL that failed
            error_message: Error description
            error_type: Type of error

        Returns:
            SafeDOM with error page
        """
        logger.warning(f"Rendering error page for {url}: {error_message}")

        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Isolation Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .error-box {{
                    background: white;
                    border-left: 4px solid #d32f2f;
                    padding: 20px;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #d32f2f; }}
                .url {{
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 4px;
                    word-break: break-all;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>⚠️ Browser Isolation Error</h1>
                <p><strong>Type:</strong> {error_type}</p>
                <p><strong>URL:</strong></p>
                <div class="url">{url}</div>
                <p><strong>Error:</strong> {error_message}</p>
                <hr>
                <p>This page could not be isolated safely. Possible reasons:</p>
                <ul>
                    <li>Network connectivity issues</li>
                    <li>URL is blocked by policy</li>
                    <li>Server returned an error</li>
                    <li>Content is too dangerous to render</li>
                    <li>Timeout during fetch</li>
                </ul>
            </div>
        </body>
        </html>
        """

        metadata = RenderMetadata(
            url=url,
            timestamp=datetime.now().isoformat(),
            render_id=self._generate_render_id(url),
            original_size=0,
            sanitized_size=len(error_html),
            fetch_time=0.0,
            sanitization_time=0.0,
            risk_score=0.0,
            removed_elements={},
            status="failed",
        )

        return SafeDOM(
            html=error_html,
            metadata=metadata,
            resources=[],
            warnings=[f"Error: {error_message}"],
            blocked_content=[],
        )
