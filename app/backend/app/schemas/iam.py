# Ref: BL-O1-* | Skill: K-013 | Fase: F6
"""Pydantic schemas for IAM."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    model_config = {"extra": "forbid"}

    refresh_token: str


class LogoutRequest(BaseModel):
    model_config = {"extra": "forbid"}

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    current_password: str
    new_password: str = Field(min_length=8)


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool
    permissions: List[str] = []

    model_config = {"from_attributes": True}


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str
    module: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    status: str
    roles: List[str] = []
    permissions: List[str] = []
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    model_config = {"extra": "forbid"}

    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8)
    role_codes: List[str] = []

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email")
        return v.lower()


class UserStatusUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    status: str


class AssignRolesRequest(BaseModel):
    model_config = {"extra": "forbid"}

    role_codes: List[str]


class AssignPermissionsRequest(BaseModel):
    model_config = {"extra": "forbid"}

    permission_codes: List[str]


def user_to_out(user) -> UserOut:  # noqa: ANN001
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        roles=user.role_codes(),
        permissions=sorted(user.permission_codes()),
        last_login=user.last_login,
        created_at=user.created_at,
    )


def role_to_out(role) -> RoleOut:  # noqa: ANN001
    return RoleOut(
        id=role.id,
        code=role.code,
        name=role.name,
        is_active=role.is_active,
        permissions=[p.code for p in role.permissions],
    )
