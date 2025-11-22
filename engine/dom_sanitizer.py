"""
DOM Sanitizer - JavaScript Removal and Content Cleaning

Removes all JavaScript, dangerous HTML, tracking beacons, and malicious
content from fetched DOM to create a safe, inert representation.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment, NavigableString
import bleach

logger = logging.getLogger(__name__)


class SanitizationResult:
    """Result of DOM sanitization operation."""

    def __init__(
        self,
        safe_html: str,
        original_size: int,
        sanitized_size: int,
        removed_scripts: int,
        removed_event_handlers: int,
        removed_iframes: int,
        removed_trackers: int,
        blocked_urls: List[str],
        suspicious_content: List[str],
        risk_score: float,
    ):
        self.safe_html = safe_html
        self.original_size = original_size
        self.sanitized_size = sanitized_size
        self.removed_scripts = removed_scripts
        self.removed_event_handlers = removed_event_handlers
        self.removed_iframes = removed_iframes
        self.removed_trackers = removed_trackers
        self.blocked_urls = blocked_urls
        self.suspicious_content = suspicious_content
        self.risk_score = risk_score

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "safe_html": self.safe_html,
            "original_size": self.original_size,
            "sanitized_size": self.sanitized_size,
            "reduction_percent": round(
                (1 - self.sanitized_size / max(self.original_size, 1)) * 100, 2
            ),
            "removed_scripts": self.removed_scripts,
            "removed_event_handlers": self.removed_event_handlers,
            "removed_iframes": self.removed_iframes,
            "removed_trackers": self.removed_trackers,
            "blocked_urls": self.blocked_urls,
            "suspicious_content": self.suspicious_content,
            "risk_score": self.risk_score,
        }


class DOMSanitizer:
    """
    Sanitizes HTML DOM by removing all JavaScript and dangerous content.

    This is the core security component that transforms potentially
    malicious HTML into safe, inert content for display.
    """

    # Dangerous JavaScript event handlers
    EVENT_HANDLERS = [
        "onclick",
        "ondblclick",
        "onmousedown",
        "onmouseup",
        "onmouseover",
        "onmousemove",
        "onmouseout",
        "onmouseenter",
        "onmouseleave",
        "onload",
        "onunload",
        "onchange",
        "onsubmit",
        "onreset",
        "onselect",
        "onblur",
        "onfocus",
        "onkeydown",
        "onkeypress",
        "onkeyup",
        "onerror",
        "onabort",
        "ondrag",
        "ondrop",
        "onscroll",
        "onresize",
        "ontouchstart",
        "ontouchmove",
        "ontouchend",
        "onpointerdown",
        "onpointerup",
        "onpointermove",
        "onbeforeunload",
        "onhashchange",
        "onpopstate",
        "onanimationstart",
        "onanimationend",
        "ontransitionend",
    ]

    # Known tracking and ad domains
    TRACKER_DOMAINS = [
        "doubleclick.net",
        "google-analytics.com",
        "googletagmanager.com",
        "facebook.com/tr",
        "connect.facebook.net",
        "analytics.js",
        "scorecardresearch.com",
        "quantserve.com",
        "chartbeat.com",
        "hotjar.com",
        "crazyegg.com",
        "mouseflow.com",
        "clicktale.com",
        "newrelic.com",
        "nr-data.net",
        "sentry.io",
        "bugsnag.com",
        "advertising.com",
        "adnxs.com",
        "adsystem.com",
        "advertising.com",
    ]

    # Suspicious patterns in content
    SUSPICIOUS_PATTERNS = [
        r"eval\s*\(",
        r"Function\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
        r"document\.write",
        r"innerHTML\s*=",
        r"outerHTML\s*=",
        r"createElement\s*\(",
        r"fetch\s*\(",
        r"XMLHttpRequest",
        r"WebSocket",
        r"crypto\.subtle",
        r"navigator\.sendBeacon",
        r"atob\s*\(",
        r"btoa\s*\(",
        r"fromCharCode",
        r"unescape\s*\(",
    ]

    def __init__(
        self,
        remove_scripts: bool = True,
        remove_iframes: bool = True,
        remove_forms: bool = False,
        remove_trackers: bool = True,
        sanitize_css: bool = True,
        allow_images: bool = True,
        allow_links: bool = True,
        policies: Optional[Dict] = None,
    ):
        """
        Initialize DOM sanitizer.

        Args:
            remove_scripts: Remove all <script> tags
            remove_iframes: Remove all <iframe> tags
            remove_forms: Remove all <form> tags
            remove_trackers: Remove known tracking pixels/scripts
            sanitize_css: Clean CSS for javascript: URLs
            allow_images: Keep <img> tags
            allow_links: Keep <a> tags
            policies: Custom sanitization policies
        """
        self.remove_scripts = remove_scripts
        self.remove_iframes = remove_iframes
        self.remove_forms = remove_forms
        self.remove_trackers = remove_trackers
        self.sanitize_css = sanitize_css
        self.allow_images = allow_images
        self.allow_links = allow_links
        self.policies = policies or {}

        # Statistics tracking
        self._stats = {
            "removed_scripts": 0,
            "removed_event_handlers": 0,
            "removed_iframes": 0,
            "removed_trackers": 0,
            "blocked_urls": [],
            "suspicious_content": [],
        }

    def sanitize(self, html: str, base_url: Optional[str] = None) -> SanitizationResult:
        """
        Sanitize HTML content by removing all dangerous elements.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            SanitizationResult with safe HTML and statistics
        """
        logger.info("Starting DOM sanitization")

        original_size = len(html)
        self._reset_stats()

        # Parse HTML
        soup = BeautifulSoup(html, "lxml")

        # Step 1: Remove <script> tags
        if self.remove_scripts:
            self._remove_scripts(soup)

        # Step 2: Remove <iframe> tags
        if self.remove_iframes:
            self._remove_iframes(soup)

        # Step 3: Remove <form> tags (optional)
        if self.remove_forms:
            self._remove_forms(soup)

        # Step 4: Remove event handlers from all tags
        self._remove_event_handlers(soup)

        # Step 5: Sanitize URLs (remove javascript: and data: URLs)
        self._sanitize_urls(soup)

        # Step 6: Remove tracking pixels and beacons
        if self.remove_trackers:
            self._remove_trackers(soup)

        # Step 7: Sanitize CSS
        if self.sanitize_css:
            self._sanitize_css(soup)

        # Step 8: Remove comments (may contain IE conditional scripts)
        self._remove_comments(soup)

        # Step 9: Remove dangerous attributes
        self._remove_dangerous_attributes(soup)

        # Step 10: Detect suspicious content
        self._detect_suspicious_content(soup)

        # Final bleach sanitization for extra safety
        safe_html = self._final_bleach_pass(str(soup))

        sanitized_size = len(safe_html)
        risk_score = self._calculate_risk_score()

        logger.info(
            f"Sanitization complete - Removed: {self._stats['removed_scripts']} scripts, "
            f"{self._stats['removed_event_handlers']} event handlers, "
            f"{self._stats['removed_iframes']} iframes, "
            f"{self._stats['removed_trackers']} trackers | "
            f"Size: {original_size} -> {sanitized_size} bytes "
            f"({round((1 - sanitized_size/max(original_size, 1))*100, 1)}% reduction) | "
            f"Risk: {risk_score}/10"
        )

        return SanitizationResult(
            safe_html=safe_html,
            original_size=original_size,
            sanitized_size=sanitized_size,
            removed_scripts=self._stats["removed_scripts"],
            removed_event_handlers=self._stats["removed_event_handlers"],
            removed_iframes=self._stats["removed_iframes"],
            removed_trackers=self._stats["removed_trackers"],
            blocked_urls=self._stats["blocked_urls"],
            suspicious_content=self._stats["suspicious_content"],
            risk_score=risk_score,
        )

    def _reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {
            "removed_scripts": 0,
            "removed_event_handlers": 0,
            "removed_iframes": 0,
            "removed_trackers": 0,
            "blocked_urls": [],
            "suspicious_content": [],
        }

    def _remove_scripts(self, soup: BeautifulSoup) -> None:
        """Remove all <script> tags."""
        scripts = soup.find_all("script")
        for script in scripts:
            # Check for suspicious content before removing
            if script.string:
                self._check_script_content(script.string)
            script.decompose()

        self._stats["removed_scripts"] = len(scripts)
        logger.debug(f"Removed {len(scripts)} <script> tags")

    def _remove_iframes(self, soup: BeautifulSoup) -> None:
        """Remove all <iframe> tags."""
        iframes = soup.find_all("iframe")
        for iframe in iframes:
            src = iframe.get("src", "")
            if src:
                self._stats["blocked_urls"].append(f"iframe: {src}")
            iframe.decompose()

        self._stats["removed_iframes"] = len(iframes)
        logger.debug(f"Removed {len(iframes)} <iframe> tags")

    def _remove_forms(self, soup: BeautifulSoup) -> None:
        """Remove all <form> tags."""
        forms = soup.find_all("form")
        for form in forms:
            form.decompose()

        logger.debug(f"Removed {len(forms)} <form> tags")

    def _remove_event_handlers(self, soup: BeautifulSoup) -> None:
        """Remove all JavaScript event handlers from tags."""
        count = 0

        for tag in soup.find_all(True):  # Find all tags
            for event_handler in self.EVENT_HANDLERS:
                if tag.has_attr(event_handler):
                    del tag[event_handler]
                    count += 1

        self._stats["removed_event_handlers"] = count
        logger.debug(f"Removed {count} event handler attributes")

    def _sanitize_urls(self, soup: BeautifulSoup) -> None:
        """Remove javascript: and data: URLs from href and src attributes."""
        dangerous_protocols = ["javascript:", "data:", "vbscript:"]

        for tag in soup.find_all(True):
            for attr in ["href", "src", "action", "formaction", "xlink:href"]:
                if tag.has_attr(attr):
                    url = tag[attr].strip().lower()

                    # Check for dangerous protocols
                    for protocol in dangerous_protocols:
                        if url.startswith(protocol):
                            logger.debug(f"Blocked dangerous URL: {tag[attr]}")
                            self._stats["blocked_urls"].append(tag[attr])
                            del tag[attr]
                            break

    def _remove_trackers(self, soup: BeautifulSoup) -> None:
        """Remove known tracking pixels and scripts."""
        count = 0

        # Remove tracking images
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if self._is_tracker_url(src):
                logger.debug(f"Removed tracker: {src}")
                img.decompose()
                count += 1

        # Remove tracking scripts
        for link in soup.find_all("link"):
            href = link.get("href", "")
            if self._is_tracker_url(href):
                logger.debug(f"Removed tracker link: {href}")
                link.decompose()
                count += 1

        self._stats["removed_trackers"] = count

    def _is_tracker_url(self, url: str) -> bool:
        """Check if URL is from a known tracking domain."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            for tracker in self.TRACKER_DOMAINS:
                if tracker in domain:
                    return True

            # Check for common tracking patterns
            if any(
                pattern in url.lower()
                for pattern in [
                    "analytics",
                    "tracking",
                    "beacon",
                    "pixel",
                    "ads",
                    "doubleclick",
                    "facebook.com/tr",
                ]
            ):
                return True

            return False
        except Exception:
            return False

    def _sanitize_css(self, soup: BeautifulSoup) -> None:
        """Remove dangerous CSS (javascript: URLs, expression())."""
        # Remove inline styles with javascript:
        for tag in soup.find_all(style=True):
            style = tag["style"]
            if "javascript:" in style.lower() or "expression(" in style.lower():
                del tag["style"]
                logger.debug(f"Removed dangerous inline style")

        # Sanitize <style> tags
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                css = style_tag.string
                if "javascript:" in css.lower() or "expression(" in css.lower():
                    style_tag.decompose()
                    logger.debug("Removed dangerous <style> tag")

    def _remove_comments(self, soup: BeautifulSoup) -> None:
        """Remove HTML comments (can contain conditional IE scripts)."""
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

    def _remove_dangerous_attributes(self, soup: BeautifulSoup) -> None:
        """Remove attributes that could be dangerous."""
        dangerous_attrs = [
            "formaction",
            "form",
            "import",
            "integrity",
            "is",
            "ping",
            "srcdoc",
            "xml",
        ]

        for tag in soup.find_all(True):
            for attr in dangerous_attrs:
                if tag.has_attr(attr):
                    del tag[attr]

    def _check_script_content(self, content: str) -> None:
        """Check script content for suspicious patterns."""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._stats["suspicious_content"].append(f"Pattern: {pattern}")

    def _detect_suspicious_content(self, soup: BeautifulSoup) -> None:
        """Detect suspicious patterns in remaining content."""
        text_content = soup.get_text()

        for pattern in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                self._stats["suspicious_content"].append(
                    f"Found {len(matches)} instances of: {pattern}"
                )

    def _final_bleach_pass(self, html: str) -> str:
        """
        Final sanitization pass using bleach library.

        This is a defense-in-depth measure to catch anything
        that might have been missed.
        """
        allowed_tags = [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "br",
            "code",
            "div",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "pre",
            "span",
            "strong",
            "ul",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "thead",
            "tbody",
            "tr",
            "td",
            "th",
            "img",
            "hr",
            "dl",
            "dt",
            "dd",
        ]

        if self.allow_images:
            allowed_tags.append("img")

        allowed_attributes = {
            "a": ["href", "title", "rel"],
            "img": ["src", "alt", "title", "width", "height"],
            "div": ["class", "id"],
            "span": ["class", "id"],
            "p": ["class"],
            "*": ["class"],
        }

        allowed_protocols = ["http", "https", "mailto"]

        return bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=allowed_protocols,
            strip=True,
        )

    def _calculate_risk_score(self) -> float:
        """
        Calculate risk score based on sanitization actions.

        Returns:
            Risk score from 0.0 (safe) to 10.0 (very dangerous)
        """
        score = 0.0

        # Scripts are high risk
        score += min(self._stats["removed_scripts"] * 0.5, 3.0)

        # Event handlers are medium risk
        score += min(self._stats["removed_event_handlers"] * 0.1, 2.0)

        # Iframes are medium-high risk
        score += min(self._stats["removed_iframes"] * 0.3, 2.0)

        # Suspicious content is high risk
        score += min(len(self._stats["suspicious_content"]) * 0.4, 2.0)

        # Blocked URLs
        score += min(len(self._stats["blocked_urls"]) * 0.2, 1.0)

        return min(round(score, 1), 10.0)
