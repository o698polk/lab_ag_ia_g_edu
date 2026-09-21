# Ref: K-004/K-013 | F6
"""API routers package."""

from fastapi import APIRouter

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.evaluation import router as evaluation_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.api.platform import router as platform_router
from app.api.roles import router as roles_router
from app.api.users import router as users_router
from app.api.zero_trust import router as zero_trust_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(catalog_router)
api_router.include_router(operations_router)
api_router.include_router(evaluation_router)
api_router.include_router(platform_router)
api_router.include_router(ai_router)
api_router.include_router(zero_trust_router)
