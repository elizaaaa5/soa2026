"""Tests for JSON logging middleware"""

import json
import pytest
import subprocess
import re
from typing import Dict, Any


@pytest.fixture
def gateway_base_url() -> str:
    """Return the base URL for the gateway service."""
    return "http://localhost:8000"


@pytest.fixture
def get_gateway_logs():
    """Helper function to get gateway container logs."""
    def _get_logs(lines: int = 50) -> list[Dict[str, Any]]:
        # Get gateway container logs
        result = subprocess.run(
            ["docker", "logs", "soa2026-gateway-1", "--tail", str(lines)],
            capture_output=True,
            text=True
        )

        # Parse JSON log lines
        logs = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

        return logs
    return _get_logs


@pytest.mark.asyncio
async def test_log_contains_request_id(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain request_id field."""
    # Make a request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    # Check that request_id exists and is not empty
    log_entry = logs[-1]  # Get the most recent log
    assert "request_id" in log_entry, "request_id field missing from log"
    assert log_entry["request_id"], "request_id should not be empty"
    assert isinstance(log_entry["request_id"], str), "request_id should be a string"


@pytest.mark.asyncio
async def test_log_contains_method(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain method field."""
    # Make a GET request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "method" in log_entry, "method field missing from log"
    assert log_entry["method"] == "GET", f"Expected method 'GET', got '{log_entry['method']}'"


@pytest.mark.asyncio
async def test_log_contains_endpoint(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain endpoint field."""
    # Make a request to a specific endpoint
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "endpoint" in log_entry, "endpoint field missing from log"
    assert log_entry["endpoint"] == "/health", f"Expected endpoint '/health', got '{log_entry['endpoint']}'"


@pytest.mark.asyncio
async def test_log_contains_status_code(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain status_code field."""
    # Make a request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "status_code" in log_entry, "status_code field missing from log"
    assert log_entry["status_code"] == response.status_code, \
        f"Expected status_code {response.status_code}, got {log_entry['status_code']}"
    assert isinstance(log_entry["status_code"], int), "status_code should be an integer"


@pytest.mark.asyncio
async def test_log_contains_duration_ms(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain duration_ms field."""
    # Make a request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "duration_ms" in log_entry, "duration_ms field missing from log"
    assert isinstance(log_entry["duration_ms"], int), "duration_ms should be an integer"
    assert log_entry["duration_ms"] >= 0, "duration_ms should be non-negative"


@pytest.mark.asyncio
async def test_log_contains_timestamp(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain timestamp field in ISO format."""
    # Make a request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "timestamp" in log_entry, "timestamp field missing from log"
    assert isinstance(log_entry["timestamp"], str), "timestamp should be a string"

    # Check ISO format (YYYY-MM-DDTHH:MM:SS.ssssss+00:00)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$'
    assert re.match(iso_pattern, log_entry["timestamp"]), \
        f"timestamp '{log_entry['timestamp']}' is not in ISO format"


@pytest.mark.asyncio
async def test_log_contains_user_id_when_authenticated(
    http_client,
    gateway_base_url: str,
    get_gateway_logs,
    user_token: str
):
    """Test that logs contain user_id when authenticated."""
    # Make an authenticated request
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await http_client.get(f"{gateway_base_url}/api/users/me", headers=headers)

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "user_id" in log_entry, "user_id field missing from log"
    assert log_entry["user_id"] is not None, "user_id should not be None for authenticated requests"
    assert isinstance(log_entry["user_id"], (str, int)), "user_id should be a string or integer"


@pytest.mark.asyncio
async def test_log_contains_request_body_for_post(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs contain request_body for POST requests."""
    # Make a POST request with a body
    request_data = {
        "email": f"test_{pytest.current_time if hasattr(pytest, 'current_time') else 'user'}@example.com",
        "password": "testpass123",
        "role": "USER"
    }

    response = await http_client.post(
        f"{gateway_base_url}/api/auth/register",
        json=request_data
    )

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "request_body" in log_entry, "request_body field missing from log for POST request"
    assert isinstance(log_entry["request_body"], dict), "request_body should be a dictionary"
    assert "email" in log_entry["request_body"], "request_body should contain email field"


@pytest.mark.asyncio
async def test_log_contains_request_body_for_put(
    http_client,
    gateway_base_url: str,
    get_gateway_logs,
    user_token: str
):
    """Test that logs contain request_body for PUT requests."""
    # Make a PUT request with a body
    headers = {"Authorization": f"Bearer {user_token}"}
    request_data = {"email": "updated@example.com"}

    response = await http_client.put(
        f"{gateway_base_url}/api/users/me",
        headers=headers,
        json=request_data
    )

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "request_body" in log_entry, "request_body field missing from log for PUT request"
    assert isinstance(log_entry["request_body"], dict), "request_body should be a dictionary"


@pytest.mark.asyncio
async def test_log_contains_request_body_for_delete(
    http_client,
    gateway_base_url: str,
    get_gateway_logs,
    user_token: str
):
    """Test that logs contain request_body for DELETE requests."""
    # Make a DELETE request with a body (if supported)
    headers = {"Authorization": f"Bearer {user_token}"}
    request_data = {"reason": "test deletion"}

    response = await http_client.delete(
        f"{gateway_base_url}/api/users/me",
        headers=headers,
        json=request_data
    )

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "request_body" in log_entry, "request_body field missing from log for DELETE request"
    assert isinstance(log_entry["request_body"], dict), "request_body should be a dictionary"


@pytest.mark.asyncio
async def test_password_is_masked_in_logs(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that password field is masked in logs."""
    # Make a POST request with password
    request_data = {
        "email": f"mask_test_{pytest.current_time if hasattr(pytest, 'current_time') else 'user'}@example.com",
        "password": "secret_password_123",
        "role": "USER"
    }

    response = await http_client.post(
        f"{gateway_base_url}/api/auth/register",
        json=request_data
    )

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "request_body" in log_entry, "request_body field missing from log"
    assert "password" in log_entry["request_body"], "password field missing from request_body"

    # Check that password is masked
    assert log_entry["request_body"]["password"] == "***", \
        f"password should be masked with '***', got '{log_entry['request_body']['password']}'"

    # Ensure the original password is NOT in the log
    log_str = json.dumps(log_entry)
    assert "secret_password_123" not in log_str, "Original password should not appear in logs"


@pytest.mark.asyncio
async def test_refresh_token_is_masked_in_logs(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that refresh_token field is masked in logs."""
    # Make a POST request with refresh_token
    request_data = {
        "refresh_token": "secret_refresh_token_xyz123"
    }

    response = await http_client.post(
        f"{gateway_base_url}/api/auth/refresh",
        json=request_data
    )

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "request_body" in log_entry, "request_body field missing from log"

    # Check if refresh_token is in the request body (may not be present if endpoint doesn't exist)
    if "refresh_token" in log_entry["request_body"]:
        # Check that refresh_token is masked
        assert log_entry["request_body"]["refresh_token"] == "***", \
            f"refresh_token should be masked with '***', got '{log_entry['request_body']['refresh_token']}'"

        # Ensure the original refresh_token is NOT in the log
        log_str = json.dumps(log_entry)
        assert "secret_refresh_token_xyz123" not in log_str, "Original refresh_token should not appear in logs"


@pytest.mark.asyncio
async def test_log_no_request_body_for_get(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that logs do NOT contain request_body for GET requests."""
    # Make a GET request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    # request_body should not be present for GET requests
    assert "request_body" not in log_entry, \
        "request_body should not be present in logs for GET requests"


@pytest.mark.asyncio
async def test_log_user_id_null_when_unauthenticated(
    http_client,
    gateway_base_url: str,
    get_gateway_logs
):
    """Test that user_id is None when not authenticated."""
    # Make an unauthenticated request
    response = await http_client.get(f"{gateway_base_url}/health")
    response.raise_for_status()

    # Get logs
    logs = get_gateway_logs()

    # Find the log entry for this request
    assert len(logs) > 0, "No logs found"

    log_entry = logs[-1]
    assert "user_id" in log_entry, "user_id field missing from log"
    assert log_entry["user_id"] is None, "user_id should be None for unauthenticated requests"
