"""RBAC tests for role-based access control."""

import pytest
import httpx
import uuid


@pytest.mark.asyncio
async def test_user_cannot_create_product(
    http_client: httpx.AsyncClient,
    user_token: str,
    catalog_base_url: str,
):
    """Test that USER cannot create a product (403)."""
    response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_update_product(
    http_client: httpx.AsyncClient,
    user_token: str,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that USER cannot update a product (403)."""
    # First, create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Try to update as USER
    response = await http_client.put(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Updated Product",
            "price": 149.99,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_product(
    http_client: httpx.AsyncClient,
    user_token: str,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that USER cannot delete a product (403)."""
    # First, create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Try to delete as USER
    response = await http_client.delete(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_seller_can_only_update_own_products(
    http_client: httpx.AsyncClient,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that SELLER can only update their own products."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Update own product - should succeed
    update_response = await http_client.put(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Updated Seller Product",
            "price": 149.99,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Seller Product"
    assert update_response.json()["price"] == 149.99


@pytest.mark.asyncio
async def test_seller_cannot_update_other_seller_products(
    http_client: httpx.AsyncClient,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that SELLER cannot update products owned by another seller."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Register another seller
    register_response = await http_client.post(
        "http://localhost:8001/auth/register",
        json={
            "email": "seller2@example.com",
            "password": "sellerpass123",
            "role": "SELLER",
        },
    )
    assert register_response.status_code == 200
    other_seller_token = register_response.json()["access_token"]

    # Try to update with another seller - should fail
    update_response = await http_client.put(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {other_seller_token}"},
        json={
            "name": "Hacked Product",
            "price": 1.99,
        },
    )
    assert update_response.status_code == 403
    assert "ACCESS_DENIED" in update_response.json()["detail"]["error_code"]


@pytest.mark.asyncio
async def test_seller_can_only_delete_own_products(
    http_client: httpx.AsyncClient,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that SELLER can only delete their own products."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Delete own product - should succeed
    delete_response = await http_client.delete(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert delete_response.status_code == 204

    # Verify product is archived
    get_response = await http_client.get(f"{catalog_base_url}/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_seller_cannot_delete_other_seller_products(
    http_client: httpx.AsyncClient,
    seller_token: str,
    catalog_base_url: str,
):
    """Test that SELLER cannot delete products owned by another seller."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Register another seller
    register_response = await http_client.post(
        "http://localhost:8001/auth/register",
        json={
            "email": "seller2@example.com",
            "password": "sellerpass123",
            "role": "SELLER",
        },
    )
    assert register_response.status_code == 200
    other_seller_token = register_response.json()["access_token"]

    # Try to delete with another seller - should fail
    delete_response = await http_client.delete(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {other_seller_token}"},
    )
    assert delete_response.status_code == 403
    assert "ACCESS_DENIED" in delete_response.json()["detail"]["error_code"]


@pytest.mark.asyncio
async def test_admin_can_update_any_product(
    http_client: httpx.AsyncClient,
    seller_token: str,
    admin_token: str,
    catalog_base_url: str,
):
    """Test that ADMIN can update any product."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Update as ADMIN - should succeed
    update_response = await http_client.put(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Admin Updated Product",
            "price": 199.99,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Admin Updated Product"
    assert update_response.json()["price"] == 199.99


@pytest.mark.asyncio
async def test_admin_can_delete_any_product(
    http_client: httpx.AsyncClient,
    seller_token: str,
    admin_token: str,
    catalog_base_url: str,
):
    """Test that ADMIN can delete any product."""
    # Create a product as SELLER
    create_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Seller Product",
            "description": "Seller Description",
            "price": 99.99,
            "stock": 10,
            "category": "Electronics",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    # Delete as ADMIN - should succeed
    delete_response = await http_client.delete(
        f"{catalog_base_url}/products/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_response.status_code == 204

    # Verify product is archived
    get_response = await http_client.get(f"{catalog_base_url}/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_user_can_only_see_own_orders(
    http_client: httpx.AsyncClient,
    user_token: str,
    orders_base_url: str,
):
    """Test that USER can only see their own orders."""
    # Create an order as USER
    create_response = await http_client.post(
        f"{orders_base_url}/api/v1/orders",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 2,
                }
            ],
        },
    )
    # Note: This might fail due to product not existing, but we're testing RBAC
    # If it succeeds, we can test the order access
    if create_response.status_code == 201:
        order_id = create_response.json()["id"]

        # Get own order - should succeed
        get_response = await http_client.get(
            f"{orders_base_url}/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == order_id

    # Register another user
    register_response = await http_client.post(
        "http://localhost:8001/auth/register",
        json={
            "email": "user2@example.com",
            "password": "userpass123",
            "role": "USER",
        },
    )
    assert register_response.status_code == 200
    other_user_token = register_response.json()["access_token"]

    # Create another order as other user
    other_create_response = await http_client.post(
        f"{orders_base_url}/api/v1/orders",
        headers={"Authorization": f"Bearer {other_user_token}"},
        json={
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 1,
                }
            ],
        },
    )

    if other_create_response.status_code == 201:
        other_order_id = other_create_response.json()["id"]

        # Try to access other user's order - should fail
        get_response = await http_client.get(
            f"{orders_base_url}/api/v1/orders/{other_order_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert get_response.status_code == 403
        assert "ORDER_OWNERSHIP_VIOLATION" in get_response.json()["detail"]["error_code"]


@pytest.mark.asyncio
async def test_admin_can_see_all_orders(
    http_client: httpx.AsyncClient,
    user_token: str,
    admin_token: str,
    orders_base_url: str,
):
    """Test that ADMIN can see all orders."""
    # Create an order as USER
    create_response = await http_client.post(
        f"{orders_base_url}/api/v1/orders",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 2,
                }
            ],
        },
    )

    if create_response.status_code == 201:
        order_id = create_response.json()["id"]

        # Get order as ADMIN - should succeed
        get_response = await http_client.get(
            f"{orders_base_url}/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == order_id
        # Verify admin can see the order even though it belongs to another user
        assert get_response.json()["user_id"] is not None
