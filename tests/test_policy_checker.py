"""
Tests for Policy Checker

Tests URL and content policy enforcement.
"""

import pytest
from engine.policy_checker import PolicyChecker


class TestPolicyChecker:
    """Test suite for PolicyChecker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.policy_checker = PolicyChecker()

    def test_allow_safe_url(self):
        """Test that safe URLs are allowed."""
        decision = self.policy_checker.check_url("https://github.com")
        
        assert decision.allowed is True
        assert decision.risk_level in ['low', 'medium']

    def test_block_malware_domain(self):
        """Test blocking of known malware domains."""
        decision = self.policy_checker.check_url("https://known-malware.com/page")
        
        assert decision.allowed is False
        assert decision.risk_level == 'critical'
        assert 'malware' in decision.reason.lower()

    def test_block_phishing_domain(self):
        """Test blocking of phishing domains."""
        decision = self.policy_checker.check_url("https://paypa1.com/login")
        
        assert decision.allowed is False
        assert decision.risk_level == 'critical'
        assert 'phishing' in decision.reason.lower()

    def test_block_invalid_protocol(self):
        """Test blocking of non-HTTP/HTTPS protocols."""
        decision = self.policy_checker.check_url("ftp://example.com")
        
        assert decision.allowed is False
        assert 'protocol' in decision.reason.lower()

    def test_detect_ip_address(self):
        """Test detection of IP address URLs."""
        decision = self.policy_checker.check_url("http://192.168.1.1/page")
        
        # Should be allowed but flagged as suspicious
        if decision.allowed:
            assert 'ip_address_url' in decision.matched_rules

    def test_detect_suspicious_tld(self):
        """Test detection of suspicious TLDs."""
        decision = self.policy_checker.check_url("https://suspicious.xyz/page")
        
        # May be allowed but should be flagged
        if decision.allowed:
            assert any(
                'suspicious_tld' in rule or 'tld' in decision.reason.lower()
                for rule in decision.matched_rules
            ) or decision.risk_level in ['medium', 'high']

    def test_content_size_limit(self):
        """Test content size policy enforcement."""
        decision = self.policy_checker.check_content_policy(
            content_type='text/html',
            size=100 * 1024 * 1024  # 100 MB
        )
        
        assert decision.allowed is False
        assert 'size' in decision.reason.lower()

    def test_allowed_content_type(self):
        """Test allowed content type."""
        decision = self.policy_checker.check_content_policy(
            content_type='text/html',
            size=1024  # 1 KB
        )
        
        assert decision.allowed is True

    def test_blocked_content_type(self):
        """Test blocked content type."""
        decision = self.policy_checker.check_content_policy(
            content_type='application/pdf',
            size=1024
        )
        
        assert decision.allowed is False
        assert 'content type' in decision.reason.lower()

    def test_explicit_blocklist(self):
        """Test explicit domain blocking."""
        decision = self.policy_checker.check_url("https://malware-site.com")
        
        assert decision.allowed is False
        assert 'blocked' in decision.reason.lower()

    def test_explicit_allowlist(self):
        """Test explicit domain allowing."""
        decision = self.policy_checker.check_url("https://google.com/search")
        
        assert decision.allowed is True
        assert 'allowed' in decision.reason.lower()

    def test_policy_summary(self):
        """Test policy summary retrieval."""
        summary = self.policy_checker.get_policy_summary()
        
        assert 'blocked_domains_count' in summary
        assert 'allowed_domains_count' in summary
        assert 'blocked_categories' in summary
        assert isinstance(summary['blocked_domains_count'], int)
        assert isinstance(summary['blocked_categories'], list)

