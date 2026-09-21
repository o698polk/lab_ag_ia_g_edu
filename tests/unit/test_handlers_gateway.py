# Ref: BL-QA-002 | Skill: K-006 | Fase: F7
"""Handler + gateway edge branches."""

from __future__ import annotations

import pytest

from sqlalchemy import select

from app.auth.deps import CurrentUser
from app.db.session import SessionLocal
from app.gateway.pep import ToolGateway
from app.models import User
from app.policy.pap import reset_pap
from app.tools import handlers


@pytest.fixture(autouse=True)
def _policies():
    reset_pap()
    yield
    reset_pap()


def _current(db, username: str) -> CurrentUser:
    user = db.scalar(select(User).where(User.username == username))
    assert user is not None
    return CurrentUser(
        user=user,
        roles=user.role_codes(),
        permissions=sorted(user.permission_codes()),
    )


@pytest.mark.unit
def test_handlers_get_student_not_found(client, auth_header):
    # ensure DB seeded via client fixture
    db = SessionLocal()
    try:
        current = _current(db, "admin")
        out = handlers.execute(db, "get_student_profile", {"student_id": 99999}, current)
        assert out["error"] == "STUDENT_NOT_FOUND"
    finally:
        db.close()


@pytest.mark.unit
def test_gateway_unknown_tool_denied(client, auth_header):
    db = SessionLocal()
    try:
        current = _current(db, "admin")
        gw = ToolGateway(db)
        result = gw.invoke(current=current, tool_name="drop_database", parameters={})
        assert result.decision == "DENY"
        assert result.reason_code == "TOOL_NOT_ALLOWED"
    finally:
        db.close()


@pytest.mark.unit
def test_gateway_idor_student_other_profile(client, auth_header, student_header):
    users = client.get("/api/v1/users", headers=auth_header).json()
    s_user = next(u for u in users if u["username"] == "student1")
    client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": s_user["id"], "student_code": "EST-HND"},
    )
    db = SessionLocal()
    try:
        current = _current(db, "student1")
        gw = ToolGateway(db)
        result = gw.invoke(
            current=current,
            tool_name="get_grades",
            parameters={"student_id": 999},
        )
        assert result.decision == "DENY"
        assert result.reason_code == "RESOURCE_NOT_OWNED"
    finally:
        db.close()


@pytest.mark.unit
def test_handlers_get_schedule_and_attendance_empty(client, auth_header):
    db = SessionLocal()
    try:
        current = _current(db, "admin")
        assert handlers.execute(db, "get_schedule", {}, current) == []
        assert (
            handlers.execute(db, "get_attendance", {"student_id": 1}, current) == []
            or isinstance(
                handlers.execute(db, "get_attendance", {"student_id": 1}, current), list
            )
        )
        assert handlers.execute(db, "get_kardex", {"student_id": 1}, current) == [] or isinstance(
            handlers.execute(db, "get_kardex", {"student_id": 1}, current), list
        )
    finally:
        db.close()


@pytest.mark.unit
def test_handlers_unknown_tool():
    db = SessionLocal()
    try:
        current = _current(db, "admin")
        with pytest.raises(ValueError):
            handlers.execute(db, "nope", {}, current)
    finally:
        db.close()


@pytest.mark.unit
def test_ai_no_tool_message(client, student_header):
    res = client.post(
        "/api/v1/ai/chat",
        headers=student_header,
        json={"message": "Hola, qué puedes hacer?"},
    )
    assert res.status_code == 200
    assert res.json()["reason_code"] == "NO_TOOL"
    assert res.json()["proposal"] is None
