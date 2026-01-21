"""
Basic tests for SecureVault backend.

These tests verify the application starts correctly
and health endpoints respond as expected.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns application info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "SecureVault"


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint returns healthy status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.anyio
async def test_security_headers(client: AsyncClient):
    """Test that security headers are present in responses."""
    response = await client.get("/")
    
    # Check critical security headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert "content-security-policy" in response.headers
