"""
Tests for API

Tests the FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


class TestAPI:
    """Test suite for API endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert "service" in response.json()
        assert response.json()["service"] == "Browser Isolation API"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_check_url_allowed(self):
        """Test URL policy check for allowed URL."""
        response = client.post("/api/v1/check-url", json={"url": "https://github.com"})

        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
        assert "reason" in data
        assert "risk_level" in data

    def test_check_url_invalid(self):
        """Test URL policy check with invalid URL."""
        response = client.post("/api/v1/check-url", json={"url": "not-a-url"})

        assert response.status_code in [200, 422]

    def test_policies_endpoint(self):
        """Test policies summary endpoint."""
        response = client.get("/api/v1/policies")

        assert response.status_code == 200
        data = response.json()
        assert "blocked_domains_count" in data
        assert "allowed_domains_count" in data

    def test_audit_endpoint(self):
        """Test audit logs endpoint."""
        response = client.get("/api/v1/audit?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "entries" in data

    def test_render_validation(self):
        """Test render endpoint validation."""
        # Missing URL
        response = client.post("/api/v1/render", json={})

        assert response.status_code == 422

    def test_render_invalid_url(self):
        """Test render with invalid URL format."""
        response = client.post("/api/v1/render", json={"url": "not-a-url"})

        assert response.status_code == 422
