import pytest
import httpx
import uuid
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for making API requests."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def users_base_url() -> str:
    """Return the base URL for the users service."""
    return "http://localhost:8001"


@pytest.fixture
def catalog_base_url() -> str:
    """Return the base URL for the catalog service."""
    return "http://localhost:8002"


@pytest.fixture
def orders_base_url() -> str:
    """Return the base URL for the orders service."""
    return "http://localhost:8003"


@pytest.fixture
async def user_token(http_client: httpx.AsyncClient, users_base_url: str) -> str:
    """Register a USER and return the access token."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": f"user_{uuid.uuid4()}@example.com",
            "password": "userpass123",
            "role": "USER"
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def seller_token(http_client: httpx.AsyncClient, users_base_url: str) -> str:
    """Register a SELLER and return the access token."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": f"seller_{uuid.uuid4()}@example.com",
            "password": "sellerpass123",
            "role": "SELLER"
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def admin_token(http_client: httpx.AsyncClient, users_base_url: str) -> str:
    """Register an ADMIN and return the access token."""
    response = await http_client.post(
        f"{users_base_url}/auth/register",
        json={
            "email": f"admin_{uuid.uuid4()}@example.com",
            "password": "adminpass123",
            "role": "ADMIN"
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]
