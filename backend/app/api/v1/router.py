from fastapi import APIRouter

from app.api.v1.endpoints import discovery, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["Discovery"])
