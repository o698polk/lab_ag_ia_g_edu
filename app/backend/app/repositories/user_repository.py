# Ref: BL-O1-004 | Skill: K-013 | Fase: F6
"""User repository."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Role, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id, User.deleted_at.is_(None))
        )
        return self.db.scalar(stmt)

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(
                User.deleted_at.is_(None),
                or_(User.username == identifier, User.email == identifier),
            )
        )
        return self.db.scalar(stmt)

    def list_users(self) -> Sequence[User]:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.deleted_at.is_(None))
            .order_by(User.id)
        )
        return self.db.scalars(stmt).all()

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
