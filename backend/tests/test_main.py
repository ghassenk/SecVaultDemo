"""
Basic tests for SecureVault backend.

These tests verify the application starts correctly
and health endpoints respond as expected.
"""

from httpx import AsyncClient


class TestHealth:
    """Health check endpoint tests."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test the root endpoint returns app info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    async def test_health_endpoint(self, client: AsyncClient):
        """Test the health endpoint returns healthy status."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_security_headers(self, client: AsyncClient):
        """Test that security headers are present in responses."""
        response = await client.get("/")
        
        # Check critical security headers
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert "content-security-policy" in response.headers
        