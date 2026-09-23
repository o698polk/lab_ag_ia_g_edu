# Ref: BL-O5-* | Skill: K-006/K-007 | Fase: F6
"""Platform: dashboard, reports, notifications, user history."""

from __future__ import annotations

import json

import pytest


@pytest.mark.unit
def test_dashboard_by_role(client, auth_header, teacher_header, student_header):
    admin = client.get("/api/v1/dashboard", headers=auth_header)
    assert admin.status_code == 200, admin.text
    assert admin.json()["role_view"] == "ADMINISTRATOR"
    assert "students" in admin.json()["indicators"]

    teacher = client.get("/api/v1/dashboard", headers=teacher_header)
    assert teacher.status_code == 200
    assert teacher.json()["role_view"] == "TEACHER"

    student = client.get("/api/v1/dashboard", headers=student_header)
    assert student.status_code == 200
    assert student.json()["role_view"] == "STUDENT"
    assert "my_courses" in student.json()["indicators"]


@pytest.mark.unit
def test_generate_report_json_and_log(client, auth_header):
    catalog = client.get("/api/v1/reports/catalog", headers=auth_header)
    assert catalog.status_code == 200
    assert any(r["code"] == "students" for r in catalog.json())

    res = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "students", "format": "JSON"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["result_status"] == "SUCCESS"
    assert body["format"] == "JSON"
    assert isinstance(json.loads(body["content"]), list)

    logs = client.get("/api/v1/reports/logs", headers=auth_header)
    assert logs.status_code == 200
    assert any(l["id"] == body["log_id"] for l in logs.json())


@pytest.mark.unit
def test_report_csv_html_and_pdf(client, auth_header):
    csv_res = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "teachers", "format": "CSV"},
    )
    assert csv_res.status_code == 200
    assert "teacher_code" in csv_res.json()["content"] or csv_res.json()["row_count"] == 0

    html_res = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "career", "format": "HTML"},
    )
    assert html_res.status_code == 200
    assert "<html>" in html_res.json()["content"]

    pdf = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "grades", "format": "PDF"},
    )
    assert pdf.status_code == 200, pdf.text
    assert pdf.json()["format"] == "PDF"
    assert str(pdf.json()["content"]).startswith("%PDF")

    xlsx = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={"report_type": "students", "format": "XLSX"},
    )
    assert xlsx.status_code == 200, xlsx.text
    assert xlsx.json()["format"] == "XLSX"
    assert "Workbook" in xlsx.json()["content"] or "xml" in xlsx.json()["content"].lower()


@pytest.mark.unit
def test_student_cannot_generate_report(client, student_header):
    res = client.post(
        "/api/v1/reports",
        headers=student_header,
        json={"report_type": "students", "format": "JSON"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["reason_code"] == "PERMISSION_MISSING"


@pytest.mark.unit
def test_notifications_create_list_read_idor(client, auth_header, student_header):
    users = client.get("/api/v1/users", headers=auth_header).json()
    student = next(u for u in users if u["username"] == "student1")

    created = client.post(
        "/api/v1/notifications",
        headers=auth_header,
        json={
            "user_id": student["id"],
            "type": "ACADEMIC",
            "title": "Nueva calificacion",
            "body": "Se registro una nota",
        },
    )
    assert created.status_code == 201, created.text
    ntf_id = created.json()["id"]

    mine = client.get("/api/v1/notifications", headers=student_header)
    assert mine.status_code == 200
    assert any(n["id"] == ntf_id for n in mine.json())

    teacher_login = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher1", "password": "Teacher123!"},
    )
    th = {"Authorization": f"Bearer {teacher_login.json()['access_token']}"}
    deny = client.put(f"/api/v1/notifications/{ntf_id}/read", headers=th)
    assert deny.status_code == 403
    assert deny.json()["detail"]["reason_code"] == "RESOURCE_NOT_OWNED"

    read = client.put(f"/api/v1/notifications/{ntf_id}/read", headers=student_header)
    assert read.status_code == 200
    assert read.json()["read_flag"] is True


@pytest.mark.unit
def test_user_history_separated_and_idor(client, auth_header, student_header):
    client.get("/api/v1/dashboard", headers=student_header)
    hist = client.get("/api/v1/me/history", headers=student_header)
    assert hist.status_code == 200
    assert any(h["action"] == "dashboard.view" for h in hist.json())
    assert all(h["module"] != "audit" for h in hist.json())

    users = client.get("/api/v1/users", headers=auth_header).json()
    admin = next(u for u in users if u["username"] == "admin")
    idor = client.get(f"/api/v1/users/{admin['id']}/history", headers=student_header)
    assert idor.status_code == 403
    assert idor.json()["detail"]["reason_code"] == "RESOURCE_NOT_OWNED"

    ok = client.get(f"/api/v1/users/{admin['id']}/history", headers=auth_header)
    assert ok.status_code == 200
