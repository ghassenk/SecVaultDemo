"""
Secrets API tests.

Tests for CRUD operations and encryption functionality.
"""

import pytest
from httpx import AsyncClient


# Test data
TEST_USER = {
    "email": "secrets_test@example.com",
    "password": "SecureP@ssw0rd123!",
}

TEST_USER_2 = {
    "email": "other_user@example.com",
    "password": "SecureP@ssw0rd123!",
}

TEST_SECRET = {
    "name": "AWS API Key",
    "description": "Production AWS credentials",
    "content": "AKIAIOSFODNN7EXAMPLE",
}


async def get_auth_token(client: AsyncClient, user: dict) -> str:
    """Helper to register and login a user, returning the access token."""
    await client.post("/api/v1/auth/register", json=user)
    response = await client.post("/api/v1/auth/login", json=user)
    return response.json()["access_token"]


class TestCreateSecret:
    """Tests for secret creation endpoint."""
    @pytest.mark.no_ratelimit
    async def test_create_secret_success(self, client: AsyncClient):
        """Test successful secret creation."""
        token = await get_auth_token(client, TEST_USER)
        
        response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == TEST_SECRET["name"]
        assert data["description"] == TEST_SECRET["description"]
        assert "id" in data
        assert "content" not in data
        assert "encrypted_content" not in data

    async def test_create_secret_unauthenticated(self, client: AsyncClient):
        """Test secret creation without authentication fails."""
        response = await client.post("/api/v1/secrets", json=TEST_SECRET)
        
        assert response.status_code == 401

    @pytest.mark.no_ratelimit
    async def test_create_secret_invalid_data(self, client: AsyncClient):
        """Test secret creation with invalid data fails."""
        token = await get_auth_token(client, TEST_USER)
        
        response = await client.post(
            "/api/v1/secrets",
            json={"description": "No name or content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 422


class TestGetSecret:
    """Tests for secret retrieval endpoint."""

    @pytest.mark.no_ratelimit
    async def test_get_secret_success(self, client: AsyncClient):
        """Test successful secret retrieval with decrypted content."""
        token = await get_auth_token(client, TEST_USER)
        
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token}"},
        )
        secret_id = create_response.json()["id"]
        
        response = await client.get(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_SECRET["name"]
        assert data["content"] == TEST_SECRET["content"]

    @pytest.mark.no_ratelimit
    async def test_get_secret_not_found(self, client: AsyncClient):
        """Test getting non-existent secret returns 404."""
        token = await get_auth_token(client, TEST_USER)
        
        response = await client.get(
            "/api/v1/secrets/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 404

    @pytest.mark.no_ratelimit
    async def test_get_secret_wrong_user(self, client: AsyncClient):
        """Test that users cannot access other users' secrets."""
        token1 = await get_auth_token(client, TEST_USER)
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token1}"},
        )
        secret_id = create_response.json()["id"]
        
        token2 = await get_auth_token(client, TEST_USER_2)
        response = await client.get(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        assert response.status_code == 404


class TestListSecrets:
    """Tests for secret listing endpoint."""

    @pytest.mark.no_ratelimit
    async def test_list_secrets_success(self, client: AsyncClient):
        """Test listing secrets with pagination."""
        token = await get_auth_token(client, TEST_USER)
        
        for i in range(3):
            await client.post(
                "/api/v1/secrets",
                json={"name": f"Secret {i}", "content": f"Content {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        response = await client.get(
            "/api/v1/secrets",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3

    @pytest.mark.no_ratelimit
    async def test_list_secrets_pagination(self, client: AsyncClient):
        """Test pagination parameters work correctly."""
        token = await get_auth_token(client, TEST_USER)
        
        response = await client.get(
            "/api/v1/secrets?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.no_ratelimit
    async def test_list_secrets_isolation(self, client: AsyncClient):
        """Test that users only see their own secrets."""
        token1 = await get_auth_token(client, TEST_USER)
        await client.post(
            "/api/v1/secrets",
            json={"name": "User1 Secret", "content": "secret1"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        
        token2 = await get_auth_token(client, TEST_USER_2)
        response = await client.get(
            "/api/v1/secrets",
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        data = response.json()
        for item in data["items"]:
            assert item["name"] != "User1 Secret"


class TestUpdateSecret:
    """Tests for secret update endpoint."""

    @pytest.mark.no_ratelimit
    async def test_update_secret_success(self, client: AsyncClient):
        """Test successful secret update."""
        token = await get_auth_token(client, TEST_USER)
        
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token}"},
        )
        secret_id = create_response.json()["id"]
        
        response = await client.put(
            f"/api/v1/secrets/{secret_id}",
            json={"name": "Updated Name", "content": "new-secret-content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.no_ratelimit
    async def test_update_secret_partial(self, client: AsyncClient):
        """Test partial update (only name, not content)."""
        token = await get_auth_token(client, TEST_USER)
        
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token}"},
        )
        secret_id = create_response.json()["id"]
        
        await client.put(
            f"/api/v1/secrets/{secret_id}",
            json={"name": "Only Name Changed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        get_response = await client.get(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.json()["content"] == TEST_SECRET["content"]

    @pytest.mark.no_ratelimit
    async def test_update_secret_wrong_user(self, client: AsyncClient):
        """Test that users cannot update other users' secrets."""
        token1 = await get_auth_token(client, TEST_USER)
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token1}"},
        )
        secret_id = create_response.json()["id"]
        
        token2 = await get_auth_token(client, TEST_USER_2)
        response = await client.put(
            f"/api/v1/secrets/{secret_id}",
            json={"name": "Hacked!"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        assert response.status_code == 404


class TestDeleteSecret:
    """Tests for secret deletion endpoint."""

    @pytest.mark.no_ratelimit
    async def test_delete_secret_success(self, client: AsyncClient):
        """Test successful secret deletion."""
        token = await get_auth_token(client, TEST_USER)
        
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token}"},
        )
        secret_id = create_response.json()["id"]
        
        response = await client.delete(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        
        get_response = await client.get(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    @pytest.mark.no_ratelimit
    async def test_delete_secret_wrong_user(self, client: AsyncClient):
        """Test that users cannot delete other users' secrets."""
        token1 = await get_auth_token(client, TEST_USER)
        create_response = await client.post(
            "/api/v1/secrets",
            json=TEST_SECRET,
            headers={"Authorization": f"Bearer {token1}"},
        )
        secret_id = create_response.json()["id"]
        
        token2 = await get_auth_token(client, TEST_USER_2)
        response = await client.delete(
            f"/api/v1/secrets/{secret_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        assert response.status_code == 404


class TestEncryption:
    """Tests specifically for encryption functionality."""

    @pytest.mark.no_ratelimit
    async def test_encryption_per_user(self, client: AsyncClient):
        """Test that encryption is user-specific."""
        token1 = await get_auth_token(client, TEST_USER)
        token2 = await get_auth_token(client, TEST_USER_2)
        
        same_content = {"name": "Same", "content": "identical-content"}
        
        resp1 = await client.post(
            "/api/v1/secrets",
            json=same_content,
            headers={"Authorization": f"Bearer {token1}"},
        )
        
        resp2 = await client.post(
            "/api/v1/secrets",
            json=same_content,
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        secret1 = await client.get(
            f"/api/v1/secrets/{resp1.json()['id']}",
            headers={"Authorization": f"Bearer {token1}"},
        )
        secret2 = await client.get(
            f"/api/v1/secrets/{resp2.json()['id']}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        
        assert secret1.json()["content"] == "identical-content"
        assert secret2.json()["content"] == "identical-content"
        