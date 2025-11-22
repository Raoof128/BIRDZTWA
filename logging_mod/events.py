"""
Event Logging - Structured Audit Trail

Provides comprehensive audit logging for all isolation operations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict


class EventType(str, Enum):
    """Types of audit events."""
    
    RENDER_SUCCESS = "render_success"
    RENDER_BLOCKED = "render_blocked"
    RENDER_ERROR = "render_error"
    POLICY_CHECK = "policy_check"
    SANITIZATION = "sanitization"
    THREAT_DETECTED = "threat_detected"
    API_REQUEST = "api_request"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"


@dataclass
class AuditEvent:
    """Single audit event."""
    
    timestamp: datetime
    event_type: str
    url: Optional[str]
    render_id: Optional[str]
    user: Optional[str]
    action: str
    details: Dict[str, Any]
    risk_score: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for browser isolation events.
    
    Logs all security-relevant events to structured JSON log files
    for compliance, forensics, and monitoring.
    """

    def __init__(
        self,
        log_file: str = "logs/isolation_audit.log",
        json_format: bool = True,
        console_output: bool = True
    ):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file
            json_format: Use JSON format for logs
            console_output: Also log to console
        """
        self.log_file = Path(log_file)
        self.json_format = json_format
        self.console_output = console_output
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up Python logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        if json_format:
            file_handler.setFormatter(
                logging.Formatter('%(message)s')
            )
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(file_handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - AUDIT - %(message)s'
                )
            )
            self.logger.addHandler(console_handler)
        
        # In-memory cache for recent events (for API queries)
        self._event_cache: List[AuditEvent] = []
        self._cache_max_size = 1000

    def log_event(
        self,
        event_type: str,
        action: str,
        details: Dict[str, Any],
        url: Optional[str] = None,
        render_id: Optional[str] = None,
        user: Optional[str] = None,
        risk_score: Optional[float] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (from EventType enum)
            action: Action performed
            details: Additional event details
            url: URL involved (if applicable)
            render_id: Render operation ID (if applicable)
            user: User performing action (if applicable)
            risk_score: Risk score (if applicable)
        """
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            url=url,
            render_id=render_id,
            user=user,
            action=action,
            details=details,
            risk_score=risk_score
        )
        
        # Log to file
        if self.json_format:
            self.logger.info(event.to_json())
        else:
            self.logger.info(
                f"Event: {event_type} | Action: {action} | "
                f"URL: {url} | Details: {details}"
            )
        
        # Add to cache
        self._add_to_cache(event)

    def _add_to_cache(self, event: AuditEvent) -> None:
        """Add event to in-memory cache."""
        self._event_cache.append(event)
        
        # Trim cache if too large
        if len(self._event_cache) > self._cache_max_size:
            self._event_cache = self._event_cache[-self._cache_max_size:]

    def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit logs from cache.

        Args:
            limit: Maximum number of logs to return
            offset: Offset for pagination
            event_type: Filter by event type

        Returns:
            List of audit events as dictionaries
        """
        # Filter by event type if specified
        events = self._event_cache
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (newest first)
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        # Apply pagination
        events = events[offset:offset + limit]
        
        # Convert to dicts
        return [e.to_dict() for e in events]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from audit logs.

        Returns:
            Dictionary with statistics
        """
        total_events = len(self._event_cache)
        
        # Count by event type
        event_counts = {}
        for event in self._event_cache:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Calculate risk statistics
        risk_scores = [e.risk_score for e in self._event_cache if e.risk_score is not None]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        high_risk_count = len([r for r in risk_scores if r >= 7.0])
        
        return {
            "total_events": total_events,
            "event_counts": event_counts,
            "average_risk_score": round(avg_risk, 2),
            "high_risk_events": high_risk_count,
            "cache_size": len(self._event_cache),
            "oldest_event": self._event_cache[0].timestamp.isoformat() if self._event_cache else None,
            "newest_event": self._event_cache[-1].timestamp.isoformat() if self._event_cache else None
        }

    def export_logs(
        self,
        output_file: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Export audit logs to file.

        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Number of events exported
        """
        # Filter events by date
        events = self._event_cache
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, 'w') as f:
                json.dump([e.to_dict() for e in events], f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='') as f:
                if events:
                    writer = csv.DictWriter(f, fieldnames=events[0].to_dict().keys())
                    writer.writeheader()
                    for event in events:
                        writer.writerow(event.to_dict())
        
        self.logger.info(f"Exported {len(events)} events to {output_file}")
        return len(events)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

