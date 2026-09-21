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
    PermissionOut,
    RoleOut,
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


@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(
    _: Annotated[CurrentUser, Depends(require_permission(P.PERMISSIONS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return RoleService(db).list_permissions()


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
