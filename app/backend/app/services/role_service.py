# Ref: BL-O1-005/006 | Skill: K-016 | Fase: F6
"""Role/permission service + Deny-by-Default checks."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.models import Permission, Role, User
from app.repositories.role_repository import RoleRepository


class AuthorizationError(PermissionError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class RoleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.roles = RoleRepository(db)

    def list_roles(self) -> Sequence[Role]:
        return self.roles.list_roles()

    def list_permissions(self) -> Sequence[Permission]:
        return self.roles.list_permissions()

    PROTECTED = {"ADMINISTRATOR", "TEACHER", "STUDENT"}

    def create_role(self, code: str, name: str) -> Role:
        code = code.strip().upper()
        existing = self.roles.get_by_code(code)
        if existing is not None:
            raise ValueError("ROLE_EXISTS")
        role = Role(code=code, name=name.strip(), is_active=True)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def deactivate_role(self, role_code: str) -> Role:
        role = self.roles.get_by_code(role_code)
        if role is None:
            raise LookupError("ROLE_NOT_FOUND")
        if role.code in self.PROTECTED:
            raise ValueError("ROLE_PROTECTED")
        role.is_active = False
        self.db.commit()
        self.db.refresh(role)
        return role

    def assign_permissions(self, role_code: str, permission_codes: list[str]) -> Role:
        role = self.roles.get_by_code(role_code)
        if role is None:
            raise LookupError("ROLE_NOT_FOUND")
        perms = []
        for code in permission_codes:
            perm = self.roles.get_permission_by_code(code)
            if perm is None:
                raise ValueError(f"PERMISSION_NOT_FOUND:{code}")
            perms.append(perm)
        role.permissions = perms
        self.db.commit()
        self.db.refresh(role)
        return role


def assert_permission(user: User, permission: str) -> None:
    """Deny by Default — missing explicit permission => DENY."""
    if not user.is_active:
        raise AuthorizationError("USER_INACTIVE")
    if permission not in user.permission_codes():
        raise AuthorizationError("PERMISSION_MISSING")
