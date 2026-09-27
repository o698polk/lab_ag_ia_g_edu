"""Agent CRUD / filters across SIGA modules."""

from __future__ import annotations

import pytest
from app.policy.pap import reset_pap


@pytest.fixture(autouse=True)
def _reload_policies():
    reset_pap()
    yield
    reset_pap()


def _chat(client, header, message: str):
    res = client.post("/api/v1/ai/chat", headers=header, json={"message": message})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.unit
def test_admin_lists_and_filters_users(client, auth_header):
    listed = _chat(client, auth_header, "Lista los usuarios activos")
    assert listed["decision"] == "ALLOW"
    assert listed["proposal"]["tool"] == "list_users"
    rows = listed["tool_result"]["result"]
    assert isinstance(rows, list)
    assert any(r.get("username") == "admin" for r in rows)


@pytest.mark.unit
def test_student_cannot_list_users(client, student_header):
    denied = _chat(client, student_header, "Lista los usuarios")
    assert denied["decision"] == "DENY"
    assert denied["proposal"]["tool"] == "list_users"
    assert denied["reason_code"] in {"ROLE_NOT_ALLOWED", "TOOL_NOT_ALLOWED"}


@pytest.mark.unit
def test_student_can_list_own_scope_courses(client, student_header):
    opened = _chat(client, student_header, "Lista los cursos")
    assert opened["decision"] == "ALLOW"
    assert opened["proposal"]["tool"] == "list_courses"


@pytest.mark.unit
def test_admin_creates_and_filters_subject(client, auth_header):
    created = _chat(client, auth_header, "Crea la asignatura LABCRUD")
    assert created["decision"] == "ALLOW"
    assert created["proposal"]["tool"] == "create_subject"
    result = created["tool_result"]["result"]
    assert result.get("error") is None
    assert result.get("code") == "LABCRUD"
    listed = _chat(client, auth_header, "Lista las asignaturas y busca LABCRUD")
    assert listed["decision"] == "ALLOW"
    assert listed["proposal"]["tool"] == "list_subjects"
    rows = listed["tool_result"]["result"]
    assert any(r.get("code") == "LABCRUD" for r in rows)


@pytest.mark.unit
def test_teacher_lists_students_but_cannot_create_user(client, teacher_header):
    listed = _chat(client, teacher_header, "Lista los estudiantes")
    assert listed["decision"] == "ALLOW"
    assert listed["proposal"]["tool"] == "list_students"
    denied = _chat(client, teacher_header, "Crea un usuario nuevo")
    assert denied["decision"] == "DENY"
    assert denied["proposal"]["tool"] == "create_user"


@pytest.mark.unit
def test_general_question_does_not_run_module_tools(client, auth_header):
    asked = _chat(client, auth_header, "Como desarrollar un juego en python de pacman")
    tool = (asked.get("proposal") or {}).get("tool")
    assert tool is None
    assert asked["reason_code"] in {"NO_TOOL", "AI_UNAVAILABLE"}
    assert "Administrator" not in (asked.get("reply") or "")
    assert "registro(s)" not in (asked.get("reply") or "")


@pytest.mark.unit
def test_admin_dashboard_and_careers(client, auth_header):
    dash = _chat(client, auth_header, "Muéstrame el dashboard")
    assert dash["decision"] == "ALLOW"
    assert dash["proposal"]["tool"] == "get_dashboard"
    careers = _chat(client, auth_header, "Lista las carreras")
    assert careers["decision"] == "ALLOW"
    assert careers["proposal"]["tool"] == "list_careers"
