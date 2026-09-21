# Ref: BL-QA-001 | BL-O1-* | Skills: K-004/K-013/K-015 | Fase: F6
"""
SIGA FastAPI entrypoint — F6 O1 IAM active.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(level=settings.log_level, log_dir=settings.log_dir)

app = FastAPI(
    title=settings.app_name,
    version="0.2.0-f6-o1",
    description="SIGA — PolkDev F6 O1 IAM (JWT + RBAC Deny-by-Default)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.app_api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "message": "SIGA PolkDev — F6 O1 IAM",
        "docs": "/docs",
        "health": f"{settings.app_api_prefix}/health",
        "auth_login": f"{settings.app_api_prefix}/auth/login",
    }


_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_frontend), html=True), name="ui")
