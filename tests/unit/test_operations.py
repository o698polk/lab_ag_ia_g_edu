# Ref: BL-O3-* | Skill: K-006 | Fase: F6
"""Operations tests: courses, assignments, enrollments, schedule conflicts."""

from __future__ import annotations

import pytest


def _setup_base(client, auth_header):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "PROG101", "name": "Programación", "credits": "4"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-O3",
            "name": "2026 O3",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    ).json()
    users = client.get("/api/v1/users", headers=auth_header).json()
    student_user = next(u for u in users if u["username"] == "student1")
    # create teacher user via admin create
    teacher_user = client.post(
        "/api/v1/users",
        headers=auth_header,
        json={
            "username": "teacher_o3",
            "email": "teacher_o3@test.local",
            "password": "Teacher123!",
            "role_codes": [],
        },
    ).json()
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": teacher_user["id"], "teacher_code": "DOC-O3", "specialty": "CS"},
    ).json()
    student = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={"user_id": student_user["id"], "student_code": "EST-O3"},
    ).json()
    course = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": subject["id"],
            "term_id": term["id"],
            "parallel_code": "A",
            "capacity": 2,
        },
    ).json()
    return {
        "subject": subject,
        "term": term,
        "teacher": teacher,
        "student": student,
        "course": course,
    }


@pytest.mark.unit
def test_course_assign_enroll_abac(client, auth_header):
    base = _setup_base(client, auth_header)
    asn = client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": base["teacher"]["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    assert asn.status_code == 201, asn.text

    abac = client.get(
        "/api/v1/abac/teaching-assignment",
        headers=auth_header,
        params={
            "teacher_id": base["teacher"]["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    assert abac.status_code == 200
    assert abac.json()["teaching_assignment_exists"] is True

    enr = client.post(
        "/api/v1/enrollments",
        headers=auth_header,
        json={
            "student_id": base["student"]["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    assert enr.status_code == 201, enr.text


@pytest.mark.unit
def test_schedule_teacher_conflict(client, auth_header):
    base = _setup_base(client, auth_header)
    client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": base["teacher"]["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    room = client.post(
        "/api/v1/classrooms",
        headers=auth_header,
        json={"code": "A101", "name": "Aula 101", "capacity": 40},
    ).json()
    room2 = client.post(
        "/api/v1/classrooms",
        headers=auth_header,
        json={"code": "A102", "name": "Aula 102", "capacity": 40},
    ).json()

    first = client.post(
        "/api/v1/schedules",
        headers=auth_header,
        json={
            "course_id": base["course"]["id"],
            "teacher_id": base["teacher"]["id"],
            "classroom_id": room["id"],
            "term_id": base["term"]["id"],
            "day_of_week": "MON",
            "start_time": "08:00:00",
            "end_time": "10:00:00",
        },
    )
    assert first.status_code == 201, first.text

    # second course same teacher overlapping
    course2 = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": base["subject"]["id"],
            "term_id": base["term"]["id"],
            "parallel_code": "B",
            "capacity": 20,
        },
    ).json()
    client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": base["teacher"]["id"],
            "course_id": course2["id"],
            "term_id": base["term"]["id"],
        },
    )
    conflict = client.post(
        "/api/v1/schedules",
        headers=auth_header,
        json={
            "course_id": course2["id"],
            "teacher_id": base["teacher"]["id"],
            "classroom_id": room2["id"],
            "term_id": base["term"]["id"],
            "day_of_week": "MON",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "TEACHER_BUSY"

    deleted = client.delete(
        f"/api/v1/schedules/{first.json()['id']}",
        headers=auth_header,
    )
    assert deleted.status_code == 204, deleted.text
    gone = client.delete(
        f"/api/v1/schedules/{first.json()['id']}",
        headers=auth_header,
    )
    assert gone.status_code == 404


@pytest.mark.unit
def test_closed_term_blocks_course(client, auth_header):
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "CLOSED1", "name": "X", "credits": "1"},
    ).json()
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "CLOSED-TERM",
            "name": "Closed",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "status": "ACTIVE",
        },
    ).json()
    client.patch(
        f"/api/v1/terms/{term['id']}/status",
        headers=auth_header,
        json={"status": "CLOSED"},
    )
    res = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={"subject_id": subject["id"], "term_id": term["id"], "parallel_code": "A"},
    )
    assert res.status_code == 409
    assert res.json()["detail"]["reason_code"] == "TERM_CLOSED"
