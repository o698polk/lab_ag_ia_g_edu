# Ref: BL-O6-004 | Skill: K-019 | Fase: F6
"""Tool Gateway PEP — validate → bind CURRENT_USER → PDP → execute/deny."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import CurrentUser
from app.models import (
    AcademicTerm,
    Enrollment,
    Evaluation,
    Student,
    Teacher,
    ToolInvocation,
    ToolRegistryEntry,
    User,
)
from app.models.operations import Course
from app.policy.pdp import AuthzRequest, PDP, Subject
from app.services.ai_settings_service import AiSettingsService
from app.services.operations_service import OperationsService
from app.tools import handlers
from app.tools.registry import TOOLS, ToolMeta, get_tool


class GatewayResult:
    def __init__(
        self,
        *,
        decision: str,
        reason_code: str,
        policy_id: str = "NONE",
        policy_version: str = "v1",
        tool: str,
        parameters: dict,
        result: Any = None,
        request_id: str = "",
    ) -> None:
        self.decision = decision
        self.reason_code = reason_code
        self.policy_id = policy_id
        self.policy_version = policy_version
        self.tool = tool
        self.parameters = parameters
        self.result = result
        self.request_id = request_id

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "tool": self.tool,
            "parameters": self.parameters,
            "result": self.result,
            "request_id": self.request_id,
        }


class ToolGateway:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pdp = PDP()
        self.audit = AuditService(db)
        self.ops = OperationsService(db)

    def ensure_registry_seeded(self) -> None:
        for meta in TOOLS.values():
            existing = self.db.scalar(
                select(ToolRegistryEntry).where(
                    ToolRegistryEntry.tool_name == meta.tool_name
                )
            )
            if existing:
                continue
            self.db.add(
                ToolRegistryEntry(
                    tool_name=meta.tool_name,
                    description=meta.description,
                    method=meta.method,
                    endpoint=meta.endpoint,
                    parameters_schema=json.dumps(meta.parameters_schema),
                    required_permissions=json.dumps(meta.required_permissions),
                    allowed_roles=json.dumps(meta.allowed_roles),
                    resource_type=meta.resource_type,
                    risk_level=meta.risk_level,
                    is_active=True,
                )
            )
        self.db.commit()

    def invoke(
        self,
        *,
        current: CurrentUser,
        tool_name: str,
        parameters: Optional[dict] = None,
        message_id: Optional[int] = None,
        request_id: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> GatewayResult:
        self.ensure_registry_seeded()
        rid = request_id or self.audit.new_request_id()
        params = dict(parameters or {})

        meta = get_tool(tool_name)
        if meta is None or not meta.is_active:
            return self._deny(
                current=current,
                tool_name=tool_name,
                params=params,
                reason="TOOL_NOT_ALLOWED",
                policy_id="NONE",
                rid=rid,
                message_id=message_id,
                ip=ip,
                user_agent=user_agent,
                security_type="TOOL_DENY",
            )

        # Identity resolution — bind CURRENT_USER (RF-AI-005)
        params = self._bind_current_user(current, meta, params)
        enforced = AiSettingsService(self.db).policies_enforced(current.user.id)
        if not enforced:
            params = self._bind_open_scope(meta, params)
            return self._execute_open(
                current=current,
                meta=meta,
                tool_name=tool_name,
                params=params,
                rid=rid,
                message_id=message_id,
                ip=ip,
                user_agent=user_agent,
            )

        role_denial = self._deny_if_role_or_permission_missing(
            current=current,
            meta=meta,
            tool_name=tool_name,
            params=params,
            rid=rid,
            message_id=message_id,
            ip=ip,
            user_agent=user_agent,
        )
        if role_denial:
            return role_denial

        # Anti-IDOR for student-scoped reads
        idor = self._check_ownership(current, meta, params)
        if idor:
            return self._deny(
                current=current,
                tool_name=tool_name,
                params=params,
                reason="RESOURCE_NOT_OWNED",
                policy_id="POL-STU-001",
                rid=rid,
                message_id=message_id,
                ip=ip,
                user_agent=user_agent,
                security_type="IDOR_ATTEMPT",
            )

        context = self._build_context(current, meta, params)
        decision = self.pdp.evaluate(
            AuthzRequest(
                subject=Subject(
                    user_id=current.user.id,
                    roles=current.roles,
                    permissions=current.permissions,
                    status=current.user.status,
                ),
                action=tool_name,
                resource={
                    "type": meta.resource_type,
                    "id": str(params.get("student_id") or params.get("evaluation_id") or ""),
                },
                context=context,
            )
        )

        if decision.decision != "ALLOW":
            return self._deny(
                current=current,
                tool_name=tool_name,
                params=params,
                reason=decision.reason_code,
                policy_id=decision.policy_id,
                policy_version=decision.policy_version,
                rid=rid,
                message_id=message_id,
                ip=ip,
                user_agent=user_agent,
                security_type="TOOL_DENY" if meta.risk_level == "HIGH" else "ACCESS_DENY",
            )

        # ALLOW — execute handler (never AI→MySQL)
        try:
            result = handlers.execute(self.db, tool_name, params, current)
            status = "SUCCESS"
        except Exception as exc:  # noqa: BLE001
            result = {"error": str(exc)}
            status = "ERROR"

        self._persist_invocation(
            tool_name=tool_name,
            user_id=current.user.id,
            message_id=message_id,
            params=params,
            decision="ALLOW",
            reason_code=decision.reason_code,
            policy_id=decision.policy_id,
            status=status,
        )
        self.audit.record_audit(
            request_id=rid,
            user_id=current.user.id,
            role=current.roles[0] if current.roles else None,
            action=tool_name,
            module="gateway",
            resource=meta.resource_type,
            resource_id=str(params.get("student_id") or ""),
            status=status,
            reason=decision.reason_code,
            new_value=params,
            ip=ip,
            user_agent=user_agent,
        )
        return GatewayResult(
            decision="ALLOW",
            reason_code=decision.reason_code,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            tool=tool_name,
            parameters=params,
            result=result,
            request_id=rid,
        )

    def _execute_open(
        self,
        *,
        current: CurrentUser,
        meta: ToolMeta,
        tool_name: str,
        params: dict,
        rid: str,
        message_id: Optional[int],
        ip: Optional[str],
        user_agent: Optional[str],
    ) -> GatewayResult:
        try:
            result = handlers.execute(self.db, tool_name, params, current, bypass=True)
            status = "SUCCESS"
        except Exception as exc:  # noqa: BLE001
            result = {"error": str(exc)}
            status = "ERROR"
        self._persist_invocation(
            tool_name=tool_name,
            user_id=current.user.id,
            message_id=message_id,
            params=params,
            decision="ALLOW",
            reason_code="POLICIES_DISABLED",
            policy_id="LAB-OPEN",
            status=status,
        )
        self.audit.record_audit(
            request_id=rid,
            user_id=current.user.id,
            role=current.roles[0] if current.roles else None,
            action=tool_name,
            module="gateway",
            resource=meta.resource_type,
            resource_id=str(params.get("student_id") or ""),
            status=status,
            reason="POLICIES_DISABLED",
            new_value=params,
            ip=ip,
            user_agent=user_agent,
        )
        return GatewayResult(
            decision="ALLOW",
            reason_code="POLICIES_DISABLED",
            policy_id="LAB-OPEN",
            policy_version="lab",
            tool=tool_name,
            parameters=params,
            result=result,
            request_id=rid,
        )

    def _deny_if_role_or_permission_missing(
        self,
        *,
        current: CurrentUser,
        meta: ToolMeta,
        tool_name: str,
        params: dict,
        rid: str,
        message_id: Optional[int],
        ip: Optional[str],
        user_agent: Optional[str],
    ) -> Optional[GatewayResult]:
        roles = set(current.roles or [])
        if meta.allowed_roles and not (roles & set(meta.allowed_roles)):
            write = tool_name.startswith(("update_", "create_", "cancel_")) or meta.risk_level == "HIGH"
            return self._deny(
                current=current,
                tool_name=tool_name,
                params=params,
                reason="TOOL_NOT_ALLOWED" if write else "ROLE_NOT_ALLOWED",
                policy_id="POL-RBAC-001",
                rid=rid,
                message_id=message_id,
                ip=ip,
                user_agent=user_agent,
                security_type="TOOL_DENY" if write else "ACCESS_DENY",
            )
        return None

    def _lab_student(self) -> Optional[Student]:
        preferred = self.db.scalar(
            select(Student)
            .join(User, User.id == Student.user_id)
            .where(User.username == "student1", Student.deleted_at.is_(None))
        )
        if preferred:
            return preferred
        return self.db.scalar(
            select(Student)
            .where(Student.deleted_at.is_(None))
            .order_by(Student.id.asc())
        )

    def _lab_evaluation(self, student_id: int) -> Optional[Evaluation]:
        existing = self.db.scalar(
            select(Evaluation)
            .join(Course, Course.id == Evaluation.course_id)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == "ACTIVE",
            )
            .order_by(Evaluation.id.asc())
        )
        if existing:
            return existing
        return self._ensure_lab_evaluation(student_id)

    def _ensure_lab_evaluation(self, student_id: int) -> Optional[Evaluation]:
        """Lab A needs a real evaluation or update_grade fails as ERROR, not ALLOW."""
        enrollment = self.db.scalar(
            select(Enrollment)
            .join(Course, Course.id == Enrollment.course_id)
            .join(AcademicTerm, AcademicTerm.id == Course.term_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == "ACTIVE",
                AcademicTerm.status != "CLOSED",
            )
            .order_by(AcademicTerm.is_current.desc(), Enrollment.id.asc())
        )
        if enrollment is None:
            enrollment = self.db.scalar(
                select(Enrollment)
                .where(
                    Enrollment.student_id == student_id,
                    Enrollment.status == "ACTIVE",
                )
                .order_by(Enrollment.id.asc())
            )
        if enrollment is None:
            return None
        ev = Evaluation(
            course_id=enrollment.course_id,
            name="Lab A/B",
            weight_percent=Decimal("10.00"),
            status="ACTIVE",
        )
        self.db.add(ev)
        self.db.flush()
        return ev

    def _bind_open_scope(self, meta: ToolMeta, params: dict) -> dict:
        """When policies are off, do not stop on CURRENT_USER / missing student."""
        out = dict(params)
        needs_student = meta.tool_name in {
            "get_grades",
            "get_kardex",
            "get_attendance",
            "get_student_profile",
            "update_grade",
            "update_attendance",
        }
        if needs_student and out.get("student_id") in (None, "", "CURRENT_USER", "{{CURRENT_USER}}"):
            student = self._lab_student()
            if student:
                out["student_id"] = student.id
        if meta.tool_name == "update_grade":
            ev = None
            sid = out.get("student_id")
            try:
                if out.get("evaluation_id") is not None:
                    ev = self.db.get(Evaluation, int(out["evaluation_id"]))
            except (TypeError, ValueError):
                ev = None
            if ev is not None and sid not in (None, ""):
                enrolled = self.db.scalar(
                    select(Enrollment).where(
                        Enrollment.course_id == ev.course_id,
                        Enrollment.student_id == int(sid),
                        Enrollment.status == "ACTIVE",
                    )
                )
                if enrolled is None:
                    ev = None
            if ev is None and sid not in (None, ""):
                ev = self._lab_evaluation(int(sid))
                if ev:
                    out["evaluation_id"] = ev.id
        return out

    def _bind_current_user(
        self, current: CurrentUser, meta: ToolMeta, params: dict
    ) -> dict:
        out = dict(params)
        for key, val in list(out.items()):
            if val == "CURRENT_USER" or val == "{{CURRENT_USER}}":
                if key in ("student_id", "id") and meta.resource_type in (
                    "student",
                    "grade",
                    "attendance",
                    "kardex",
                ):
                    student = self.db.scalar(
                        select(Student).where(
                            Student.user_id == current.user.id,
                            Student.deleted_at.is_(None),
                        )
                    )
                    if student:
                        out[key] = student.id
                    elif "TEACHER" in current.roles or "ADMINISTRATOR" in current.roles:
                        out.pop(key, None)
                    else:
                        out[key] = None
                elif key == "teacher_id":
                    teacher = self.db.scalar(
                        select(Teacher).where(Teacher.user_id == current.user.id)
                    )
                    out[key] = teacher.id if teacher else current.user.id
                else:
                    out[key] = current.user.id
        # Auto-bind student tools when student_id omitted
        if (
            "student_id" not in out
            and meta.tool_name in ("get_grades", "get_kardex", "get_attendance", "get_student_profile")
            and "STUDENT" in current.roles
        ):
            student = self.db.scalar(
                select(Student).where(
                    Student.user_id == current.user.id,
                    Student.deleted_at.is_(None),
                )
            )
            if student:
                out["student_id"] = student.id
        return out

    def _check_ownership(
        self, current: CurrentUser, meta: ToolMeta, params: dict
    ) -> bool:
        """Return True if IDOR violation detected."""
        if "ADMINISTRATOR" in current.roles or "TEACHER" in current.roles:
            return False
        if "STUDENT" not in current.roles:
            return False
        sid = params.get("student_id")
        if sid is None:
            return False
        me = self.db.scalar(
            select(Student).where(
                Student.user_id == current.user.id,
                Student.deleted_at.is_(None),
            )
        )
        if me is None:
            return True
        return int(sid) != me.id

    def _build_context(
        self, current: CurrentUser, meta: ToolMeta, params: dict
    ) -> dict:
        ctx: dict[str, Any] = {
            "admin_bypass": "ADMINISTRATOR" in current.roles,
            "teaching_assignment_exists": False,
            "term_status": "ACTIVE",
            "resource_owned": True,
        }
        if meta.tool_name in ("update_grade", "update_attendance"):
            teacher = self.db.scalar(
                select(Teacher).where(Teacher.user_id == current.user.id)
            )
            course_id = params.get("course_id")
            if course_id is None and params.get("evaluation_id"):
                from app.models import Evaluation

                ev = self.db.get(Evaluation, int(params["evaluation_id"]))
                if ev:
                    course_id = ev.course_id
            if teacher and course_id:
                course = self.db.get(Course, int(course_id))
                if course:
                    ctx["teaching_assignment_exists"] = self.ops.teaching_assignment_exists(
                        teacher_id=teacher.id,
                        course_id=course.id,
                        term_id=course.term_id,
                    )
                    from app.models import AcademicTerm

                    term = self.db.get(AcademicTerm, course.term_id)
                    if term:
                        ctx["term_status"] = term.status
            elif "ADMINISTRATOR" in current.roles:
                ctx["teaching_assignment_exists"] = True
        return ctx

    def _deny(
        self,
        *,
        current: CurrentUser,
        tool_name: str,
        params: dict,
        reason: str,
        policy_id: str,
        rid: str,
        message_id: Optional[int],
        ip: Optional[str],
        user_agent: Optional[str],
        security_type: str,
        policy_version: str = "v1",
    ) -> GatewayResult:
        self._persist_invocation(
            tool_name=tool_name,
            user_id=current.user.id,
            message_id=message_id,
            params=params,
            decision="DENY",
            reason_code=reason,
            policy_id=policy_id,
            status="DENIED",
        )
        self.audit.record_audit(
            request_id=rid,
            user_id=current.user.id,
            role=current.roles[0] if current.roles else None,
            action=tool_name,
            module="gateway",
            resource=tool_name,
            status="DENIED",
            reason=reason,
            new_value=params,
            ip=ip,
            user_agent=user_agent,
        )
        self.audit.record_security(
            request_id=rid,
            user_id=current.user.id,
            event_type=security_type,
            severity="HIGH" if tool_name.startswith("update_") else "MED",
            details={"tool": tool_name, "reason": reason, "parameters": params},
        )
        # Ensure no grade mutation happened
        return GatewayResult(
            decision="DENY",
            reason_code=reason,
            policy_id=policy_id,
            policy_version=policy_version,
            tool=tool_name,
            parameters=params,
            result=None,
            request_id=rid,
        )

    def _persist_invocation(
        self,
        *,
        tool_name: str,
        user_id: int,
        message_id: Optional[int],
        params: dict,
        decision: str,
        reason_code: str,
        policy_id: str,
        status: str,
    ) -> None:
        entry = self.db.scalar(
            select(ToolRegistryEntry).where(ToolRegistryEntry.tool_name == tool_name)
        )
        inv = ToolInvocation(
            tool_id=entry.id if entry else None,
            tool_name=tool_name,
            user_id=user_id,
            message_id=message_id,
            parameters=json.dumps(params),
            decision=decision,
            reason_code=reason_code,
            policy_id=policy_id,
            status=status,
        )
        self.db.add(inv)
        self.db.commit()
