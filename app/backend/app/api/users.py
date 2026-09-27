# Ref: BL-O1-004 | Skill: K-013 | Fase: F6
"""Users API — Deny by Default via require_permission."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.iam import (
    AdminSetPasswordRequest,
    AssignRolesRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    UserStatusUpdate,
    UserUpdate,
    user_to_out,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return [user_to_out(u) for u in UserService(db).list_users()]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user = UserService(db).create_user(
            username=body.username,
            email=body.email,
            password=body.password,
            cedula=body.cedula,
            role_codes=body.role_codes,
            first_name=body.first_name,
            last_name=body.last_name,
            phone=body.phone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user_to_out(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return user_to_out(UserService(db).get_user(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return user_to_out(UserService(db).update_user(user_id, **body.model_dump(exclude_unset=True)))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{user_id}/login-as", response_model=TokenResponse)
def login_as(
    user_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.USERS_LOGIN_AS))],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    if current.impersonator_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ALREADY_IMPERSONATING",
        )
    try:
        tokens = AuthService(db).login_as(current.user, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        code = str(exc)
        status_code = (
            status.HTTP_403_FORBIDDEN
            if code == "USER_INACTIVE"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=code) from exc
    AuditService(db).record_security(
        request_id=AuditService.new_request_id(),
        user_id=current.user.id,
        event_type="IMPERSONATION_START",
        severity="MED",
        details={
            "admin_id": current.user.id,
            "user_id": user_id,
            "ip": request.client.host if request.client else None,
        },
    )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.patch("/{user_id}/status", response_model=UserOut)
def update_status(
    user_id: int,
    body: UserStatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return user_to_out(UserService(db).set_status(user_id, body.status))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{user_id}", response_model=UserOut)
def delete_user(
    user_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_DELETE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return user_to_out(UserService(db).soft_delete(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{user_id}/roles", response_model=UserOut)
def assign_roles(
    user_id: int,
    body: AssignRolesRequest,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return user_to_out(UserService(db).assign_roles(user_id, body.role_codes))
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def admin_set_password(
    user_id: int,
    body: AdminSetPasswordRequest,
    _: Annotated[CurrentUser, Depends(require_permission(P.USERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user = UserService(db).get_user(user_id)
        AuthService(db).set_password(user, body.new_password)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
