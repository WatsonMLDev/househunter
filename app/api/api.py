from fastapi import APIRouter
from app.api.endpoints import properties, zones, admin

api_router = APIRouter()

api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(zones.router, prefix="/zones", tags=["zones"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
