from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_db_session() -> AsyncMock:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = None
    return mock_session
