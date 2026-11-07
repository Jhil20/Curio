from unittest.mock import AsyncMock

import pytest
from app.db.session import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_root_liveness_health(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_v1_liveness_health(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_connected(mock_db_session: AsyncMock) -> None:
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_readiness_disconnected() -> None:
    async def failing_get_db():
        failing_mock = AsyncMock()
        failing_mock.execute.side_effect = ConnectionRefusedError("Database unreachable")
        yield failing_mock

    app.dependency_overrides[get_db] = failing_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.clear()
