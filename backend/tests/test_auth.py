"""
Authentication tests.

Tests for user registration, login, and token management.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# Test data
VALID_USER = {
    "email": "test@example.com",
    "password": "SecureP@ssw0rd123!",
}

WEAK_PASSWORDS = [
    "short1!A",           # Too short
    "nouppercase123!",    # No uppercase
    "NOLOWERCASE123!",    # No lowercase
    "NoDigitsHere!!",     # No digits
    "NoSpecialChar123",   # No special char
]


class TestRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.anyio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=VALID_USER)
        
        # Should return 201 Created
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == VALID_USER["email"]
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.anyio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with existing email fails."""
        # Register first user
        await client.post("/api/v1/auth/register", json=VALID_USER)
        
        # Try to register again with same email
        response = await client.post("/api/v1/auth/register", json=VALID_USER)
        
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": VALID_USER["password"]},
        )
        
        assert response.status_code == 422

    @pytest.mark.anyio
    @pytest.mark.parametrize("weak_password", WEAK_PASSWORDS)
    async def test_register_weak_password(self, client: AsyncClient, weak_password: str):
        """Test registration with weak passwords fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": weak_password},
        )
        
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_email_normalized(self, client: AsyncClient):
        """Test that email is normalized to lowercase."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "TEST@EXAMPLE.COM", "password": VALID_USER["password"]},
        )
        
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"


class TestLogin:
    """Tests for user login endpoint."""

    @pytest.mark.anyio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login returns tokens."""
        # Register user first
        await client.post("/api/v1/auth/register", json=VALID_USER)
        
        # Login
        response = await client.post("/api/v1/auth/login", json=VALID_USER)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.anyio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v1/auth/register", json=VALID_USER)
        
        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": "WrongP@ssw0rd123!"},
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "SomeP@ssw0rd123!"},
        )
        
        assert response.status_code == 401
        # Same error message as wrong password (prevents enumeration)
        assert response.json()["detail"] == "Invalid email or password"


class TestProtectedRoutes:
    """Tests for protected route access."""

    @pytest.mark.anyio
    async def test_me_authenticated(self, client: AsyncClient):
        """Test /me endpoint with valid token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=VALID_USER)
        login_response = await client.post("/api/v1/auth/login", json=VALID_USER)
        access_token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == VALID_USER["email"]

    @pytest.mark.anyio
    async def test_me_no_token(self, client: AsyncClient):
        """Test /me endpoint without token fails."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_me_invalid_token(self, client: AsyncClient):
        """Test /me endpoint with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.anyio
    async def test_refresh_success(self, client: AsyncClient):
        """Test successful token refresh."""
        # Register and login
        await client.post("/api/v1/auth/register", json=VALID_USER)
        login_response = await client.post("/api/v1/auth/login", json=VALID_USER)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        """Test that access token cannot be used for refresh."""
        # Register and login
        await client.post("/api/v1/auth/register", json=VALID_USER)
        login_response = await client.post("/api/v1/auth/login", json=VALID_USER)
        access_token = login_response.json()["access_token"]
        
        # Try to use access token for refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        assert response.status_code == 401


class TestPasswordChange:
    """Tests for password change endpoint."""

    @pytest.mark.anyio
    async def test_change_password_success(self, client: AsyncClient):
        """Test successful password change."""
        # Register and login
        await client.post("/api/v1/auth/register", json=VALID_USER)
        login_response = await client.post("/api/v1/auth/login", json=VALID_USER)
        access_token = login_response.json()["access_token"]
        
        # Change password
        new_password = "NewSecureP@ss123!"
        response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": VALID_USER["password"],
                "new_password": new_password,
            },
        )
        
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": new_password},
        )
        assert login_response.status_code == 200

    @pytest.mark.anyio
    async def test_change_password_wrong_current(self, client: AsyncClient):
        """Test password change with wrong current password fails."""
        # Register and login
        await client.post("/api/v1/auth/register", json=VALID_USER)
        login_response = await client.post("/api/v1/auth/login", json=VALID_USER)
        access_token = login_response.json()["access_token"]
        
        # Try to change with wrong current password
        response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "WrongP@ssw0rd123!",
                "new_password": "NewSecureP@ss123!",
            },
        )
        
        assert response.status_code == 400
