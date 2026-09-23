# Ref: BL-O1-002/003 | Skill: K-015 | Fase: F6
"""Authentication application service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.password import hash_password, verify_password
from app.auth.tokens import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_token,
    new_refresh_token_value,
    refresh_expiry,
    session_expiry,
)
from app.core.config import get_settings
from app.models import RefreshToken, SessionToken, User
from app.repositories.user_repository import UserRepository


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def login(
        self,
        identifier: str,
        password: str,
        *,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthTokens:
        user = self.users.get_by_username_or_email(identifier)
        if user is None or not verify_password(password, user.password_hash):
            raise PermissionError("INVALID_CREDENTIALS")
        if not user.is_active:
            raise PermissionError("USER_INACTIVE")

        roles = user.role_codes()
        perms = sorted(user.permission_codes())
        access = create_access_token(
            user_id=user.id,
            username=user.username,
            roles=roles,
            permissions=perms,
        )
        refresh_raw = new_refresh_token_value()
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_raw),
                expires_at=refresh_expiry(),
                revoked=False,
            )
        )
        self.db.add(
            SessionToken(
                user_id=user.id,
                session_id=str(uuid.uuid4()),
                expires_at=session_expiry(),
                ip=ip,
                user_agent=user_agent,
            )
        )
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        return AuthTokens(access_token=access, refresh_token=refresh_raw)

    def refresh(self, refresh_token: str) -> AuthTokens:
        token_h = hash_token(refresh_token)
        row = self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_h)
        )
        if row is None or row.revoked:
            raise PermissionError("INVALID_REFRESH")
        now = datetime.now(timezone.utc)
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < now:
            raise PermissionError("REFRESH_EXPIRED")

        user = self.users.get_by_id(row.user_id)
        if user is None or not user.is_active:
            raise PermissionError("USER_INACTIVE")

        row.revoked = True
        new_raw = new_refresh_token_value()
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(new_raw),
                expires_at=refresh_expiry(),
                revoked=False,
            )
        )
        access = create_access_token(
            user_id=user.id,
            username=user.username,
            roles=user.role_codes(),
            permissions=sorted(user.permission_codes()),
        )
        self.db.commit()
        return AuthTokens(access_token=access, refresh_token=new_raw)

    def logout(self, refresh_token: str) -> None:
        token_h = hash_token(refresh_token)
        row = self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_h)
        )
        if row is not None:
            row.revoked = True
            self.db.commit()

    def change_password(self, user: User, current: str, new_password: str) -> None:
        if not verify_password(current, user.password_hash):
            raise PermissionError("INVALID_CREDENTIALS")
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def request_password_reset(self, identifier: str) -> Optional[str]:
        """Issue reset JWT if user exists. Token returned only in local/test."""
        user = self.users.get_by_username_or_email(identifier)
        if user is None or not user.is_active:
            return None
        token = create_reset_token(user_id=user.id, username=user.username)
        env = get_settings().app_env
        if env in {"local", "test"}:
            return token
        return None

    def reset_password(self, token: str, new_password: str) -> None:
        payload = decode_token(token, expected_type="password_reset")
        user = self.users.get_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise PermissionError("USER_INACTIVE")
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def set_password(self, user: User, new_password: str) -> None:
        user.password_hash = hash_password(new_password)
        self.db.commit()

    @staticmethod
    def decode_access(token: str) -> dict:
        payload = decode_token(token, expected_type="access")
        if payload.get("type") != "access":
            raise PermissionError("INVALID_TOKEN_TYPE")
        return payload
