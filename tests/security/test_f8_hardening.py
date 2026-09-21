# Ref: F8 | Skill: K-007 | Fase: F8
"""F8 security: headers, JWT type, ABAC teacher, tampering, login failure audit."""

from __future__ import annotations

import jwt
import pytest

from app.core.config import get_settings


@pytest.mark.security
def test_security_headers_present(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "no-referrer"
    assert "no-store" in res.headers.get("Cache-Control", "")


@pytest.mark.security
def test_jwt_wrong_type_rejected(client):
    settings = get_settings()
    forged = jwt.encode(
        {
            "sub": "1",
            "type": "refresh",
            "exp": 9999999999,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert res.status_code == 401


@pytest.mark.security
def test_login_failure_creates_security_event(client, auth_header):
    bad = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "DefinitelyWrong!"},
    )
    assert bad.status_code == 401
    events = client.get("/api/v1/security/events", headers=auth_header)
    assert events.status_code == 200
    assert any(e["event_type"] == "LOGIN_FAILURE" for e in events.json())


@pytest.mark.security
def test_teacher_cannot_grade_unassigned_course(
    client, auth_header, teacher_header
):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "F8ABAC", "name": "ABAC", "credits": "3"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-F8A",
            "name": "F8A",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    t_user = next(u for u in users if u["username"] == "teacher1")
    s_user = next(u for u in users if u["username"] == "student1")
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": t_user["id"], "teacher_code": "DOC-F8A"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": s_user["id"], "student_code": "EST-F8A"},
    ).json()
    # Course WITHOUT teaching assignment for teacher1
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "X",
            "capacity": 10,
        },
    ).json()
    client.post(
        "/api/v1/enrollments",
        headers=auth_header,
        json={
            "student_id": student["id"],
            "course_id": course["id"],
            "term_id": term["id"],
        },
    )
    # Ensure teacher profile exists but no assignment
    _ = teacher
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": course["id"],
            "name": "Unauthorized",
            "weight_percent": "10",
        },
    )
    assert ev.status_code == 403
    assert ev.json()["detail"]["reason_code"] == "CONTEXT_MISMATCH"


@pytest.mark.security
def test_parameter_tampering_score_out_of_range(
    client, auth_header, teacher_header
):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "F8TAM", "name": "Tamper", "credits": "3"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-F8T",
            "name": "F8T",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    t_user = next(u for u in users if u["username"] == "teacher1")
    s_user = next(u for u in users if u["username"] == "student1")
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": t_user["id"], "teacher_code": "DOC-F8T"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": s_user["id"], "student_code": "EST-F8T"},
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "T",
            "capacity": 10,
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
        json={"course_id": course["id"], "name": "P", "weight_percent": "20"},
    ).json()
    bad = client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev["id"],
            "student_id": student["id"],
            "score": "150",
        },
    )
    assert bad.status_code == 422


@pytest.mark.security
def test_opaque_refresh_as_bearer_rejected(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login['refresh_token']}"},
    )
    assert res.status_code == 401
