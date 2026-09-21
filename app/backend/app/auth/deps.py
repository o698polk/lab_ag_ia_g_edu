# Ref: BL-O1-006 | Skill: K-016 | Fase: F6 | ADR-005
"""Auth dependencies — revalidate identity from DB (JWT is not absolute authz)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.role_service import AuthorizationError, assert_permission

bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user: User
    roles: list[str]
    permissions: list[str]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    try:
        payload = AuthService.decode_access(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN"
        ) from exc

    user_id = int(payload["sub"])
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_INACTIVE")

    # Revalidate from DB (Zero Trust) — do not trust JWT permission claims alone
    return CurrentUser(
        user=user,
        roles=user.role_codes(),
        permissions=sorted(user.permission_codes()),
    )


def require_permission(permission: str) -> Callable:
    def _dep(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        try:
            assert_permission(current.user, permission)
        except AuthorizationError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"decision": "DENY", "reason_code": exc.reason_code},
            ) from exc
        return current

    return _dep
