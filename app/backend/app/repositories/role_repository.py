# Ref: BL-O1-005 | Skill: K-016 | Fase: F6
"""Role and permission repository."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Permission, Role


class RoleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> Optional[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.code == code)
        )
        return self.db.scalar(stmt)

    def get_by_id(self, role_id: int) -> Optional[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return self.db.scalar(stmt)

    def list_roles(self) -> Sequence[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
        return self.db.scalars(stmt).all()

    def list_permissions(self) -> Sequence[Permission]:
        return self.db.scalars(select(Permission).order_by(Permission.code)).all()

    def get_permission_by_code(self, code: str) -> Optional[Permission]:
        return self.db.scalar(select(Permission).where(Permission.code == code))
