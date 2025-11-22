"""
Tests for DOM Sanitizer

Tests the DOM sanitization engine that removes JavaScript and malicious content.
"""

import pytest
from engine.dom_sanitizer import DOMSanitizer


class TestDOMSanitizer:
    """Test suite for DOMSanitizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = DOMSanitizer()

    def test_remove_script_tags(self):
        """Test removal of script tags."""
        html = """
        <html>
            <head><script>alert('xss')</script></head>
            <body>
                <p>Content</p>
                <script src="evil.js"></script>
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert '<script>' not in result.safe_html.lower()
        assert 'alert' not in result.safe_html
        assert result.removed_scripts == 2

    def test_remove_event_handlers(self):
        """Test removal of JavaScript event handlers."""
        html = """
        <html>
            <body>
                <button onclick="malicious()">Click</button>
                <img src="test.jpg" onerror="steal()">
                <div onload="track()">Content</div>
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert 'onclick' not in result.safe_html.lower()
        assert 'onerror' not in result.safe_html.lower()
        assert 'onload' not in result.safe_html.lower()
        assert result.removed_event_handlers >= 3

    def test_remove_javascript_urls(self):
        """Test removal of javascript: URLs."""
        html = """
        <html>
            <body>
                <a href="javascript:alert('xss')">Click</a>
                <img src="javascript:evil()">
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert 'javascript:' not in result.safe_html.lower()
        assert len(result.blocked_urls) >= 2

    def test_remove_iframes(self):
        """Test removal of iframe tags."""
        html = """
        <html>
            <body>
                <iframe src="http://phishing.com"></iframe>
                <iframe src="http://malware.net"></iframe>
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert '<iframe' not in result.safe_html.lower()
        assert result.removed_iframes == 2

    def test_preserve_safe_content(self):
        """Test that safe content is preserved."""
        html = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph text</p>
                <img src="image.jpg" alt="Image">
                <a href="https://safe-site.com">Link</a>
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert '<h1>' in result.safe_html.lower()
        assert '<p>' in result.safe_html.lower()
        assert '<img' in result.safe_html.lower()
        assert '<a' in result.safe_html.lower()
        assert 'safe-site.com' in result.safe_html.lower()

    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        # Low risk
        safe_html = "<html><body><p>Safe content</p></body></html>"
        result = self.sanitizer.sanitize(safe_html)
        assert result.risk_score < 3.0
        
        # High risk
        dangerous_html = """
        <html>
            <body>
                <script>eval(atob('...'))</script>
                <script>document.write('<iframe src="malware">')</script>
                <iframe src="phishing"></iframe>
                <img onclick="steal()" onerror="track()">
            </body>
        </html>
        """
        result = self.sanitizer.sanitize(dangerous_html)
        assert result.risk_score >= 5.0

    def test_tracker_removal(self):
        """Test removal of tracking pixels."""
        html = """
        <html>
            <body>
                <img src="https://google-analytics.com/pixel.gif">
                <script src="https://googletagmanager.com/gtm.js"></script>
                <img src="https://facebook.com/tr/?id=123">
            </body>
        </html>
        """
        
        sanitizer = DOMSanitizer(remove_trackers=True)
        result = sanitizer.sanitize(html)
        
        assert result.removed_trackers > 0
        assert 'google-analytics' not in result.safe_html.lower()

    def test_sanitize_css(self):
        """Test CSS sanitization."""
        html = """
        <html>
            <head>
                <style>
                    body { background: url('javascript:alert(1)'); }
                    div { expression(alert('xss')); }
                </style>
            </head>
            <body style="background: url('javascript:evil()')">
                Content
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert 'javascript:' not in result.safe_html.lower()
        assert 'expression(' not in result.safe_html.lower()

    def test_size_reduction(self):
        """Test that sanitization reduces page size."""
        html = """
        <html>
            <head>
                <script>var x = 1; var y = 2; var z = 3;</script>
                <script>function malicious() { /* lots of code */ }</script>
            </head>
            <body>
                <p>Small content</p>
            </body>
        </html>
        """
        
        result = self.sanitizer.sanitize(html)
        
        assert result.sanitized_size < result.original_size
        assert result.sanitized_size > 0

    def test_empty_html(self):
        """Test sanitization of empty HTML."""
        html = ""
        result = self.sanitizer.sanitize(html)
        
        assert result.safe_html is not None
        assert result.removed_scripts == 0

    def test_forms_handling(self):
        """Test form handling based on policy."""
        html = """
        <html>
            <body>
                <form action="/submit" method="post">
                    <input type="text" name="username">
                    <button>Submit</button>
                </form>
            </body>
        </html>
        """
        
        # Default: keep forms
        sanitizer = DOMSanitizer(remove_forms=False)
        result = sanitizer.sanitize(html)
        assert '<form' in result.safe_html.lower()
        
        # Remove forms
        sanitizer = DOMSanitizer(remove_forms=True)
        result = sanitizer.sanitize(html)
        assert '<form' not in result.safe_html.lower()

