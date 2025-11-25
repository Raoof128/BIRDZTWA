"""
API Models - Pydantic Schemas

Request and response models for the Browser Isolation API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class RenderRequest(BaseModel):
    """Request to render a URL."""

    url: str = Field(..., description="URL to isolate and render")
    timeout: int = Field(30, ge=5, le=120, description="Timeout in seconds")
    wait_for_load: bool = Field(True, description="Wait for full page load")
    block_trackers: bool = Field(True, description="Block tracking elements")

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class RenderStatus(BaseModel):
    """Status of a render operation."""

    render_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    url: str
    progress: int = Field(..., ge=0, le=100)
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class RenderResponse(BaseModel):
    """Response from render operation."""

    render_id: str
    url: str
    status: str
    html: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    blocked_content: List[Dict[str, str]] = []
    risk_score: float = Field(..., ge=0.0, le=10.0)
    timestamp: datetime


class PolicyCheckRequest(BaseModel):
    """Request to check URL policy."""

    url: str = Field(..., description="URL to check")


class PolicyCheckResponse(BaseModel):
    """Response from policy check."""

    url: str
    allowed: bool
    reason: str
    risk_level: str
    matched_rules: List[str]


class AuditLogEntry(BaseModel):
    """Single audit log entry."""

    timestamp: datetime
    event_type: str
    url: Optional[str] = None
    render_id: Optional[str] = None
    user: Optional[str] = None
    action: str
    details: Dict[str, Any]
    risk_score: Optional[float] = None


class AuditLogResponse(BaseModel):
    """Response with audit logs."""

    total: int
    entries: List[AuditLogEntry]
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    uptime_seconds: float
    chromium_available: bool
    active_renders: int
    total_renders: int


class PolicySummaryResponse(BaseModel):
    """Summary of active policies."""

    blocked_domains_count: int
    allowed_domains_count: int
    blocked_categories: List[str]
    blocked_patterns_count: int
    allowed_patterns_count: int
    malware_domains_count: int
    phishing_domains_count: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
