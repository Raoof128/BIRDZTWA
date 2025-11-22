"""
Remote Fetcher - Headless Browser URL Fetching

Loads URLs in an isolated headless Chromium browser and extracts
the DOM and resources safely without local execution.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class FetchResult:
    """Result of a remote fetch operation."""

    def __init__(
        self,
        url: str,
        html: str,
        status_code: int,
        headers: Dict[str, str],
        resources: List[Dict[str, Any]],
        console_logs: List[str],
        errors: List[str],
        fetch_time: float,
        timestamp: datetime,
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.headers = headers
        self.resources = resources
        self.console_logs = console_logs
        self.errors = errors
        self.fetch_time = fetch_time
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "html": self.html,
            "status_code": self.status_code,
            "headers": self.headers,
            "resources": self.resources,
            "console_logs": self.console_logs,
            "errors": self.errors,
            "fetch_time": self.fetch_time,
            "timestamp": self.timestamp.isoformat(),
        }


class RemoteFetcher:
    """
    Fetches web pages using headless Chromium in an isolated environment.

    This component loads URLs remotely and extracts the DOM without
    executing any code on the user's device.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None,
        block_resources: Optional[List[str]] = None,
    ):
        """
        Initialize the remote fetcher.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            user_agent: Custom user agent string
            viewport: Browser viewport dimensions
            block_resources: Resource types to block (e.g., 'script', 'image')
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 BrowserIsolation/1.0"
        )
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.block_resources = block_resources or [
            "script",
            "websocket",
            "eventsource",
            "serviceworker",
        ]

        self._browser: Optional[Browser] = None
        self._playwright = None
        self._console_logs: List[str] = []
        self._errors: List[str] = []
        self._resources: List[Dict[str, Any]] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the headless browser."""
        logger.info("Starting headless browser (Playwright + Chromium)")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        logger.info("Headless browser started successfully")

    async def close(self) -> None:
        """Close the headless browser."""
        if self._browser:
            await self._browser.close()
            logger.info("Headless browser closed")

        if self._playwright:
            await self._playwright.stop()

    async def fetch(self, url: str, wait_for_load: bool = True) -> FetchResult:
        """
        Fetch a URL in the isolated headless browser.

        Args:
            url: The URL to fetch
            wait_for_load: Wait for page to fully load

        Returns:
            FetchResult containing the page data

        Raises:
            Exception: If fetch fails
        """
        if not self._browser:
            await self.start()

        start_time = datetime.now()
        self._console_logs = []
        self._errors = []
        self._resources = []

        logger.info(f"Fetching URL in isolated browser: {url}")

        try:
            # Create new browser context (isolated session)
            context = await self._browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport,
                ignore_https_errors=True,
                java_script_enabled=True,  # We enable JS in fetcher, but sanitize before rendering
            )

            # Create new page
            page = await context.new_page()

            # Set up event listeners
            page.on("console", lambda msg: self._console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: self._errors.append(str(err)))
            page.on("request", self._handle_request)
            page.on("response", self._handle_response)

            # Block dangerous resource types
            await page.route("**/*", self._route_handler)

            # Navigate to URL
            response = await page.goto(
                url,
                wait_until="networkidle" if wait_for_load else "domcontentloaded",
                timeout=self.timeout,
            )

            # Wait a bit for dynamic content
            if wait_for_load:
                await page.wait_for_timeout(2000)

            # Extract HTML
            html = await page.content()

            # Get response details
            status_code = response.status if response else 0
            headers = dict(response.headers) if response else {}

            # Calculate fetch time
            fetch_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Successfully fetched {url} "
                f"(status: {status_code}, time: {fetch_time:.2f}s, "
                f"size: {len(html)} bytes)"
            )

            # Clean up
            await context.close()

            return FetchResult(
                url=url,
                html=html,
                status_code=status_code,
                headers=headers,
                resources=self._resources.copy(),
                console_logs=self._console_logs.copy(),
                errors=self._errors.copy(),
                fetch_time=fetch_time,
                timestamp=start_time,
            )

        except PlaywrightTimeout:
            logger.error(f"Timeout fetching {url} after {self.timeout}ms")
            raise TimeoutError(f"Page load timeout for {url}")

        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}", exc_info=True)
            raise

    async def _route_handler(self, route, request):
        """
        Handle resource routing to block dangerous content.

        This blocks scripts, WebSockets, and other dangerous resources
        at the network level during fetch (defense in depth).
        """
        resource_type = request.resource_type

        # Block dangerous resource types
        if resource_type in self.block_resources:
            logger.debug(f"Blocking {resource_type}: {request.url}")
            await route.abort()
            return

        # Allow other resources
        await route.continue_()

    def _handle_request(self, request) -> None:
        """Track outgoing requests."""
        self._resources.append(
            {
                "type": "request",
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _handle_response(self, response) -> None:
        """Track incoming responses."""
        self._resources.append(
            {
                "type": "response",
                "url": response.url,
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def fetch_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[FetchResult]:
        """
        Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent fetches

        Returns:
            List of FetchResults
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str) -> FetchResult:
            async with semaphore:
                return await self.fetch(url)

        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        fetch_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
            else:
                fetch_results.append(result)

        return fetch_results


# Convenience function for single fetch
async def fetch_url(url: str, **kwargs) -> FetchResult:
    """
    Convenience function to fetch a single URL.

    Args:
        url: URL to fetch
        **kwargs: Additional arguments for RemoteFetcher

    Returns:
        FetchResult
    """
    async with RemoteFetcher(**kwargs) as fetcher:
        return await fetcher.fetch(url)
