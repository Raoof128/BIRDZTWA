#!/usr/bin/env python3
"""
isolationctl - Browser Isolation CLI Tool

Command-line interface for browser isolation operations.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import RemoteFetcher, DOMSanitizer, RemoteRenderer, PolicyChecker
from logging_mod.events import AuditLogger
from reporting.markdown_generator import MarkdownReportGenerator
from reporting.json_exporter import JSONExporter

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Browser Isolation CLI - Zero-Trust Web Access Tool
    
    Isolate and render web pages safely without malware risk.
    """
    pass


@cli.command()
@click.argument('url')
@click.option('--timeout', default=30, help='Timeout in seconds')
@click.option('--output', '-o', help='Save sanitized HTML to file')
@click.option('--report', '-r', help='Generate report file')
@click.option('--no-trackers', is_flag=True, help='Block trackers')
def render(url, timeout, output, report, no_trackers):
    """
    Render a URL in isolated browser and display safe content.
    
    Example: isolationctl render https://example.com
    """
    console.print(f"\n[bold blue]🛡️  Browser Isolation - Rendering URL[/bold blue]")
    console.print(f"[cyan]URL:[/cyan] {url}\n")
    
    try:
        # Check policy
        with console.status("[yellow]Checking policy..."):
            policy_checker = PolicyChecker()
            decision = policy_checker.check_url(url)
        
        if not decision.allowed:
            console.print(f"[red]❌ URL blocked by policy:[/red] {decision.reason}")
            console.print(f"[red]Risk level:[/red] {decision.risk_level}")
            sys.exit(1)
        
        console.print(f"[green]✅ Policy check passed[/green]")
        
        # Fetch
        with console.status("[yellow]Fetching URL in isolated browser..."):
            async def fetch():
                fetcher = RemoteFetcher(timeout=timeout * 1000)
                async with fetcher:
                    return await fetcher.fetch(url)
            
            fetch_result = asyncio.run(fetch())
        
        console.print(f"[green]✅ Fetched successfully[/green] ({fetch_result.fetch_time:.2f}s)")
        
        # Sanitize
        with console.status("[yellow]Sanitizing DOM..."):
            sanitizer = DOMSanitizer(remove_trackers=no_trackers)
            sanit_result = sanitizer.sanitize(fetch_result.html)
        
        console.print(f"[green]✅ Sanitization complete[/green]")
        
        # Render
        renderer = RemoteRenderer()
        safe_dom = renderer.render(
            url=url,
            sanitized_html=sanit_result.safe_html,
            sanitization_result=sanit_result,
            fetch_result=fetch_result
        )
        
        # Display results
        console.print("\n" + "="*70)
        console.print(f"[bold]Isolation Results[/bold]")
        console.print("="*70 + "\n")
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("URL", url)
        table.add_row("Render ID", safe_dom.metadata.render_id)
        table.add_row("Risk Score", f"{safe_dom.metadata.risk_score}/10")
        table.add_row("Original Size", f"{sanit_result.original_size:,} bytes")
        table.add_row("Sanitized Size", f"{sanit_result.sanitized_size:,} bytes")
        table.add_row("Reduction", f"{(1 - sanit_result.sanitized_size/sanit_result.original_size)*100:.1f}%")
        table.add_row("Removed Scripts", str(sanit_result.removed_scripts))
        table.add_row("Removed Event Handlers", str(sanit_result.removed_event_handlers))
        table.add_row("Removed iFrames", str(sanit_result.removed_iframes))
        table.add_row("Removed Trackers", str(sanit_result.removed_trackers))
        
        console.print(table)
        
        # Warnings
        if safe_dom.warnings:
            console.print("\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in safe_dom.warnings:
                console.print(f"  • {warning}")
        
        # Save output
        if output:
            Path(output).write_text(safe_dom.html)
            console.print(f"\n[green]✅ Saved sanitized HTML to:[/green] {output}")
        
        # Generate report
        if report:
            report_gen = MarkdownReportGenerator()
            report_content = report_gen.generate_isolation_report(
                url=url,
                render_id=safe_dom.metadata.render_id,
                metadata=safe_dom.metadata.to_dict(),
                warnings=safe_dom.warnings,
                blocked_content=safe_dom.blocked_content,
                risk_score=safe_dom.metadata.risk_score,
                timestamp=datetime.now()
            )
            Path(report).write_text(report_content)
            console.print(f"[green]✅ Saved report to:[/green] {report}")
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('url')
def check_url(url):
    """
    Check if a URL is allowed by policy without rendering.
    
    Example: isolationctl check-url https://example.com
    """
    console.print(f"\n[bold blue]🔍 Policy Check[/bold blue]")
    console.print(f"[cyan]URL:[/cyan] {url}\n")
    
    policy_checker = PolicyChecker()
    decision = policy_checker.check_url(url)
    
    if decision.allowed:
        console.print(Panel(
            f"[green]✅ ALLOWED[/green]\n\n"
            f"Reason: {decision.reason}\n"
            f"Risk Level: {decision.risk_level}\n"
            f"Matched Rules: {', '.join(decision.matched_rules)}",
            title="Policy Decision",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ BLOCKED[/red]\n\n"
            f"Reason: {decision.reason}\n"
            f"Risk Level: {decision.risk_level}\n"
            f"Matched Rules: {', '.join(decision.matched_rules)}",
            title="Policy Decision",
            border_style="red"
        ))
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', default='markdown', type=click.Choice(['markdown', 'json']))
@click.option('--output', '-o', help='Output file path')
@click.option('--limit', default=50, help='Number of entries')
def report(format, output, limit):
    """
    Generate audit report from logs.
    
    Example: isolationctl report --format markdown --output report.md
    """
    console.print(f"\n[bold blue]📄 Generating Report[/bold blue]\n")
    
    try:
        audit_logger = AuditLogger()
        logs = audit_logger.get_logs(limit=limit)
        
        if not logs:
            console.print("[yellow]No audit logs found[/yellow]")
            return
        
        if format == 'json':
            exporter = JSONExporter()
            content = exporter.export_multiple(logs)
        else:
            # Create markdown summary
            content = f"# Browser Isolation Audit Report\n\n"
            content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"**Entries:** {len(logs)}\n\n"
            
            for log in logs:
                content += f"## {log['event_type']} - {log['timestamp']}\n"
                if log.get('url'):
                    content += f"**URL:** {log['url']}\n"
                content += f"**Action:** {log['action']}\n"
                if log.get('risk_score'):
                    content += f"**Risk Score:** {log['risk_score']}/10\n"
                content += "\n"
        
        if output:
            Path(output).write_text(content)
            console.print(f"[green]✅ Report saved to:[/green] {output}")
        else:
            console.print(content)
    
    except Exception as e:
        console.print(f"[red]❌ Error generating report:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--host', default='0.0.0.0', help='API host')
@click.option('--port', default=8000, help='API port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def start_api(host, port, reload):
    """
    Start the FastAPI server.
    
    Example: isolationctl start-api --port 8000
    """
    console.print(f"\n[bold blue]🚀 Starting Browser Isolation API[/bold blue]")
    console.print(f"[cyan]Host:[/cyan] {host}")
    console.print(f"[cyan]Port:[/cyan] {port}\n")
    
    try:
        from api.server import start_server
        start_server(host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        console.print("\n[yellow]API server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--port', default=8501, help='Dashboard port')
def start_dashboard(port):
    """
    Start the Streamlit dashboard.
    
    Example: isolationctl start-dashboard --port 8501
    """
    console.print(f"\n[bold blue]🎨 Starting Safe Viewer Dashboard[/bold blue]")
    console.print(f"[cyan]Port:[/cyan] {port}\n")
    
    import subprocess
    
    try:
        dashboard_path = Path(__file__).parent.parent / "client" / "safe_viewer.py"
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", str(port)
        ])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
def stats():
    """
    Display audit log statistics.
    
    Example: isolationctl stats
    """
    console.print(f"\n[bold blue]📊 Browser Isolation Statistics[/bold blue]\n")
    
    try:
        audit_logger = AuditLogger()
        stats = audit_logger.get_statistics()
        
        # Create stats table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Events", str(stats['total_events']))
        table.add_row("Average Risk Score", f"{stats['average_risk_score']}/10")
        table.add_row("High Risk Events", str(stats['high_risk_events']))
        table.add_row("Cache Size", str(stats['cache_size']))
        
        console.print(table)
        
        # Event counts
        if stats.get('event_counts'):
            console.print("\n[bold]Event Types:[/bold]")
            for event_type, count in stats['event_counts'].items():
                console.print(f"  • {event_type}: {count}")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli()

