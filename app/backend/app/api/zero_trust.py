# Ref: BL-O6-001/006 | Skill: K-013/K-020/K-021 | Fase: F6
"""Policies inventory + technical audit/security APIs."""

from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.policy.pap import get_pap
from app.tools.registry import list_tools

router = APIRouter(tags=["zero-trust"])


class PolicyOut(BaseModel):
    policy_id: str
    version: str
    module: str
    effect_default: str
    rules_count: int


class ToolOut(BaseModel):
    tool_name: str
    risk_level: str
    required_permissions: list[str]
    allowed_roles: list[str]
    resource_type: str


class AuditOut(BaseModel):
    id: int
    request_id: str
    user_id: Optional[int]
    action: str
    module: str
    status: str
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityOut(BaseModel):
    id: int
    request_id: str
    user_id: Optional[int]
    event_type: str
    severity: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/policies", response_model=List[PolicyOut])
def list_policies(
    _: Annotated[CurrentUser, Depends(require_permission(P.AUDIT_VIEW))],
):
    return [
        PolicyOut(
            policy_id=p.policy_id,
            version=p.version,
            module=p.module,
            effect_default=p.effect_default,
            rules_count=len(p.rules),
        )
        for p in get_pap().list()
    ]


@router.get("/tools", response_model=List[ToolOut])
def list_registered_tools(
    _: Annotated[CurrentUser, Depends(require_permission(P.AUDIT_VIEW))],
):
    return [
        ToolOut(
            tool_name=t.tool_name,
            risk_level=t.risk_level,
            required_permissions=t.required_permissions,
            allowed_roles=t.allowed_roles,
            resource_type=t.resource_type,
        )
        for t in list_tools()
    ]


@router.get("/audit/events", response_model=List[AuditOut])
def audit_events(
    _: Annotated[CurrentUser, Depends(require_permission(P.AUDIT_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return list(AuditService(db).list_audit())


@router.get("/security/events", response_model=List[SecurityOut])
def security_events(
    _: Annotated[CurrentUser, Depends(require_permission(P.AUDIT_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return list(AuditService(db).list_security())
