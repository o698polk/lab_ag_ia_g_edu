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
    impersonator_id: int | None = None


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

    raw_impersonator = payload.get("impersonator_id")
    impersonator_id = int(raw_impersonator) if raw_impersonator else None

    # Revalidate from DB (Zero Trust) — do not trust JWT permission claims alone
    return CurrentUser(
        user=user,
        roles=user.role_codes(),
        permissions=sorted(user.permission_codes()),
        impersonator_id=impersonator_id,
    )


def _forbidden(exc: AuthorizationError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"decision": "DENY", "reason_code": exc.reason_code},
    )


def require_permission(permission: str) -> Callable:
    def _dep(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        try:
            assert_permission(current.user, permission)
        except AuthorizationError as exc:
            raise _forbidden(exc) from exc
        return current

    return _dep


def require_permission_or_impersonator(permission: str) -> Callable:
    """Allow the actor or, during login-as, the original admin."""

    def _dep(
        current: Annotated[CurrentUser, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> CurrentUser:
        try:
            assert_permission(current.user, permission)
            return current
        except AuthorizationError as actor_exc:
            if not current.impersonator_id:
                raise _forbidden(actor_exc) from actor_exc
            admin = UserRepository(db).get_by_id(current.impersonator_id)
            if admin is None or not admin.is_active:
                raise _forbidden(actor_exc) from actor_exc
            try:
                assert_permission(admin, permission)
            except AuthorizationError as admin_exc:
                raise _forbidden(admin_exc) from admin_exc
            return current

    return _dep
