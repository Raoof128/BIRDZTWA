"""
Safe Viewer Dashboard - Streamlit UI

Interactive dashboard for viewing isolated web content safely.
"""

import asyncio
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from engine import DOMSanitizer, PolicyChecker, RemoteFetcher, RemoteRenderer
from logging_mod.events import AuditLogger
from reporting.markdown_generator import MarkdownReportGenerator

# Configure page
st.set_page_config(
    page_title="Browser Isolation - Safe Viewer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize components
@st.cache_resource
def init_components():
    """Initialize isolation components."""
    policy_checker = PolicyChecker()
    audit_logger = AuditLogger()
    report_generator = MarkdownReportGenerator()
    return policy_checker, audit_logger, report_generator


policy_checker, audit_logger, report_generator = init_components()

# Session state initialization
if "history" not in st.session_state:
    st.session_state.history = []
if "current_render" not in st.session_state:
    st.session_state.current_render = None


def render_header():
    """Render dashboard header."""
    st.title("🛡️ Browser Isolation - Safe Viewer")
    st.markdown(
        """
    **Zero-Trust Web Access** - View any website safely without malware risk.
    All JavaScript removed • Tracking blocked • Complete isolation
    """
    )
    st.divider()


def render_sidebar():
    """Render sidebar with controls and stats."""
    with st.sidebar:
        st.header("🎛️ Controls")

        # URL input
        url = st.text_input(
            "Enter URL to isolate:",
            placeholder="https://example.com",
            help="Enter any HTTP/HTTPS URL",
        )

        # Options
        with st.expander("⚙️ Options"):
            timeout = st.slider("Timeout (seconds)", 5, 120, 30)
            wait_for_load = st.checkbox("Wait for full page load", value=True)
            block_trackers = st.checkbox("Block trackers", value=True)

        # Render button
        if st.button("🚀 Isolate & Render", type="primary", use_container_width=True):
            if url:
                with st.spinner("🔒 Isolating..."):
                    perform_isolation(url, timeout, wait_for_load, block_trackers)
            else:
                st.error("Please enter a URL")

        st.divider()

        # Statistics
        st.header("📊 Statistics")
        stats = audit_logger.get_statistics()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Renders", stats.get("total_events", 0))
        with col2:
            st.metric("Avg Risk", f"{stats.get('average_risk_score', 0):.1f}/10")

        st.metric("High Risk Pages", stats.get("high_risk_events", 0))

        # Recent history
        st.divider()
        st.header("📜 Recent History")
        if st.session_state.history:
            for i, item in enumerate(reversed(st.session_state.history[-5:])):
                with st.expander(f"🌐 {item['url'][:30]}..."):
                    st.write(f"**Risk:** {item['risk_score']:.1f}/10")
                    st.write(f"**Time:** {item['timestamp']}")
                    if st.button("View", key=f"history_{i}"):
                        st.session_state.current_render = item
        else:
            st.info("No history yet")


def perform_isolation(url: str, timeout: int, wait_for_load: bool, block_trackers: bool):
    """Perform isolation operation."""
    try:
        # Check policy
        policy_decision = policy_checker.check_url(url)

        if not policy_decision.allowed:
            st.error(f"❌ **URL Blocked by Policy**\n\n{policy_decision.reason}")
            st.warning(f"Risk Level: {policy_decision.risk_level.upper()}")
            return

        # Fetch URL
        async def fetch():
            fetcher = RemoteFetcher(timeout=timeout * 1000)
            async with fetcher:
                return await fetcher.fetch(url, wait_for_load=wait_for_load)

        fetch_result = asyncio.run(fetch())

        # Sanitize
        sanitizer = DOMSanitizer(remove_trackers=block_trackers)
        sanitization_result = sanitizer.sanitize(fetch_result.html)

        # Render
        renderer = RemoteRenderer()
        safe_dom = renderer.render(
            url=url,
            sanitized_html=sanitization_result.safe_html,
            sanitization_result=sanitization_result,
            fetch_result=fetch_result,
        )

        # Store in session
        render_data = {
            "url": url,
            "html": safe_dom.html,
            "metadata": safe_dom.metadata.to_dict(),
            "warnings": safe_dom.warnings,
            "blocked_content": safe_dom.blocked_content,
            "risk_score": safe_dom.metadata.risk_score,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        st.session_state.current_render = render_data
        st.session_state.history.append(render_data)

        # Log
        audit_logger.log_event(
            event_type="render_success",
            url=url,
            render_id=safe_dom.metadata.render_id,
            action="render",
            details={
                "risk_score": safe_dom.metadata.risk_score,
                "removed_scripts": sanitization_result.removed_scripts,
            },
            risk_score=safe_dom.metadata.risk_score,
        )

        st.success(f"✅ Successfully isolated: {url}")
        st.rerun()

    except Exception as e:
        st.error(f"❌ **Isolation Failed**\n\n{str(e)}")


def render_main_content():
    """Render main content area."""
    if st.session_state.current_render is None:
        # Welcome screen
        st.info("👋 **Welcome to Browser Isolation**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
            ### 🛡️ Zero Trust
            All pages load in isolated browser.
            No code executes on your device.
            """
            )

        with col2:
            st.markdown(
                """
            ### 🧹 Sanitized
            JavaScript removed completely.
            Tracking blocked automatically.
            """
            )

        with col3:
            st.markdown(
                """
            ### 📊 Monitored
            Complete audit trail.
            Risk scoring included.
            """
            )

        st.markdown("---")
        st.markdown("### 🚀 Quick Start")
        st.markdown(
            """
        1. Enter a URL in the sidebar
        2. Click **Isolate & Render**
        3. View safe content below

        **Try these examples:**
        - `https://example.com`
        - `https://www.wikipedia.org`
        - `https://news.ycombinator.com`
        """
        )

        return

    # Display isolated content
    render = st.session_state.current_render

    # Header with risk score
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        st.subheader(f"🌐 {render['url']}")

    with col2:
        risk = render["risk_score"]
        if risk >= 7:
            st.error(f"🔴 Risk: {risk}/10")
        elif risk >= 5:
            st.warning(f"🟠 Risk: {risk}/10")
        else:
            st.success(f"🟢 Risk: {risk}/10")

    with col3:
        st.info(f"📅 {render['timestamp']}")

    with col4:
        if st.button("📄 Generate Report"):
            generate_report(render)

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📄 Safe Content", "🚫 Blocked Items", "⚠️ Warnings", "📊 Analysis"]
    )

    with tab1:
        render_safe_content(render)

    with tab2:
        render_blocked_content(render)

    with tab3:
        render_warnings(render)

    with tab4:
        render_analysis(render)


def render_safe_content(render: dict):
    """Render the safe HTML content."""
    st.markdown("### Safe DOM View (Read-Only)")
    st.info("ℹ️ This content has been sanitized. All JavaScript and malicious elements removed.")

    # NOTE: Per user memory, don't display full notebook contents
    # We'll show a preview instead
    html_preview = render["html"][:1000] + "..." if len(render["html"]) > 1000 else render["html"]

    with st.expander("View Sanitized HTML (Preview)", expanded=False):
        st.code(html_preview, language="html")

    st.markdown("---")
    st.markdown("**Render in Safe Frame:**")

    # Show in iframe (safe because it's already sanitized)
    st.components.v1.html(
        f"""
        <div style="border: 2px solid #4CAF50; padding: 20px; background: white;">
            <div style="background: #4CAF50; color: white; padding: 10px; margin: -20px -20px 20px -20px;">
                🔒 ISOLATED CONTENT - READ ONLY MODE
            </div>
            {render['html'][:5000]}
            {"<p>... (content truncated for display) ...</p>" if len(render['html']) > 5000 else ""}
        </div>
        """,
        height=600,
        scrolling=True,
    )


def render_blocked_content(render: dict):
    """Render blocked content information."""
    st.markdown("### Blocked Threats & Elements")

    blocked = render.get("blocked_content", [])

    if not blocked:
        st.success("✅ No threats detected - page was clean!")
        return

    for item in blocked:
        risk = item.get("risk", "low")

        if risk == "high":
            st.error(
                f"🔴 **{item.get('type', 'unknown').upper()}** - Count: {item.get('count', 0)}"
            )
        elif risk == "medium":
            st.warning(
                f"🟠 **{item.get('type', 'unknown').upper()}** - Count: {item.get('count', 0)}"
            )
        else:
            st.info(f"🟡 **{item.get('type', 'unknown').upper()}** - Count: {item.get('count', 0)}")

        st.markdown(f"_{item.get('description', 'N/A')}_")
        st.markdown("---")


def render_warnings(render: dict):
    """Render warnings."""
    st.markdown("### Security Warnings")

    warnings = render.get("warnings", [])

    if not warnings:
        st.success("✅ No warnings - content appears safe!")
        return

    for warning in warnings:
        st.warning(f"⚠️ {warning}")


def render_analysis(render: dict):
    """Render analysis and statistics."""
    st.markdown("### Technical Analysis")

    metadata = render.get("metadata", {})

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Original Size", f"{metadata.get('original_size', 0):,} bytes")

    with col2:
        st.metric("Sanitized Size", f"{metadata.get('sanitized_size', 0):,} bytes")

    with col3:
        st.metric("Reduction", f"{metadata.get('reduction_percent', 0):.1f}%")

    with col4:
        st.metric("Fetch Time", f"{metadata.get('fetch_time', 0):.2f}s")

    st.divider()

    # Removed elements chart
    removed = metadata.get("removed_elements", {})

    if any(removed.values()):
        st.markdown("### Removed Elements")

        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(removed.keys()),
                    y=list(removed.values()),
                    marker_color=["#ff6b6b", "#feca57", "#ff9ff3", "#54a0ff"],
                )
            ]
        )

        fig.update_layout(
            title="Threat Elements Removed",
            xaxis_title="Element Type",
            yaxis_title="Count",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)


def generate_report(render: dict):
    """Generate and download report."""
    report = report_generator.generate_isolation_report(
        url=render["url"],
        render_id=render["metadata"].get("render_id", "unknown"),
        metadata=render["metadata"],
        warnings=render["warnings"],
        blocked_content=render["blocked_content"],
        risk_score=render["risk_score"],
        timestamp=datetime.now(),
    )

    st.download_button(
        label="📥 Download Report (Markdown)",
        data=report,
        file_name=f"isolation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )

    st.success("✅ Report generated!")


def main():
    """Main dashboard function."""
    render_header()
    render_sidebar()
    render_main_content()

    # Footer
    st.divider()
    st.markdown(
        """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        Browser Isolation System v1.0 | Zero Trust Architecture |
        <a href='/docs'>API Docs</a> |
        Built with Playwright + FastAPI + Streamlit
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
