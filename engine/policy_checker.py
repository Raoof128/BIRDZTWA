"""
Policy Checker - URL and Content Policy Enforcement

Enforces access policies, URL filtering, and content rules
before and during isolation operations.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path
import yaml
import tldextract

logger = logging.getLogger(__name__)


class PolicyDecision:
    """Result of a policy check."""
    
    def __init__(
        self,
        allowed: bool,
        reason: str,
        risk_level: str,
        matched_rules: List[str]
    ):
        self.allowed = allowed
        self.reason = reason
        self.risk_level = risk_level  # 'low', 'medium', 'high', 'critical'
        self.matched_rules = matched_rules

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "matched_rules": self.matched_rules
        }


class PolicyChecker:
    """
    Enforces URL filtering and content policies.
    
    Checks URLs against allow/deny lists and applies content
    filtering rules based on organizational policies.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize policy checker.

        Args:
            config_path: Path to policy configuration file (YAML)
        """
        self.config_path = config_path
        self.blocked_domains: List[str] = []
        self.allowed_domains: List[str] = []
        self.blocked_categories: List[str] = []
        self.blocked_patterns: List[re.Pattern] = []
        self.allowed_patterns: List[re.Pattern] = []
        self.malware_domains: List[str] = []
        self.phishing_domains: List[str] = []
        
        # Load configuration
        if config_path:
            self._load_config(config_path)
        else:
            self._load_default_config()

    def _load_config(self, config_path: str) -> None:
        """Load policy configuration from YAML file."""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"Config file not found: {config_path}, using defaults")
                self._load_default_config()
                return

            with open(path, 'r') as f:
                config = yaml.safe_load(f)

            self.blocked_domains = config.get('blocked_domains', [])
            self.allowed_domains = config.get('allowed_domains', [])
            self.blocked_categories = config.get('block_categories', [])
            
            # Compile regex patterns
            for pattern in config.get('blocked_patterns', []):
                self.blocked_patterns.append(re.compile(pattern, re.IGNORECASE))
            
            for pattern in config.get('allowed_patterns', []):
                self.allowed_patterns.append(re.compile(pattern, re.IGNORECASE))

            # Load threat intelligence
            self.malware_domains = config.get('malware_domains', [])
            self.phishing_domains = config.get('phishing_domains', [])

            logger.info(
                f"Loaded policy config: {len(self.blocked_domains)} blocked domains, "
                f"{len(self.allowed_domains)} allowed domains, "
                f"{len(self.blocked_categories)} blocked categories"
            )

        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default policy configuration."""
        self.blocked_domains = [
            "malware-site.com",
            "phishing-example.net",
            "crypto-miner.io",
            "suspicious-ads.com"
        ]
        
        self.allowed_domains = [
            "google.com",
            "github.com",
            "stackoverflow.com"
        ]
        
        self.blocked_categories = [
            "ads",
            "trackers",
            "cryptominers",
            "malware",
            "phishing"
        ]

        self.malware_domains = [
            "known-malware.com",
            "virus-distributor.net",
            "trojan-host.io"
        ]

        self.phishing_domains = [
            "paypa1.com",  # Typosquatting
            "g00gle.com",
            "micr0soft.com"
        ]

        logger.info("Loaded default policy configuration")

    def check_url(self, url: str) -> PolicyDecision:
        """
        Check if a URL is allowed by policy.

        Args:
            url: URL to check

        Returns:
            PolicyDecision with allow/deny decision
        """
        logger.debug(f"Checking URL policy: {url}")

        matched_rules = []

        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return PolicyDecision(
                    allowed=False,
                    reason="Invalid URL format",
                    risk_level="medium",
                    matched_rules=["invalid_format"]
                )

            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Protocol '{parsed.scheme}' not allowed (only HTTP/HTTPS)",
                    risk_level="medium",
                    matched_rules=["protocol_violation"]
                )

            # Extract domain components
            extracted = tldextract.extract(url)
            domain = extracted.domain
            suffix = extracted.suffix
            full_domain = f"{domain}.{suffix}" if suffix else domain

            # Check malware domains (highest priority)
            if self._is_malware_domain(full_domain):
                matched_rules.append("malware_domain")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Domain '{full_domain}' is known malware distributor",
                    risk_level="critical",
                    matched_rules=matched_rules
                )

            # Check phishing domains
            if self._is_phishing_domain(full_domain):
                matched_rules.append("phishing_domain")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Domain '{full_domain}' is known phishing site",
                    risk_level="critical",
                    matched_rules=matched_rules
                )

            # Check explicit block list
            if self._is_blocked_domain(full_domain):
                matched_rules.append("blocked_domain")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Domain '{full_domain}' is blocked by policy",
                    risk_level="high",
                    matched_rules=matched_rules
                )

            # Check blocked patterns
            for pattern in self.blocked_patterns:
                if pattern.search(url):
                    matched_rules.append(f"blocked_pattern:{pattern.pattern}")
                    return PolicyDecision(
                        allowed=False,
                        reason=f"URL matches blocked pattern",
                        risk_level="high",
                        matched_rules=matched_rules
                    )

            # Check allow list (if domain is explicitly allowed, skip other checks)
            if self._is_allowed_domain(full_domain):
                matched_rules.append("allowed_domain")
                return PolicyDecision(
                    allowed=True,
                    reason=f"Domain '{full_domain}' is explicitly allowed",
                    risk_level="low",
                    matched_rules=matched_rules
                )

            # Check allowed patterns
            for pattern in self.allowed_patterns:
                if pattern.search(url):
                    matched_rules.append(f"allowed_pattern:{pattern.pattern}")
                    return PolicyDecision(
                        allowed=True,
                        reason="URL matches allowed pattern",
                        risk_level="low",
                        matched_rules=matched_rules
                    )

            # Check for suspicious URL patterns
            risk_indicators = self._check_suspicious_patterns(url)
            if risk_indicators:
                return PolicyDecision(
                    allowed=True,  # Allow but warn
                    reason="URL has suspicious characteristics but not blocked",
                    risk_level="medium",
                    matched_rules=risk_indicators
                )

            # Default: Allow (Zero Trust isolation handles the rest)
            return PolicyDecision(
                allowed=True,
                reason="No blocking rules matched, isolation will sanitize content",
                risk_level="low",
                matched_rules=["default_allow"]
            )

        except Exception as e:
            logger.error(f"Error checking URL policy: {e}")
            return PolicyDecision(
                allowed=False,
                reason=f"Policy check error: {str(e)}",
                risk_level="high",
                matched_rules=["error"]
            )

    def _is_blocked_domain(self, domain: str) -> bool:
        """Check if domain is in block list."""
        domain_lower = domain.lower()
        for blocked in self.blocked_domains:
            if blocked.lower() in domain_lower or domain_lower == blocked.lower():
                return True
        return False

    def _is_allowed_domain(self, domain: str) -> bool:
        """Check if domain is in allow list."""
        domain_lower = domain.lower()
        for allowed in self.allowed_domains:
            if allowed.lower() in domain_lower or domain_lower == allowed.lower():
                return True
        return False

    def _is_malware_domain(self, domain: str) -> bool:
        """Check if domain is known malware distributor."""
        domain_lower = domain.lower()
        for malware in self.malware_domains:
            if malware.lower() in domain_lower or domain_lower == malware.lower():
                return True
        return False

    def _is_phishing_domain(self, domain: str) -> bool:
        """Check if domain is known phishing site."""
        domain_lower = domain.lower()
        for phishing in self.phishing_domains:
            if phishing.lower() in domain_lower or domain_lower == phishing.lower():
                return True
        return False

    def _check_suspicious_patterns(self, url: str) -> List[str]:
        """Check for suspicious URL patterns."""
        indicators = []

        # Check for IP address instead of domain
        if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            indicators.append("ip_address_url")

        # Check for excessive subdomain depth
        parsed = urlparse(url)
        if parsed.netloc.count('.') > 3:
            indicators.append("excessive_subdomains")

        # Check for suspicious TLDs
        suspicious_tlds = ['.xyz', '.top', '.tk', '.ml', '.ga', '.cf', '.gq']
        if any(url.lower().endswith(tld) for tld in suspicious_tlds):
            indicators.append("suspicious_tld")

        # Check for very long domains (possible DGA)
        if len(parsed.netloc) > 50:
            indicators.append("long_domain")

        # Check for excessive random characters
        if re.search(r'[a-z0-9]{30,}', parsed.netloc):
            indicators.append("random_chars")

        # Check for homograph attacks (mixing character sets)
        if re.search(r'[а-яА-Я]', url):  # Cyrillic characters
            indicators.append("homograph_attack")

        return indicators

    def check_content_policy(self, content_type: str, size: int) -> PolicyDecision:
        """
        Check if content type and size are allowed.

        Args:
            content_type: MIME type of content
            size: Content size in bytes

        Returns:
            PolicyDecision
        """
        max_size = 50 * 1024 * 1024  # 50MB

        # Check size
        if size > max_size:
            return PolicyDecision(
                allowed=False,
                reason=f"Content size ({size} bytes) exceeds limit ({max_size} bytes)",
                risk_level="medium",
                matched_rules=["size_exceeded"]
            )

        # Check content type
        allowed_types = [
            'text/html',
            'text/plain',
            'application/xhtml+xml',
            'text/xml',
            'application/xml'
        ]

        if not any(content_type.startswith(t) for t in allowed_types):
            return PolicyDecision(
                allowed=False,
                reason=f"Content type '{content_type}' not supported for isolation",
                risk_level="low",
                matched_rules=["unsupported_content_type"]
            )

        return PolicyDecision(
            allowed=True,
            reason="Content meets policy requirements",
            risk_level="low",
            matched_rules=["content_ok"]
        )

    def get_policy_summary(self) -> Dict:
        """Get summary of active policies."""
        return {
            "blocked_domains_count": len(self.blocked_domains),
            "allowed_domains_count": len(self.allowed_domains),
            "blocked_categories": self.blocked_categories,
            "blocked_patterns_count": len(self.blocked_patterns),
            "allowed_patterns_count": len(self.allowed_patterns),
            "malware_domains_count": len(self.malware_domains),
            "phishing_domains_count": len(self.phishing_domains)
        }

