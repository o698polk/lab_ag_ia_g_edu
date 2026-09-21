# Ref: BL-O6-006 | Skill: K-021 | Fase: F6
"""Technical audit + security events (≠ user history)."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, SecurityEvent


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def new_request_id() -> str:
        return str(uuid.uuid4())

    def record_audit(
        self,
        *,
        request_id: str,
        user_id: Optional[int],
        role: Optional[str],
        action: str,
        module: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str,
        reason: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        ev = AuditEvent(
            request_id=request_id,
            user_id=user_id,
            role=role,
            action=action,
            module=module,
            resource=resource,
            resource_id=resource_id,
            old_value=json.dumps(old_value) if old_value is not None else None,
            new_value=json.dumps(new_value) if new_value is not None else None,
            ip=ip,
            user_agent=user_agent,
            status=status,
            reason=reason,
        )
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    def record_security(
        self,
        *,
        request_id: str,
        user_id: Optional[int],
        event_type: str,
        severity: str = "MED",
        details: Optional[dict] = None,
    ) -> SecurityEvent:
        ev = SecurityEvent(
            request_id=request_id,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            details=json.dumps(details) if details else None,
        )
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    def list_audit(self, *, limit: int = 100) -> Sequence[AuditEvent]:
        return list(
            self.db.scalars(
                select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
            )
        )

    def list_security(self, *, limit: int = 100) -> Sequence[SecurityEvent]:
        return list(
            self.db.scalars(
                select(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(limit)
            )
        )
