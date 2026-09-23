# Ref: BL-O2-* | Skill: K-006 | Fase: F6
"""Catalog academic tests."""

import pytest


@pytest.mark.unit
def test_create_career_and_subject(client, auth_header):
    career = client.post(
        "/api/v1/careers",
        headers=auth_header,
        json={"code": "SIS", "name": "Sistemas", "duration_semesters": 8},
    )
    assert career.status_code == 201, career.text
    subject = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "MAT101", "name": "Matemáticas", "credits": "4.0", "hours": 64},
    )
    assert subject.status_code == 201, subject.text


@pytest.mark.unit
def test_curriculum_flow(client, auth_header):
    career_id = client.post(
        "/api/v1/careers",
        headers=auth_header,
        json={"code": "IND", "name": "Industrial"},
    ).json()["id"]
    subject_id = client.post(
        "/api/v1/subjects",
        headers=auth_header,
        json={"code": "FIS101", "name": "Física", "credits": "3"},
    ).json()["id"]
    cur = client.post(
        "/api/v1/curricula",
        headers=auth_header,
        json={"career_id": career_id, "version": "2026"},
    )
    assert cur.status_code == 201
    add = client.post(
        f"/api/v1/curricula/{cur.json()['id']}/subjects",
        headers=auth_header,
        json={"subject_id": subject_id, "level": 1, "semester": 1, "credits": "3"},
    )
    assert add.status_code == 201
    assert subject_id in add.json()["subject_ids"]


@pytest.mark.unit
def test_term_closed_not_writable(client, auth_header):
    term = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-1",
            "name": "Periodo 2026-1",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "status": "ACTIVE",
            "is_current": True,
        },
    )
    assert term.status_code == 201, term.text
    term_id = term.json()["id"]
    closed = client.patch(
        f"/api/v1/terms/{term_id}/status",
        headers=auth_header,
        json={"status": "CLOSED"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    writable = client.get(
        f"/api/v1/terms/{term_id}/writable",
        headers=auth_header,
    )
    assert writable.status_code == 409
    assert writable.json()["detail"]["reason_code"] == "TERM_CLOSED"


@pytest.mark.unit
def test_only_one_active_term(client, auth_header):
    first = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-A",
            "name": "Activo A",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
            "status": "ACTIVE",
        },
    )
    second = client.post(
        "/api/v1/terms",
        headers=auth_header,
        json={
            "code": "2026-B",
            "name": "Activo B",
            "start_date": "2026-06-01",
            "end_date": "2026-10-31",
            "status": "ACTIVE",
        },
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    terms = client.get("/api/v1/terms", headers=auth_header).json()
    active = [row for row in terms if row["status"] == "ACTIVE"]
    assert len(active) == 1
    assert active[0]["code"] == "2026-B"
    assert active[0]["is_current"] is True
    previous = next(row for row in terms if row["code"] == "2026-A")
    assert previous["status"] == "CLOSED"
    assert previous["is_current"] is False


@pytest.mark.unit
def test_student_profile(client, auth_header):
    # student1 user id from seed order: admin=1, student=2, blocked=3
    users = client.get("/api/v1/users", headers=auth_header).json()
    student_user = next(u for u in users if u["username"] == "student1")
    career_id = client.post(
        "/api/v1/careers",
        headers=auth_header,
        json={"code": "EDU", "name": "Educación"},
    ).json()["id"]
    res = client.post(
        "/api/v1/students",
        headers=auth_header,
        json={
            "user_id": student_user["id"],
            "student_code": "EST-001",
            "career_id": career_id,
            "level": "1",
        },
    )
    assert res.status_code == 201, res.text
    assert res.json()["student_code"] == "EST-001"


@pytest.mark.unit
def test_catalog_denied_for_student(client, student_token):
    res = client.get(
        "/api/v1/careers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 403
