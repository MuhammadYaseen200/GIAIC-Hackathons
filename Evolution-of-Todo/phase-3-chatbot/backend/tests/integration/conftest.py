"""Shared fixtures for integration tests.

Provides authenticated HTTP client that registers a real user
and uses a valid JWT token for all requests.
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient

BASE_URL = "http://localhost:8000"


@pytest_asyncio.fixture
async def test_client():
    """Create authenticated async test client.

    Registers a unique test user, logs in, and provides
    a client with a valid Authorization header.
    """
    unique_id = uuid4().hex[:8]
    email = f"inttest_{unique_id}@example.com"
    password = "TestPass123"

    async with AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Integration Test User",
            },
        )

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

        if login_resp.status_code == 200:
            token = login_resp.json()["data"]["token"]
            client.headers["Authorization"] = f"Bearer {token}"

        yield client
