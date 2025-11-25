"""
Chromium Runner - Headless Browser Instance Manager

Manages the lifecycle of headless Chromium browsers for isolation operations.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from playwright.async_api import Browser, Playwright, async_playwright

logger = logging.getLogger(__name__)


class ChromiumRunner:
    """
    Manages headless Chromium browser instances.

    Provides a clean interface for starting, stopping, and managing
    browser instances used for isolation operations.
    """

    def __init__(
        self, headless: bool = True, proxy: Optional[str] = None, extra_args: Optional[list] = None
    ):
        """
        Initialize Chromium runner.

        Args:
            headless: Run in headless mode
            proxy: Optional proxy server URL
            extra_args: Additional Chromium launch arguments
        """
        self.headless = headless
        self.proxy = proxy
        self.extra_args = extra_args or []

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._is_running = False

    async def start(self) -> None:
        """Start the Chromium browser instance."""
        if self._is_running:
            logger.warning("Chromium runner already started")
            return

        logger.info("Starting Chromium runner...")

        try:
            self._playwright = await async_playwright().start()

            # Build launch arguments
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-default-browser-check",
                "--safebrowsing-disable-auto-update",
            ]

            # Add custom args
            launch_args.extend(self.extra_args)

            # Launch browser
            launch_options: Dict[str, Any] = {"headless": self.headless, "args": launch_args}

            if self.proxy:
                launch_options["proxy"] = {"server": self.proxy}

            self._browser = await self._playwright.chromium.launch(**launch_options)
            self._is_running = True

            logger.info("Chromium runner started successfully")

        except Exception as e:
            logger.error(f"Failed to start Chromium runner: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the Chromium browser instance."""
        if not self._is_running:
            return

        logger.info("Stopping Chromium runner...")

        try:
            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._is_running = False
            logger.info("Chromium runner stopped")

        except Exception as e:
            logger.error(f"Error stopping Chromium runner: {e}")

    @property
    def browser(self) -> Optional[Browser]:
        """Get the browser instance."""
        return self._browser

    @property
    def is_running(self) -> bool:
        """Check if runner is active."""
        return self._is_running

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


@asynccontextmanager
async def managed_chromium(**kwargs):
    """
    Context manager for temporary Chromium instance.

    Usage:
        async with managed_chromium() as runner:
            browser = runner.browser
            # Use browser...
    """
    runner = ChromiumRunner(**kwargs)
    try:
        await runner.start()
        yield runner
    finally:
        await runner.stop()
