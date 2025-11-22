"""
Tests for Remote Fetcher

Tests the headless browser fetching component.
"""

import pytest
import asyncio
from engine.fetcher import RemoteFetcher


@pytest.mark.asyncio
class TestRemoteFetcher:
    """Test suite for RemoteFetcher."""

    async def test_fetch_simple_url(self):
        """Test fetching a simple URL."""
        async with RemoteFetcher() as fetcher:
            result = await fetcher.fetch("https://example.com")

            assert result is not None
            assert result.html is not None
            assert len(result.html) > 0
            assert result.status_code == 200
            assert result.url == "https://example.com"

    async def test_fetch_with_timeout(self):
        """Test fetch with timeout."""
        async with RemoteFetcher(timeout=5000) as fetcher:
            result = await fetcher.fetch("https://example.com")

            assert result.fetch_time < 5.0

    async def test_invalid_url(self):
        """Test handling of invalid URL."""
        async with RemoteFetcher() as fetcher:
            with pytest.raises(Exception):
                await fetcher.fetch("not-a-valid-url")

    async def test_resource_blocking(self):
        """Test that dangerous resources are blocked."""
        # Block scripts during fetch
        async with RemoteFetcher(block_resources=["script"]) as fetcher:
            result = await fetcher.fetch("https://example.com")

            # Should still get HTML
            assert result.html is not None

    async def test_fetch_result_metadata(self):
        """Test that fetch result contains metadata."""
        async with RemoteFetcher() as fetcher:
            result = await fetcher.fetch("https://example.com")

            assert hasattr(result, "url")
            assert hasattr(result, "html")
            assert hasattr(result, "status_code")
            assert hasattr(result, "headers")
            assert hasattr(result, "resources")
            assert hasattr(result, "fetch_time")
            assert hasattr(result, "timestamp")
