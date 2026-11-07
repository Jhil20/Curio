import pytest
from app.core.config import Settings
from app.core.exceptions import NotFoundException
from app.main import app
from httpx import ASGITransport, AsyncClient


def test_settings_defaults() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL=None,
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
    )
    assert settings.PROJECT_NAME == "Curio"
    assert settings.async_database_url == (
        "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
    )


def test_settings_custom_database_url() -> None:
    custom_url = "postgresql+asyncpg://custom_user:custom_pass@dbhost:5433/custom_db"
    settings = Settings(DATABASE_URL=custom_url)
    assert settings.async_database_url == custom_url


@pytest.mark.asyncio
async def test_custom_exception_handler() -> None:
    @app.get("/test-error")
    async def trigger_error() -> None:
        raise NotFoundException("Custom resource missing")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-error")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NotFoundException"
        assert data["error"]["message"] == "Custom resource missing"
