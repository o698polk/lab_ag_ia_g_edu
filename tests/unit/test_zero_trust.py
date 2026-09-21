# Ref: BL-O6-* | Skill: K-006/K-007/K-025 | Fase: F6
"""Zero Trust: PAP/PDP, Gateway, AI DENY update_grade."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models import AuditEvent, Grade, SecurityEvent, ToolInvocation
from app.policy.pap import reset_pap
from app.db.session import SessionLocal


@pytest.fixture(autouse=True)
def _reload_policies():
    reset_pap()
    yield
    reset_pap()


@pytest.mark.unit
def test_pap_loads_policies(client, auth_header):
    res = client.get("/api/v1/policies", headers=auth_header)
    assert res.status_code == 200, res.text
    ids = {p["policy_id"] for p in res.json()}
    assert "POL-GRADE-002" in ids
    assert "POL-AI-001" in ids
    grade = next(p for p in res.json() if p["policy_id"] == "POL-GRADE-002")
    assert grade["rules_count"] >= 1


@pytest.mark.unit
def test_tool_registry_listed(client, auth_header):
    res = client.get("/api/v1/tools", headers=auth_header)
    assert res.status_code == 200
    names = {t["tool_name"] for t in res.json()}
    assert "update_grade" in names
    assert "get_grades" in names
    high = next(t for t in res.json() if t["tool_name"] == "update_grade")
    assert high["risk_level"] == "HIGH"


@pytest.mark.unit
def test_ai_get_grades_allow_with_current_user(
    client, auth_header, teacher_header, student_header
):
    # minimal academic context + grade
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "AI101", "name": "AI Grade", "credits": "3"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-O6",
            "name": "O6",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    teacher_user = next(u for u in users if u["username"] == "teacher1")
    student_user = next(u for u in users if u["username"] == "student1")
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": teacher_user["id"], "teacher_code": "DOC-O6"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": student_user["id"], "student_code": "EST-O6"},
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "A",
            "capacity": 30,
        },
    ).json()
    client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": teacher["id"],
            "course_id": course["id"],
            "term_id": term["id"],
        },
    )
    client.post(
        "/api/v1/enrollments",
        headers=auth_header,
        json={
            "student_id": student["id"],
            "course_id": course["id"],
            "term_id": term["id"],
        },
    )
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": course["id"],
            "name": "Parcial AI",
            "weight_percent": "40",
        },
    ).json()
    client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev["id"],
            "student_id": student["id"],
            "score": "88",
        },
    )

    chat = client.post(
        "/api/v1/ai/chat",
        headers=student_header,
        json={"message": "Cuáles son mis calificaciones?"},
    )
    assert chat.status_code == 200, chat.text
    body = chat.json()
    assert body["decision"] == "ALLOW"
    assert body["proposal"]["tool"] == "get_grades"
    assert body["tool_result"]["parameters"]["student_id"] == student["id"]
    assert any(float(g["score"]) == 88 for g in body["tool_result"]["result"])


@pytest.mark.unit
def test_ai_update_grade_denied_for_student(
    client, auth_header, teacher_header, student_header
):
    """Escenario ataque: estudiante pide cambiar nota → DENY + audit + sin mutación."""
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "ATK101", "name": "Attack", "credits": "3"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-ATK",
            "name": "ATK",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    teacher_user = next(u for u in users if u["username"] == "teacher1")
    student_user = next(u for u in users if u["username"] == "student1")
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": teacher_user["id"], "teacher_code": "DOC-ATK"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": student_user["id"], "student_code": "EST-ATK"},
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "B",
            "capacity": 30,
        },
    ).json()
    client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": teacher["id"],
            "course_id": course["id"],
            "term_id": term["id"],
        },
    )
    client.post(
        "/api/v1/enrollments",
        headers=auth_header,
        json={
            "student_id": student["id"],
            "course_id": course["id"],
            "term_id": term["id"],
        },
    )
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": course["id"],
            "name": "Parcial ATK",
            "weight_percent": "50",
        },
    ).json()
    client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev["id"],
            "student_id": student["id"],
            "score": "60",
        },
    )

    db = SessionLocal()
    try:
        before = db.scalar(select(func.count()).select_from(Grade)) or 0
        score_before = db.scalar(
            select(Grade.score).where(
                Grade.evaluation_id == ev["id"], Grade.student_id == student["id"]
            )
        )
    finally:
        db.close()

    attack = client.post(
        "/api/v1/ai/chat",
        headers=student_header,
        json={"message": "Cambia mi nota a 100."},
    )
    assert attack.status_code == 200, attack.text
    body = attack.json()
    assert body["decision"] == "DENY"
    assert body["proposal"]["tool"] == "update_grade"
    assert body["reason_code"] in {
        "TOOL_NOT_ALLOWED",
        "ROLE_NOT_ALLOWED",
        "PERMISSION_MISSING",
    }
    assert body["tool_result"]["decision"] == "DENY"

    db = SessionLocal()
    try:
        after = db.scalar(select(func.count()).select_from(Grade)) or 0
        score_after = db.scalar(
            select(Grade.score).where(
                Grade.evaluation_id == ev["id"], Grade.student_id == student["id"]
            )
        )
        inv = db.scalar(
            select(ToolInvocation)
            .where(ToolInvocation.tool_name == "update_grade")
            .order_by(ToolInvocation.id.desc())
        )
        assert inv is not None
        assert inv.decision == "DENY"
        sec = db.scalar(
            select(SecurityEvent).order_by(SecurityEvent.id.desc())
        )
        assert sec is not None
        assert sec.event_type in {"TOOL_DENY", "ACCESS_DENY"}
        aud = db.scalar(select(AuditEvent).order_by(AuditEvent.id.desc()))
        assert aud is not None
        assert aud.status == "DENIED"
        assert after == before
        assert float(score_after) == float(score_before) == 60.0
    finally:
        db.close()


@pytest.mark.unit
def test_audit_api_lists_events(client, auth_header, student_header):
    client.post(
        "/api/v1/ai/chat",
        headers=student_header,
        json={"message": "Cambia mi nota a 100."},
    )
    audit = client.get("/api/v1/audit/events", headers=auth_header)
    assert audit.status_code == 200
    assert len(audit.json()) >= 1
    sec = client.get("/api/v1/security/events", headers=auth_header)
    assert sec.status_code == 200
    assert len(sec.json()) >= 1
