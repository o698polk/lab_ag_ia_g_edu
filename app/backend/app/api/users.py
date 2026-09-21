# Ref: BL-O1-004 | Skill: K-013 | Fase: F6
"""Users API — Deny by Default via require_permission."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.iam import (
    AssignRolesRequest,
    UserCreate,
    UserOut,
    UserStatusUpdate,
    user_to_out,
)
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
            role_codes=body.role_codes,
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
