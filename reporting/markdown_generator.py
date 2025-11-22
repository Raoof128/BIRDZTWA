"""
Markdown Report Generator

Generates human-readable Markdown reports of isolation operations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class MarkdownReportGenerator:
    """Generates detailed Markdown reports for isolation operations."""

    def __init__(self):
        """Initialize report generator."""
        pass

    def generate_isolation_report(
        self,
        url: str,
        render_id: str,
        metadata: Dict[str, Any],
        warnings: List[str],
        blocked_content: List[Dict[str, str]],
        risk_score: float,
        timestamp: datetime,
    ) -> str:
        """
        Generate a comprehensive isolation report.

        Args:
            url: Isolated URL
            render_id: Render operation ID
            metadata: Render metadata
            warnings: List of warnings
            blocked_content: List of blocked content items
            risk_score: Risk score
            timestamp: Report timestamp

        Returns:
            Markdown formatted report
        """
        # Determine risk level
        if risk_score >= 7.0:
            risk_level = "🔴 HIGH"
            risk_emoji = "🚨"
        elif risk_score >= 5.0:
            risk_level = "🟠 MEDIUM"
            risk_emoji = "⚠️"
        elif risk_score >= 3.0:
            risk_level = "🟡 LOW"
            risk_emoji = "⚡"
        else:
            risk_level = "🟢 MINIMAL"
            risk_emoji = "✅"

        report = f"""# Browser Isolation Report

**Generated:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Render ID:** `{render_id}`  
**URL:** {url}  
**Risk Level:** {risk_level} ({risk_score}/10) {risk_emoji}

---

## Executive Summary

This URL was isolated and sanitized in a remote headless browser environment. All JavaScript and potentially malicious content was removed before rendering.

### Quick Stats

| Metric | Value |
|--------|-------|
| Original Size | {metadata.get('original_size', 0):,} bytes |
| Sanitized Size | {metadata.get('sanitized_size', 0):,} bytes |
| Size Reduction | {metadata.get('reduction_percent', 0):.1f}% |
| Fetch Time | {metadata.get('fetch_time', 0):.2f}s |
| Risk Score | {risk_score}/10 |
| Status | {metadata.get('status', 'unknown').upper()} |

---

## Security Actions Taken

"""

        # Add removed elements section
        removed = metadata.get("removed_elements", {})
        if any(removed.values()):
            report += "### Removed Threats\n\n"

            if removed.get("scripts", 0) > 0:
                report += f"- ✅ **Removed {removed['scripts']} JavaScript scripts** - All executable code stripped\n"

            if removed.get("event_handlers", 0) > 0:
                report += f"- ✅ **Removed {removed['event_handlers']} event handlers** - Interactive threats neutralized\n"

            if removed.get("iframes", 0) > 0:
                report += (
                    f"- ✅ **Blocked {removed['iframes']} iframes** - Embedded content blocked\n"
                )

            if removed.get("trackers", 0) > 0:
                report += f"- ✅ **Removed {removed['trackers']} trackers** - Privacy protected\n"

            report += "\n"
        else:
            report += "✅ **No threats detected** - Page was clean\n\n"

        # Add blocked content details
        if blocked_content:
            report += "### Blocked Content Details\n\n"
            report += "| Type | Count | Description | Risk |\n"
            report += "|------|-------|-------------|------|\n"

            for item in blocked_content:
                risk_indicator = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(
                    item.get("risk", "low"), "⚪"
                )

                report += f"| {item.get('type', 'unknown')} | {item.get('count', 0)} | {item.get('description', 'N/A')} | {risk_indicator} |\n"

            report += "\n"

        # Add warnings section
        if warnings:
            report += "## ⚠️ Warnings\n\n"
            for warning in warnings:
                report += f"- {warning}\n"
            report += "\n"

        # Add recommendations
        report += """---

## Recommendations

"""

        if risk_score >= 7.0:
            report += """### 🚨 HIGH RISK - Immediate Action Required

This page contained significant threats:
- **Do not** trust any information from this site
- **Report** this URL to security team
- **Block** this domain in your firewall
- **Investigate** the source of this link
- **Consider** this page as potentially malicious

"""
        elif risk_score >= 5.0:
            report += """### ⚠️ MEDIUM RISK - Exercise Caution

This page had concerning elements:
- Verify the legitimacy of this site before trusting content
- Do not download files or enter sensitive information
- Monitor for suspicious behavior
- Consider blocking if not essential

"""
        elif risk_score >= 3.0:
            report += """### ⚡ LOW RISK - Normal Precautions

This page appears relatively safe but had some minor issues:
- Standard web browsing cautions apply
- Isolation successfully neutralized potential threats
- Safe to view read-only content

