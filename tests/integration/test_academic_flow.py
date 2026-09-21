# Ref: BL-QA-002 | Skill: K-006 | Fase: F7
"""Integration: multi-module academic flow with AuthZ."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_full_academic_pipeline(client, auth_header, teacher_header, student_header):
    """Career → subject → term → course → assignment → enrollment → grade → kardex."""
    career = client.post(
        "/api/v1/careers",
        headers=auth_header,
        json={"code": "INT-SIS", "name": "Sistemas", "modality": "PRESENCIAL"},
    )
    assert career.status_code == 201, career.text

    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "INT101", "name": "Integracion", "credits": "4"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-INT",
            "name": "Integracion",
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
        json={"user_id": t_user["id"], "teacher_code": "DOC-INT"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={
            "user_id": s_user["id"],
            "student_code": "EST-INT",
            "career_id": career.json()["id"],
        },
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "A",
            "capacity": 25,
        },
    ).json()
    assert (
        client.post(
            "/api/v1/teaching-assignments",
            headers=auth_header,
            json={
                "teacher_id": teacher["id"],
                "course_id": course["id"],
                "term_id": term["id"],
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/enrollments",
            headers=auth_header,
            json={
                "student_id": student["id"],
                "course_id": course["id"],
                "term_id": term["id"],
            },
        ).status_code
        == 201
    )
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": course["id"],
            "name": "Parcial INT",
            "weight_percent": "100",
        },
    )
    assert ev.status_code == 201, ev.text
    grade = client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev.json()["id"],
            "student_id": student["id"],
            "score": "91",
        },
    )
    assert grade.status_code == 200
    mine = client.get("/api/v1/me/grades", headers=student_header)
    assert mine.status_code == 200
    assert float(mine.json()[0]["score"]) == 91.0

    kardex = client.put(
        "/api/v1/kardex",
        headers=auth_header,
        json={
            "student_id": student["id"],
            "term_id": term["id"],
            "subject_id": subject["id"],
            "course_id": course["id"],
            "final_grade": "91",
            "academic_status": "APPROVED",
            "credits": "4",
        },
    )
    assert kardex.status_code == 200, kardex.text
    my_k = client.get("/api/v1/me/kardex", headers=student_header)
    assert my_k.status_code == 200
    assert my_k.json()[0]["academic_status"] == "APPROVED"

    dash = client.get("/api/v1/dashboard", headers=auth_header)
    assert dash.status_code == 200
    assert dash.json()["indicators"]["students"] >= 1

    report = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "grades", "format": "JSON"},
    )
    assert report.status_code == 200
    assert report.json()["row_count"] >= 1


@pytest.mark.integration
def test_closed_term_blocks_enrollment(client, auth_header):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "CLS101", "name": "Closed", "credits": "2"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2025-CLS",
            "name": "Closed Term",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "status": "CLOSED",
            "is_current": False,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    s_user = next(u for u in users if u["username"] == "student1")
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": s_user["id"], "student_code": "EST-CLS"},
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "Z",
            "capacity": 10,
        },
    )
    # Creating course on CLOSED may itself be blocked depending on service rules
    if course.status_code == 201:
        enr = client.post(
            "/api/v1/enrollments",
            headers=auth_header,
            json={
                "student_id": student["id"],
                "course_id": course.json()["id"],
                "term_id": term["id"],
            },
        )
        assert enr.status_code in (403, 409)
        detail = enr.json().get("detail")
        if isinstance(detail, dict):
            assert detail.get("reason_code") in {"TERM_CLOSED", "CONTEXT_MISMATCH"}
    else:
        assert course.status_code in (403, 409)
