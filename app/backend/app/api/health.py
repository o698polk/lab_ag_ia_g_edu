# Ref: BL-QA-001 | Skill: K-004 | Fase: F5
"""Health endpoints — smoke check for F5 Gate."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe (no DB required)."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
        "phase": "F8",
    }


@router.get("/ready")
def ready() -> dict:
    """Readiness probe — config loaded; DB check deferred to F6/scripts."""
    settings = get_settings()
    warnings = []
    if settings.is_jwt_secret_default:
        warnings.append("JWT_SECRET is still the default placeholder")
    return {
        "status": "ready",
        "host": settings.app_host,
        "port": settings.app_port,
        "ai_provider": settings.ai_provider,
        "policy_path": settings.policy_path,
        "warnings": warnings,
    }
