"""
Logging Module - Audit and Event Logging

Structured logging for isolation operations and security events.
"""

from .events import AuditLogger, EventType

__all__ = ["AuditLogger", "EventType"]

