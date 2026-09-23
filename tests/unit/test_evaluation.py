# Ref: BL-O4-* | Skill: K-006/K-007 | Fase: F6
"""Evaluation ABAC + anti-IDOR tests."""

from __future__ import annotations

import pytest


def _setup_grade_context(client, auth_header):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "GRD101", "name": "Grading", "credits": "3"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-O4",
            "name": "O4",
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
        json={"user_id": teacher_user["id"], "teacher_code": "DOC-O4"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": student_user["id"], "student_code": "EST-O4"},
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
    return {
        "subject": subject,
        "term": term,
        "teacher": teacher,
        "student": student,
        "course": course,
    }


@pytest.mark.unit
def test_admin_can_create_evaluation_without_teacher_profile(client, auth_header):
    base = _setup_grade_context(client, auth_header)
    ev = client.post(
        "/api/v1/evaluations",
        headers=auth_header,
        json={
            "course_id": base["course"]["id"],
            "name": "Admin Parcial",
            "weight_percent": 20,
        },
    )
    assert ev.status_code == 201, ev.text
    assert ev.json()["name"] == "Admin Parcial"

    kx = client.put(
        "/api/v1/kardex",
        headers=auth_header,
        json={
            "student_id": base["student"]["id"],
            "term_id": base["term"]["id"],
            "subject_id": base["subject"]["id"],
            "course_id": base["course"]["id"],
            "final_grade": 85,
            "academic_status": "IN_PROGRESS",
            "credits": 3,
        },
    )
    assert kx.status_code == 200, kx.text
    assert float(kx.json()["final_grade"]) == 85


@pytest.mark.unit
def test_teacher_can_grade_assigned_course(client, auth_header, teacher_header, student_header):
    base = _setup_grade_context(client, auth_header)
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": base["course"]["id"],
            "name": "Parcial 1",
            "weight_percent": "30",
        },
    )
    assert ev.status_code == 201, ev.text
    grade = client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev.json()["id"],
            "student_id": base["student"]["id"],
            "score": "85.5",
        },
    )
    assert grade.status_code == 200, grade.text
    mine = client.get("/api/v1/me/grades", headers=student_header)
    assert mine.status_code == 200
    assert float(mine.json()[0]["score"]) == 85.5


@pytest.mark.unit
def test_student_reads_own_grades_and_idor(client, auth_header, teacher_header, student_header):
    base = _setup_grade_context(client, auth_header)
    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={
            "course_id": base["course"]["id"],
            "name": "Parcial 1",
            "weight_percent": "20",
        },
    ).json()
    client.put(
        "/api/v1/grades",
        headers=teacher_header,
        json={
            "evaluation_id": ev["id"],
            "student_id": base["student"]["id"],
            "score": "90",
        },
    )
    mine = client.get("/api/v1/me/grades", headers=student_header)
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    # IDOR attempt — fabricate other student id
    idor = client.get("/api/v1/students/9999/grades", headers=student_header)
    assert idor.status_code == 403
    assert idor.json()["detail"]["reason_code"] == "RESOURCE_NOT_OWNED"


