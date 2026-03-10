import pytest
import httpx
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invalid_email_format_422(http_client: AsyncClient, users_base_url: str):
    """Test that invalid email format returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": "invalid-email",
            "password": "validpassword123",
            "role": "USER"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_short_password_422(http_client: AsyncClient, users_base_url: str):
    """Test that short password returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
            "role": "USER"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_negative_price_422(http_client: AsyncClient, catalog_base_url: str, seller_token: str):
    """Test that negative price returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": -10.99,
            "stock": 10
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_zero_stock_422(http_client: AsyncClient, catalog_base_url: str, seller_token: str):
    """Test that zero stock returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 10.99,
            "stock": 0
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_negative_stock_422(http_client: AsyncClient, catalog_base_url: str, seller_token: str):
    """Test that negative stock returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 10.99,
            "stock": -5
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_promo_code_format_422(http_client: AsyncClient, catalog_base_url: str, seller_token: str):
    """Test that invalid promo code format returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{catalog_base_url}/promotions",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": "invalid code with spaces!",
            "discount_percent": 20
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_uuid_format_400(http_client: AsyncClient, catalog_base_url: str, user_token: str):
    """Test that invalid UUID format returns 400 Bad Request."""
    response = await http_client.get(
        f"{catalog_base_url}/products/invalid-uuid-format",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_missing_required_fields_422(http_client: AsyncClient, users_base_url: str):
    """Test that missing required fields returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": "user@example.com"
            # Missing password and role
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_missing_all_required_fields_422(http_client: AsyncClient, users_base_url: str):
    """Test that missing all required fields returns 422 Unprocessable Entity."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