"""
        else:
            report += """### ✅ MINIMAL RISK - Safe

This page appears clean:
- No significant threats detected
- Standard security practices applied
- Safe to view in isolated mode

"""

        # Add technical details
        report += """---

## Technical Details

### Isolation Process

1. **Policy Check** - URL validated against blocklists and policies
2. **Remote Fetch** - Page loaded in isolated headless Chromium
3. **DOM Extraction** - HTML structure captured without execution
4. **Sanitization** - All JavaScript, event handlers, and trackers removed
5. **Safe Rendering** - Clean HTML transmitted to viewer
6. **Audit Logging** - All actions recorded for compliance

### What Was Blocked

The isolation system removed the following threat vectors:
- All `<script>` tags (inline and external)
- JavaScript event handlers (onclick, onload, etc.)
- `javascript:` and `data:` URLs
- Cross-site iframes
- Tracking pixels and beacons
- Known malicious domains
- Dangerous CSS (expression, javascript URLs)
- HTML comments (may contain IE conditional scripts)

### What Remains Safe

The sanitized page contains only:
- Static HTML structure
- Images (from validated sources)
- CSS styling (sanitized)
- Text content
- Safe links (validated protocols)

---

## Compliance & Forensics

**Render ID:** `{render_id}`  
**Timestamp:** {timestamp.isoformat()}  
**User Agent:** BrowserIsolation/1.0  
**Isolation Engine:** Playwright + Chromium  
**Sanitization:** BeautifulSoup + Bleach  

This report can be used for:
- Security incident documentation
- Compliance audits (SOC 2, ISO 27001)
- Threat intelligence
- User awareness training
- Forensic analysis

---

## About Browser Isolation

Browser Isolation (Remote Browser Isolation / RBI) is a Zero Trust security technology that:

- **Prevents malware infections** - Code never executes on user devices
- **Blocks phishing attacks** - Dangerous scripts disabled
- **Protects privacy** - Trackers removed
- **Enables safe research** - Security teams can analyze threats safely
- **Ensures compliance** - Complete audit trail

**Technology:** Headless Chromium + DOM Sanitization + Policy Enforcement

---

**Generated by Browser Isolation System v1.0**  
**Report Format:** Markdown  
**Classification:** Security Report - Internal Use
"""

        return report

    def save_report(self, report: str, output_path: str) -> None:
        """
        Save report to file.

        Args:
            report: Report content
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(report)

    def generate_summary_report(
        self, renders: List[Dict[str, Any]], start_date: datetime, end_date: datetime
    ) -> str:
        """
        Generate a summary report for multiple isolation operations.

        Args:
            renders: List of render operations
            start_date: Start date
            end_date: End date

        Returns:
            Markdown formatted summary report
        """
        total_renders = len(renders)

        if total_renders == 0:
            return "# No isolation operations in the specified period\n"

        # Calculate statistics
        total_scripts = sum(r.get("removed_scripts", 0) for r in renders)
        total_threats = sum(
            r.get("removed_scripts", 0)
            + r.get("removed_iframes", 0)
            + len(r.get("blocked_urls", []))
            for r in renders
        )
        avg_risk = sum(r.get("risk_score", 0) for r in renders) / total_renders
        high_risk_count = len([r for r in renders if r.get("risk_score", 0) >= 7.0])

        report = f"""# Browser Isolation Summary Report

**Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Total Isolations:** {total_renders}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Overview

| Metric | Value |
|--------|-------|
| Total Pages Isolated | {total_renders} |
| Total Scripts Removed | {total_scripts:,} |
| Total Threats Blocked | {total_threats:,} |
| Average Risk Score | {avg_risk:.1f}/10 |
| High Risk Pages | {high_risk_count} ({high_risk_count/total_renders*100:.1f}%) |

---

## Top Threats Blocked

"""

        # Add top dangerous pages
        sorted_renders = sorted(renders, key=lambda r: r.get("risk_score", 0), reverse=True)

        report += "### Most Dangerous Pages\n\n"
        report += "| Risk | URL | Scripts | Threats |\n"
        report += "|------|-----|---------|----------|\n"

        for render in sorted_renders[:10]:
            risk = render.get("risk_score", 0)
            url = render.get("url", "unknown")[:50]
            scripts = render.get("removed_scripts", 0)
            threats = scripts + render.get("removed_iframes", 0)

            risk_emoji = "🔴" if risk >= 7 else "🟠" if risk >= 5 else "🟡"

            report += f"| {risk_emoji} {risk:.1f} | {url} | {scripts} | {threats} |\n"

        report += f"\n\n---\n\n**Report End**\n"

        return report
