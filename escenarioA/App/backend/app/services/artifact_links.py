"""URLs firmadas para descarga directa de artifacts (SPEC-021)."""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime

from flask import current_app


def _secret() -> bytes:
    key = current_app.config.get("SECRET_KEY") or current_app.config.get("JWT_SECRET_KEY") or "dev"
    return str(key).encode("utf-8")


def _sign(artifact_id: int, expires: int, user_id: int) -> str:
    payload = f"{int(artifact_id)}:{int(expires)}:{int(user_id)}"
    return hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def artifact_download_path(artifact) -> str:
    """Path completo API usable en navegador: /api/v1/ai/artifacts/<id>/download?expires=&sig="""
    now = int(time.time())
    if artifact.expires_at:
        exp_ts = int(artifact.expires_at.timestamp())
    else:
        exp_ts = now + 72 * 3600
    # No firmar más allá de la caducidad del artifact
    expires = max(now + 60, exp_ts)
    sig = _sign(artifact.id, expires, artifact.user_id)
    return f"/api/v1/ai/artifacts/{artifact.id}/download?expires={expires}&sig={sig}"


def verify_artifact_download_sig(artifact, expires: str | None, sig: str | None) -> bool:
    if not expires or not sig or artifact is None:
        return False
    try:
        exp = int(expires)
    except (TypeError, ValueError):
        return False
    if exp < int(time.time()):
        return False
    if artifact.expires_at and artifact.expires_at < datetime.utcnow():
        return False
    expected = _sign(artifact.id, exp, artifact.user_id)
    return hmac.compare_digest(expected, str(sig))
