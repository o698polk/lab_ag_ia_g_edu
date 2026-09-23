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
            "cedula": "0991112223",
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


@pytest.mark.unit
def test_teacher_scoped_courses_and_final_grades(client, auth_header, teacher_token, student_token):
    base = _setup_base(client, auth_header)
    users = client.get("/api/v1/users", headers=auth_header).json()
    teacher1 = next(u for u in users if u["username"] == "teacher1")
    teacher = client.post(
        "/api/v1/teachers",
        headers=auth_header,
        json={"user_id": teacher1["id"], "teacher_code": "DOC-T1", "specialty": "CS"},
    )
    if teacher.status_code != 201:
        teachers = client.get("/api/v1/teachers", headers=auth_header).json()
        teacher = next(t for t in teachers if t.get("user_id") == teacher1["id"])
    else:
        teacher = teacher.json()
    assigned = client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": teacher["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    assert assigned.status_code in (200, 201), assigned.text
    client.post(
        "/api/v1/enrollments",
        headers=auth_header,
        json={
            "student_id": base["student"]["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    teacher_courses = client.get(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_courses.status_code == 200
    assigned_courses = teacher_courses.json()
    ids = [c["id"] for c in assigned_courses]
    assert base["course"]["id"] in ids
    mine = next(c for c in assigned_courses if c["id"] == base["course"]["id"])
    assert mine.get("subject_name") == "Programación"
    assert mine.get("course_name") == "A"

    other = client.post(
        "/api/v1/courses",
        headers=auth_header,
        json={
            "subject_id": base["subject"]["id"],
            "term_id": base["term"]["id"],
            "parallel_code": "B",
            "capacity": 10,
        },
    ).json()
    teacher_courses = client.get(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {teacher_token}"},
    ).json()
    assert other["id"] not in [c["id"] for c in teacher_courses]

    finals = client.put(
        f"/api/v1/courses/{base['course']['id']}/final-grades",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "items": [
                {
                    "student_id": base["student"]["id"],
                    "first_partial": "8.50",
                    "second_partial": "9.00",
                }
            ]
        },
    )
    assert finals.status_code == 200, finals.text
    row = finals.json()["students"][0]
    assert str(row["final_average"]) in ("8.75", "8.750")
    assert row["academic_status"] == "APROBADO"
    assert row["recovery_grade"] is None
    assert row["recovery_allowed"] is False
    assert row["name"]

    denied = client.put(
        f"/api/v1/courses/{other['id']}/final-grades",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "items": [
                {
                    "student_id": base["student"]["id"],
                    "first_partial": "9.00",
                    "second_partial": "9.00",
                }
            ]
        },
    )
    assert denied.status_code == 403

    mine = client.get(
        "/api/v1/me/academic",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert mine.status_code == 200, mine.text
    subjects = [r["subject_name"] for r in mine.json()]
    assert "Programación" in subjects
    assert mine.json()[0]["final_grade"] is not None


@pytest.mark.unit
def test_teacher_sees_only_active_term_courses(client, auth_header, teacher_token):
    base = _setup_base(client, auth_header)
    users = client.get("/api/v1/users", headers=auth_header).json()
    teacher1 = next(u for u in users if u["username"] == "teacher1")
    teachers = client.get("/api/v1/teachers", headers=auth_header).json()
    teacher = next((t for t in teachers if t.get("user_id") == teacher1["id"]), None)
    if teacher is None:
        teacher = client.post(
            "/api/v1/teachers",
            headers=auth_header,
            json={"user_id": teacher1["id"], "teacher_code": "DOC-T1", "specialty": "CS"},
        ).json()
    planned = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2027-P",
            "name": "Planificado",
            "start_date": "2027-01-01",
            "end_date": "2027-05-31",
            "status": "PLANNED",
        },
    ).json()
    closed = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2025-C",
            "name": "Cerrado",
            "start_date": "2025-01-01",
            "end_date": "2025-05-31",
            "status": "CLOSED",
        },
    ).json()
    extra = []
    for term, parallel in ((planned, "P"), (closed, "C")):
        course = client.post(
            "/api/v1/courses",
            headers=auth_header,
            json={
                "subject_id": base["subject"]["id"],
                "term_id": term["id"],
                "parallel_code": parallel,
                "capacity": 20,
            },
        )
        assert course.status_code == 201, course.text
        extra.append(course.json())
        assigned = client.post(
            "/api/v1/teaching-assignments",
            headers=auth_header,
            json={
                "teacher_id": teacher["id"],
                "course_id": extra[-1]["id"],
                "term_id": term["id"],
            },
        )
        assert assigned.status_code in (200, 201), assigned.text
    client.post(
        "/api/v1/teaching-assignments",
        headers=auth_header,
        json={
            "teacher_id": teacher["id"],
            "course_id": base["course"]["id"],
            "term_id": base["term"]["id"],
        },
    )
    visible = client.get(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert visible.status_code == 200
    ids = [row["id"] for row in visible.json()]
    assert base["course"]["id"] in ids
    assert extra[0]["id"] not in ids
    assert extra[1]["id"] not in ids
    assert all(row.get("term_name") == base["term"]["name"] for row in visible.json())
