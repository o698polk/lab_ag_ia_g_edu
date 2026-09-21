# Ref: BL-O6-002 | Skill: K-020 | Fase: F6 | ADR-005
"""PDP — Policy Decision Point (ALLOW/DENY only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.policy.pap import PAP, PolicyDocument, PolicyRule, get_pap


@dataclass
class Decision:
    decision: str  # ALLOW | DENY
    reason_code: str
    policy_id: str
    policy_version: str


@dataclass
class Subject:
    user_id: int
    roles: list[str]
    permissions: list[str]
    status: str = "ACTIVE"


@dataclass
class AuthzRequest:
    subject: Subject
    action: str
    resource: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


class PDP:
    """Deny-by-Default evaluator. Never returns soft allow."""

    def __init__(self, pap: Optional[PAP] = None) -> None:
        self.pap = pap or get_pap()

    def evaluate(self, req: AuthzRequest) -> Decision:
        if req.subject.status != "ACTIVE":
            return Decision("DENY", "USER_INACTIVE", "POL-AUTH-001", "v1")

        matching: list[tuple[PolicyDocument, PolicyRule]] = []
        for policy in self.pap.list():
            for rule in policy.rules:
                if req.action in rule.actions:
                    matching.append((policy, rule))

        # Explicit DENY rules first (e.g. STUDENT cannot update_grade via AI)
        for policy, rule in matching:
            if rule.effect != "DENY":
                continue
            if rule.roles and not self._roles_ok(req.subject.roles, rule.roles):
                continue
            return Decision(
                "DENY",
                "TOOL_NOT_ALLOWED" if req.action.startswith(("update_", "create_", "cancel_")) else "ROLE_NOT_ALLOWED",
                policy.policy_id,
                policy.version,
            )

        # ALLOW rules
        last_fail: Optional[tuple[str, PolicyDocument]] = None
        for policy, rule in matching:
            if rule.effect != "ALLOW":
                continue
            deny_reason = self._rule_fail_reason(req, rule)
            if deny_reason is None:
                return Decision("ALLOW", "POLICY_MATCH", policy.policy_id, policy.version)
            last_fail = (deny_reason, policy)

        if last_fail:
            return Decision(
                "DENY",
                last_fail[0],
                last_fail[1].policy_id,
                last_fail[1].version,
            )

        return Decision("DENY", "DEFAULT_DENY", "NONE", "v1")

    def _roles_ok(self, subject_roles: list[str], allowed: list[str]) -> bool:
        return bool(set(subject_roles) & set(allowed))

    def _rule_fail_reason(self, req: AuthzRequest, rule: PolicyRule) -> Optional[str]:
        if rule.roles and not self._roles_ok(req.subject.roles, rule.roles):
            return "ROLE_NOT_ALLOWED"
        if rule.permissions:
            if not set(rule.permissions).issubset(set(req.subject.permissions)):
                return "PERMISSION_MISSING"
        for cond in rule.conditions:
            reason = self._eval_condition(cond, req)
            if reason:
                return reason
        return None

    def _eval_condition(self, cond: str, req: AuthzRequest) -> Optional[str]:
        c = cond.strip()
        ctx = req.context
        if c == "user.status == ACTIVE":
            if req.subject.status != "ACTIVE":
                return "USER_INACTIVE"
            return None
        if c == "teaching_assignment.exists":
            # ADMINISTRATOR may bypass assignment in gateway context flag
            if ctx.get("admin_bypass"):
                return None
            if not ctx.get("teaching_assignment_exists", False):
                return "CONTEXT_MISMATCH"
            return None
        if c == "term.status == ACTIVE":
            status = ctx.get("term_status", "ACTIVE")
            if status == "CLOSED":
                return "TERM_CLOSED"
            if status not in ("ACTIVE", None):
                # PLANNED etc. still block writes
                if status != "ACTIVE":
                    return "TERM_CLOSED"
            return None
        if c == "resource.owned":
            if not ctx.get("resource_owned", False):
                return "RESOURCE_NOT_OWNED"
            return None
        return None
