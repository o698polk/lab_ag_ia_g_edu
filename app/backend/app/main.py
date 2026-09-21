# Ref: BL-QA-001 | BL-O1-* | F8 | Skills: K-004/K-007/K-013/K-015
"""
SIGA FastAPI entrypoint — F8 security hardening active.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security_middleware import LoginRateLimitMiddleware, SecurityHeadersMiddleware

settings = get_settings()
setup_logging(level=settings.log_level, log_dir=settings.log_dir)

app = FastAPI(
    title=settings.app_name,
    version="0.8.0-f8",
    description="SIGA — PolkDev F8 Security (JWT + RBAC/ABAC + Gateway/PDP)",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

# Middleware order: last added runs first on request
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    LoginRateLimitMiddleware,
    max_attempts=20 if settings.app_env == "test" else 10,
    window_seconds=60,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix=settings.app_api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "message": "SIGA PolkDev — F8 Security",
        "docs": "/docs" if settings.app_debug else None,
        "health": f"{settings.app_api_prefix}/health",
        "auth_login": f"{settings.app_api_prefix}/auth/login",
    }


_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_frontend), html=True), name="ui")
