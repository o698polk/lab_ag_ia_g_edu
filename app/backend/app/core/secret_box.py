# Ref: RF-AI-CFG | Skill: K-018 | Fase: post-F12
"""Symmetric encryption for stored credentials. Never log plaintext."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

_PURPOSE = b"siga.ai-settings.v1:"


def _fernet() -> Fernet:
    secret = get_settings().jwt_secret.encode("utf-8")
    digest = hashlib.sha256(_PURPOSE + secret).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ValueError("SECRET_UNREADABLE") from exc


def key_hint(plain: str) -> str:
    if not plain:
        return ""
    tail = plain[-4:] if len(plain) >= 4 else "****"
    return f"••••{tail}"
