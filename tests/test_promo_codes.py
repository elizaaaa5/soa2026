import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid


@pytest.mark.asyncio
async def test_create_promo_code_as_seller(http_client, seller_token, orders_base_url):
    """Test creating a promo code as SELLER"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)
    code = f"SUM{uuid.uuid4().hex[:6].upper()}"

    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": code,
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    if response.status_code != 201:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == code
    assert data["discount_type"] == "PERCENTAGE"
    assert data["discount_value"] == 10.0
    assert data["min_order_amount"] == 100.0
    assert data["max_uses"] == 1000
    assert data["current_uses"] == 0
    assert data["active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_promo_code_as_admin(http_client, admin_token, orders_base_url):
    """Test creating a promo code as ADMIN"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)
    code = f"WIN{uuid.uuid4().hex[:6].upper()}"

    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": code,
            "discount_type": "FIXED_AMOUNT",
            "discount_value": 50.0,
            "min_order_amount": 200.0,
            "max_uses": 500,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == code
    assert data["discount_type"] == "FIXED_AMOUNT"
    assert data["discount_value"] == 50.0
    assert data["min_order_amount"] == 200.0
    assert data["max_uses"] == 500
    assert data["current_uses"] == 0
    assert data["active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_user_cannot_create_promo_code(http_client, user_token, orders_base_url):
    """Test that USER cannot create promo code (should return 403)"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)

    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "code": "USERPROMO",
            "discount_type": "PERCENTAGE",
            "discount_value": 5.0,
            "min_order_amount": 50.0,
            "max_uses": 100,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["error_code"] == "ACCESS_DENIED"


@pytest.mark.asyncio
async def test_promo_code_exists_error(http_client, seller_token, orders_base_url):
    """Test PROMO_CODE_EXISTS error (400) when creating duplicate promo code"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)
    code = f"DUP{uuid.uuid4().hex[:6].upper()}"

    # Create first promo code
    await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": code,
            "discount_type": "PERCENTAGE",
            "discount_value": 15.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    # Try to create duplicate promo code
    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": code,
            "discount_type": "FIXED_AMOUNT",
            "discount_value": 20.0,
            "min_order_amount": 150.0,
            "max_uses": 500,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "PROMO_CODE_EXISTS"
    assert "Промокод уже существует" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_order_with_promo_code_discount(
    http_client, seller_token, user_token, orders_base_url, catalog_base_url
):
    """Test order with promo code (discount applied correctly)"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)
    code = f"DIS{uuid.uuid4().hex[:6].upper()}"

    # Create a promo code
    promo_response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": code,
            "discount_type": "PERCENTAGE",
            "discount_value": 20.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )
    assert promo_response.status_code == 201

    # Create a product in catalog
    product_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product",
            "description": "A test product",
            "price": 200.0,
            "stock": 100,
            "category": "electronics",
            "status": "ACTIVE",
        },
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Create order with promo code
    order_response = await http_client.post(
        f"{orders_base_url}/api/v1/orders",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
            "promo_code": code,
        },
    )

    assert order_response.status_code == 201
    order_data = order_response.json()

    # Verify discount was applied
    # Subtotal: 200.0
    # Discount (20%): 40.0
    # Total: 160.0
    assert order_data["total_amount"] == 160.0
    assert order_data["discount_amount"] == 40.0
    assert order_data["promo_code_id"] is not None


@pytest.mark.asyncio
async def test_promo_code_validation_dates(http_client, seller_token, orders_base_url):
    """Test that promo code with invalid dates returns error"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from - timedelta(
        days=1
    )  # Invalid: valid_until before valid_from

    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": f"INV{uuid.uuid4().hex[:6].upper()}",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_DATES"
    assert "valid_until должен быть позже valid_from" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_promo_code_validation_same_dates(
    http_client, seller_token, orders_base_url
):
    """Test that promo code with same dates returns error"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from  # Invalid: same dates

    response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": f"SAME{uuid.uuid4().hex[:6].upper()}",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_DATES"


@pytest.mark.asyncio
async def test_order_with_fixed_amount_promo_code(
    http_client, seller_token, user_token, orders_base_url, catalog_base_url
):
    """Test order with fixed amount promo code"""
    valid_from = datetime.now(timezone.utc)
    valid_until = valid_from + timedelta(days=30)
    code = f"FIX{uuid.uuid4().hex[:6].upper()}"

    # Create a promo code with fixed amount discount
    promo_response = await http_client.post(
        f"{orders_base_url}/api/v1/promo-codes",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "code": code,
            "discount_type": "FIXED_AMOUNT",
            "discount_value": 50.0,
            "min_order_amount": 100.0,
            "max_uses": 1000,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
    )
    assert promo_response.status_code == 201

    # Create a product in catalog
    product_response = await http_client.post(
        f"{catalog_base_url}/products",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "name": "Test Product 2",
            "description": "Another test product",
            "price": 200.0,
            "stock": 100,
            "category": "electronics",
            "status": "ACTIVE",
        },
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Create order with promo code
    order_response = await http_client.post(
        f"{orders_base_url}/api/v1/orders",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
            "promo_code": code,
        },
    )

    assert order_response.status_code == 201
    order_data = order_response.json()

    # Verify discount was applied
    # Subtotal: 200.0
    # Discount (fixed): 50.0
    # Total: 150.0
    assert order_data["total_amount"] == 150.0
    assert order_data["discount_amount"] == 50.0
    assert order_data["promo_code_id"] is not None
