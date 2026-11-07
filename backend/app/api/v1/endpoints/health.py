from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthCheckResponse, ReadinessCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Health Check",
)
async def liveness_health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
    )


@router.get(
    "/health/ready",
    response_model=ReadinessCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Health Check",
)
async def readiness_health_check(
    db: AsyncSession = Depends(get_db),
) -> ReadinessCheckResponse:
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return ReadinessCheckResponse(
        status="ready" if db_status == "connected" else "degraded",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_status,
    )
