# Ref: BL-O1-002 | Skill: K-015 | Fase: F6 | ADR-005
"""JWT access/refresh token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    *,
    user_id: int,
    username: str,
    roles: list[str],
    permissions: list[str],
) -> str:
    settings = get_settings()
    exp = _now() + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": roles[0] if roles else None,
        "roles": roles,
        "permissions": permissions,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_reset_token(*, user_id: int, username: str) -> str:
    settings = get_settings()
    exp = _now() + timedelta(minutes=15)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "password_reset",
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, expected_type: str = "access") -> dict[str, Any]:
    """Decode JWT with algorithm whitelist and type check (F8)."""
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise jwt.InvalidTokenError("INVALID_HEADER") from exc
    alg = str(header.get("alg", ""))
    allowed = {settings.jwt_algorithm}
    if alg.lower() == "none" or alg not in allowed:
        raise jwt.InvalidAlgorithmError("ALG_NOT_ALLOWED")
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "type"]},
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("INVALID_TOKEN_TYPE")
    return payload


def new_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    settings = get_settings()
    return _now() + timedelta(days=settings.jwt_refresh_ttl_days)


def session_expiry() -> datetime:
    settings = get_settings()
    return _now() + timedelta(minutes=settings.jwt_access_ttl_minutes)
