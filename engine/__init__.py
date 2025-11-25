"""
Browser Isolation Engine - Core Components

This package contains the core isolation engine components for remote
DOM rendering and sanitization.
"""

from .dom_sanitizer import DOMSanitizer
from .fetcher import RemoteFetcher
from .policy_checker import PolicyChecker
from .remote_renderer import RemoteRenderer

__all__ = [
    "RemoteFetcher",
    "DOMSanitizer",
    "RemoteRenderer",
    "PolicyChecker",
]

__version__ = "1.0.0"
