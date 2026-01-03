from fastapi import APIRouter
from app.api.endpoints import properties, zones, admin, auth, user_data

api_router = APIRouter()

api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(zones.router, prefix="/zones", tags=["zones"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user_data.router, prefix="/user", tags=["user"])
