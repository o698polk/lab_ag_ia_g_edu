# Ref: BL-O1-005 | Skill: K-016 | Fase: F6
"""Roles and permissions API."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.iam import (
    AssignPermissionsRequest,
    PermissionCreate,
    PermissionOut,
    PermissionUpdate,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    role_to_out,
)
from app.services.role_service import RoleService

router = APIRouter(tags=["roles"])


@router.get("/roles", response_model=List[RoleOut])
def list_roles(
    _: Annotated[CurrentUser, Depends(require_permission(P.ROLES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return [role_to_out(r) for r in RoleService(db).list_roles()]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: RoleCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.ROLES_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        role = RoleService(db).create_role(body.code, body.name, body.description)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return role_to_out(role)


@router.patch("/roles/{role_code}", response_model=RoleOut)
def update_role(
    role_code: str,
    body: RoleUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.ROLES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        role = RoleService(db).update_role(role_code, **body.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return role_to_out(role)


@router.delete("/roles/{role_code}", response_model=RoleOut)
def deactivate_role(
    role_code: str,
    _: Annotated[CurrentUser, Depends(require_permission(P.ROLES_DELETE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        role = RoleService(db).deactivate_role(role_code)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return role_to_out(role)


@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return RoleService(db).list_permissions()


@router.post("/permissions", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(
    body: PermissionCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return RoleService(db).create_permission(body.code, body.description, body.module)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/permissions/{permission_id}", response_model=PermissionOut)
def update_permission(
    permission_id: int,
    body: PermissionUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return RoleService(db).update_permission(
            permission_id, **body.model_dump(exclude_unset=True)
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/permissions/{permission_id}", response_model=PermissionOut)
def delete_permission(
    permission_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_DELETE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return RoleService(db).deactivate_permission(permission_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/roles/{role_code}/permissions", response_model=RoleOut)
def assign_permissions(
    role_code: str,
    body: AssignPermissionsRequest,
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_ASSIGN))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        role = RoleService(db).assign_permissions(role_code, body.permission_codes)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return role_to_out(role)
