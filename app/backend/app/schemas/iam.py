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


class ForgotPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    username: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8)


class ForgotPasswordOut(BaseModel):
    accepted: bool = True
    reset_token: Optional[str] = None


class AdminSetPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    new_password: str = Field(min_length=8)


class RoleCreate(BaseModel):
    model_config = {"extra": "forbid"}

    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    description: str = ""


class RoleUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    name: Optional[str] = Field(default=None, min_length=2, max_length=128)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str = ""
    is_active: bool
    permissions: List[str] = []
    users_count: int = 0

    model_config = {"from_attributes": True}


class PermissionCreate(BaseModel):
    model_config = {"extra": "forbid"}

    code: str = Field(min_length=3, max_length=128)
    description: str = ""
    module: str = Field(min_length=2, max_length=64)


class PermissionUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    description: Optional[str] = None
    module: Optional[str] = None
    is_active: Optional[bool] = None


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str
    module: str
    is_active: bool = True

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str = ""
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
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    role_codes: List[str] = []

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email")
        return v.lower()


class UserUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    role_codes: Optional[List[str]] = None

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
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
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        full_name=user.full_name,
        phone=user.phone or "",
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
        description=getattr(role, "description", "") or "",
        is_active=role.is_active,
        permissions=[p.code for p in role.permissions],
        users_count=len(role.users or []),
    )
