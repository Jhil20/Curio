from pydantic import BaseModel, ConfigDict


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    status: str
    environment: str
    version: str


class ReadinessCheckResponse(HealthCheckResponse):
    database: str
