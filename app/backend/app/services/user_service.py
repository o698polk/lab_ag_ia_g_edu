# Ref: BL-O1-004 | Skill: K-013 | Fase: F6
"""User management service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.models import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def list_users(self) -> Sequence[User]:
        return self.users.list_users()

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise LookupError("USER_NOT_FOUND")
        return user

    def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        role_codes: list[str] | None = None,
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
    ) -> User:
        if self.users.get_by_username_or_email(username) or self.users.get_by_username_or_email(
            email
        ):
            raise ValueError("USER_EXISTS")
        user = User(
            username=username,
            email=email,
            first_name=first_name or "",
            last_name=last_name or "",
            phone=phone or "",
            password_hash=hash_password(password),
            status="ACTIVE",
        )
        for code in role_codes or []:
            role = self.roles.get_by_code(code)
            if role is None:
                raise ValueError(f"ROLE_NOT_FOUND:{code}")
            user.roles.append(role)
        self.users.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(
        self,
        user_id: int,
        *,
        username: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        status: str | None = None,
        role_codes: list[str] | None = None,
    ) -> User:
        user = self.get_user(user_id)
        if username and username != user.username:
            if self.users.get_by_username_or_email(username):
                raise ValueError("USER_EXISTS")
            user.username = username
        if email and email != user.email:
            if self.users.get_by_username_or_email(email):
                raise ValueError("USER_EXISTS")
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        if status is not None:
            user.status = status
        if role_codes is not None:
            self.assign_roles(user_id, role_codes)
            return self.get_user(user_id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_status(self, user_id: int, status: str) -> User:
        user = self.get_user(user_id)
        user.status = status
        self.db.commit()
        return user

    def soft_delete(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.deleted_at = datetime.now(timezone.utc)
        user.status = "DELETED"
        self.db.commit()
        return user

    def assign_roles(self, user_id: int, role_codes: list[str]) -> User:
        user = self.get_user(user_id)
        roles = []
        for code in role_codes:
            role = self.roles.get_by_code(code)
            if role is None:
                raise ValueError(f"ROLE_NOT_FOUND:{code}")
            roles.append(role)
        user.roles = roles
        self.db.commit()
        self.db.refresh(user)
        return user