@pytest.mark.unit
def test_teacher_without_assignment_denied(client, auth_header, teacher_header):
    # course without assignment for teacher1
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "NOASN", "name": "NoAsn", "credits": "1"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "NOASN-T",
            "name": "T",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    teacher_user = next(u for u in users if u["username"] == "teacher1")
    client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": teacher_user["id"], "teacher_code": "DOC-NA"},
    )
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={"subject_id": subject["id"], "term_id": term["id"], "parallel_code": "A"},
    ).json()
    res = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={"course_id": course["id"], "name": "X", "weight_percent": "10"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["reason_code"] == "CONTEXT_MISMATCH"


@pytest.mark.unit
def test_attendance_and_kardex(client, auth_header, teacher_header, student_header):
    base = _setup_grade_context(client, auth_header)
    session = client.post(
        "/api/v1/attendance/sessions",
        headers=teacher_header,
        json={
            "course_id": base["course"]["id"],
            "session_date": "2026-03-01",
            "topic": "Intro",
        },
    )
    assert session.status_code == 201, session.text
    mark = client.put(
        "/api/v1/attendance/records",
        headers=teacher_header,
        json={
            "session_id": session.json()["id"],
            "student_id": base["student"]["id"],
            "status": "PRESENT",
        },
    )
    assert mark.status_code == 200, mark.text
    pct = client.get(
        f"/api/v1/attendance/courses/{base['course']['id']}/students/{base['student']['id']}/percent",
        headers=auth_header,
    )
    assert pct.status_code == 200
    assert pct.json()["percentage"] == 100.0

    kardex = client.put(
        "/api/v1/kardex",
        headers=auth_header,
        json={
            "student_id": base["student"]["id"],
            "term_id": base["term"]["id"],
            "subject_id": base["subject"]["id"],
            "course_id": base["course"]["id"],
            "final_grade": "88",
            "academic_status": "APPROVED",
            "credits": "3",
        },
    )
    assert kardex.status_code == 200, kardex.text
    my_k = client.get("/api/v1/me/kardex", headers=student_header)
    assert my_k.status_code == 200
    assert my_k.json()[0]["academic_status"] == "APPROVED"


@pytest.mark.unit
def test_course_hours_roster_attendance_bulk_and_gradebook(
    client, auth_header, teacher_header
):
    base = _setup_grade_context(client, auth_header)
    cid = base["course"]["id"]
    patched = client.patch(
        f"/api/v1/courses/{cid}",
        headers=auth_header,
        json={
            "hours_theory": 4,
            "hours_practical": 2,
            "hours_autonomous": 3,
            "teacher_id": base["teacher"]["id"],
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["hours_theory"] == 4
    assert patched.json()["hours_attendable"] == 6

    roster = client.get(f"/api/v1/courses/{cid}/roster", headers=auth_header)
    assert roster.status_code == 200
    assert any(r["student_id"] == base["student"]["id"] for r in roster.json())

    att = client.put(
        "/api/v1/attendance/bulk",
        headers=teacher_header,
        json={
            "course_id": cid,
            "session_date": "2026-09-22",
            "hour_slot": 1,
            "records": [
                {"student_id": base["student"]["id"], "status": "PRESENT"},
            ],
        },
    )
    assert att.status_code == 200, att.text
    assert att.json()["hour_slot"] == 1
    assert att.json()["students"][0]["present"] is True

    listed = client.get(
        "/api/v1/attendance/roster",
        headers=teacher_header,
        params={"course_id": cid, "session_date": "2026-09-22", "hour_slot": 1},
    )
    assert listed.status_code == 200
    assert listed.json()["hours_available"] == [1, 2, 3, 4, 5, 6]

    ev = client.post(
        "/api/v1/evaluations",
        headers=teacher_header,
        json={"course_id": cid, "name": "Acta 1", "weight_percent": 40},
    )
    assert ev.status_code == 201, ev.text
    book = client.get(
        f"/api/v1/courses/{cid}/gradebook",
        headers=teacher_header,
        params={"evaluation_id": ev.json()["id"]},
    )
    assert book.status_code == 200
    assert book.json()["students"][0]["student_id"] == base["student"]["id"]
    assert book.json()["students"][0]["attendance_pct"] == 100.0


@pytest.mark.unit
def test_course_grades_rules_and_integrity(client, auth_header, teacher_header, student_header):
    base = _setup_grade_context(client, auth_header)
    path = f"/api/v1/courses/{base['course']['id']}/final-grades"
    sid = base["student"]["id"]

    approved = client.put(
        path,
        headers=teacher_header,
        json={"items": [{"student_id": sid, "first_partial": "8.50", "second_partial": "9.00"}]},
    )
    assert approved.status_code == 200, approved.text
    row = approved.json()["students"][0]
    assert row["academic_status"] == "APROBADO"
    assert str(row["final_average"]) in ("8.75", "8.750")
    assert row["recovery_grade"] is None

    blocked = client.put(
        path,
        headers=teacher_header,
        json={
            "items": [
                {
                    "student_id": sid,
                    "first_partial": "8.50",
                    "second_partial": "9.00",
                    "recovery_grade": "9.00",
                }
            ]
        },
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "RECOVERY_NOT_ALLOWED"

    pending = client.put(
        path,
        headers=teacher_header,
        json={"items": [{"student_id": sid, "first_partial": "6.00", "second_partial": "6.50"}]},
    )
    assert pending.json()["students"][0]["academic_status"] == "SUPLETORIO PENDIENTE"

    recovered = client.put(
        path,
        headers=teacher_header,
        json={
            "items": [
                {
                    "student_id": sid,
                    "first_partial": "6.00",
                    "second_partial": "6.50",
                    "recovery_grade": "7.50",
                }
            ]
        },
    )
    rec = recovered.json()["students"][0]
    assert rec["academic_status"] == "APROBADO POR RECUPERACIÓN"
    assert str(rec["official_grade"]) in ("7.00", "7.0", "7.000")

    failed = client.put(
        path,
        headers=teacher_header,
        json={
            "items": [
                {
                    "student_id": sid,
                    "first_partial": "5.50",
                    "second_partial": "6.00",
                    "recovery_grade": "6.25",
                }
            ]
        },
    )
    assert failed.json()["students"][0]["academic_status"] == "REPROBADO"

    student_write = client.put(
        path,
        headers=student_header,
        json={"items": [{"student_id": sid, "first_partial": "10", "second_partial": "10"}]},
    )
    assert student_write.status_code == 403

    mine = client.get("/api/v1/me/academic", headers=student_header)
    assert mine.status_code == 200
    mine_row = next(r for r in mine.json() if r["course_id"] == base["course"]["id"])
    assert mine_row["academic_status"] == "REPROBADO"
    assert mine_row["first_partial"] is not None
