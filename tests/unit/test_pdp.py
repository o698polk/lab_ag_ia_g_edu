# Ref: BL-QA-002 | Skill: K-006 | Fase: F7
"""Direct PDP unit tests — Deny-by-Default branches."""

from __future__ import annotations

import pytest

from app.policy.pap import reset_pap
from app.policy.pdp import AuthzRequest, PDP, Subject


@pytest.fixture(autouse=True)
def _policies():
    reset_pap()
    yield
    reset_pap()


def _subj(roles, perms, status="ACTIVE", uid=1):
    return Subject(user_id=uid, roles=roles, permissions=perms, status=status)


@pytest.mark.unit
def test_pdp_user_inactive():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["TEACHER"], ["grades.update"], status="BLOCKED"),
            action="update_grade",
            context={},
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code == "USER_INACTIVE"


@pytest.mark.unit
def test_pdp_student_update_grade_tool_not_allowed():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["STUDENT"], ["grades.view", "ai.use"]),
            action="update_grade",
            context={},
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code in {"TOOL_NOT_ALLOWED", "ROLE_NOT_ALLOWED"}


@pytest.mark.unit
def test_pdp_teacher_update_grade_allow():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["TEACHER"], ["grades.update"]),
            action="update_grade",
            context={
                "teaching_assignment_exists": True,
                "term_status": "ACTIVE",
            },
        )
    )
    assert d.decision == "ALLOW"
    assert d.reason_code == "POLICY_MATCH"


@pytest.mark.unit
def test_pdp_teacher_without_assignment():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["TEACHER"], ["grades.update"]),
            action="update_grade",
            context={
                "teaching_assignment_exists": False,
                "term_status": "ACTIVE",
            },
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code == "CONTEXT_MISMATCH"


@pytest.mark.unit
def test_pdp_term_closed():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["TEACHER"], ["grades.update"]),
            action="update_grade",
            context={
                "teaching_assignment_exists": True,
                "term_status": "CLOSED",
            },
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code == "TERM_CLOSED"


@pytest.mark.unit
def test_pdp_permission_missing():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["TEACHER"], []),  # no grades.update
            action="update_grade",
            context={
                "teaching_assignment_exists": True,
                "term_status": "ACTIVE",
            },
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code in {"PERMISSION_MISSING", "TOOL_NOT_ALLOWED", "ROLE_NOT_ALLOWED"}


@pytest.mark.unit
def test_pdp_default_deny_unknown_action():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["ADMINISTRATOR"], ["users.view"]),
            action="unknown.explode",
            context={},
        )
    )
    assert d.decision == "DENY"
    assert d.reason_code == "DEFAULT_DENY"


@pytest.mark.unit
def test_pdp_get_grades_allow_student():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["STUDENT"], ["grades.view"]),
            action="get_grades",
            context={},
        )
    )
    assert d.decision == "ALLOW"


@pytest.mark.unit
def test_pdp_admin_bypass_assignment():
    d = PDP().evaluate(
        AuthzRequest(
            subject=_subj(["ADMINISTRATOR"], ["grades.update"]),
            action="update_grade",
            context={
                "admin_bypass": True,
                "teaching_assignment_exists": False,
                "term_status": "ACTIVE",
            },
        )
    )
    assert d.decision == "ALLOW"


@pytest.mark.unit
def test_pap_get_and_list():
    from app.policy.pap import get_pap

    pap = get_pap()
    assert len(pap.list()) >= 5
    g = pap.get("POL-GRADE-002")
    assert g is not None
    assert pap.get("POL-GRADE-002", "v1") is not None
    assert pap.get("POL-GRADE-002", "v9") is None
    assert pap.get("NO-SUCH") is None
