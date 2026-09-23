# Ref: BL-O1-008 | Skill: K-006 | Fase: F6
"""IAM auth and Deny-by-Default tests."""

import pytest


@pytest.mark.unit
def test_login_success(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.unit
def test_user_patch_and_permission_crud(client, auth_header):
    users = client.get("/api/v1/users", headers=auth_header)
    assert users.status_code == 200
    admin = next(u for u in users.json() if u["username"] == "admin")
    patched = client.patch(
        f"/api/v1/users/{admin['id']}",
        headers=auth_header,
        json={"first_name": "Ada", "last_name": "Lovelace", "phone": "099000111"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["first_name"] == "Ada"
    assert patched.json()["id"] == admin["id"]

    created = client.post(
        "/api/v1/permissions",
        headers=auth_header,
        json={"code": "demo.view", "module": "demo", "description": "Ver demo"},
    )
    assert created.status_code == 201, created.text
    pid = created.json()["id"]
    upd = client.patch(
        f"/api/v1/permissions/{pid}",
        headers=auth_header,
        json={"description": "Ver demo actualizado"},
    )
    assert upd.status_code == 200
    assert upd.json()["description"] == "Ver demo actualizado"

    role = client.post(
        "/api/v1/roles",
        headers=auth_header,
        json={"code": "COORD", "name": "Coordinador", "description": "Coordina"},
    )
    assert role.status_code == 201, role.text
    meta = client.patch(
        "/api/v1/roles/COORD",
        headers=auth_header,
        json={"description": "Coordinación académica"},
    )
    assert meta.status_code == 200
    assert meta.json()["description"] == "Coordinación académica"


@pytest.mark.unit
def test_login_invalid(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert res.status_code == 401


@pytest.mark.unit
def test_login_blocked(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "blocked", "password": "Blocked123!"},
    )
    assert res.status_code == 403


@pytest.mark.unit
def test_me(client, admin_token):
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["username"] == "admin"
    assert "ADMINISTRATOR" in res.json()["roles"]


@pytest.mark.unit
def test_users_list_admin_allowed(client, admin_token):
    res = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert len(res.json()) >= 2


@pytest.mark.unit
def test_users_list_student_denied(client, student_token):
    res = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["decision"] == "DENY"
    assert detail["reason_code"] == "PERMISSION_MISSING"


@pytest.mark.unit
def test_refresh_and_logout(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()
    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refresh.status_code == 200
    new_refresh = refresh.json()["refresh_token"]
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 204
    again = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert again.status_code == 401


@pytest.mark.unit
def test_health_phase(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["phase"].startswith("F12")


@pytest.mark.unit
def test_forgot_and_reset_password(client):
    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={"username": "student1"},
    )
    assert forgot.status_code == 200
    body = forgot.json()
    assert body["accepted"] is True
    assert body["reset_token"]

    unknown = client.post(
        "/api/v1/auth/forgot-password",
        json={"username": "nobody-here"},
    )
    assert unknown.status_code == 200
    assert unknown.json()["accepted"] is True
    assert unknown.json()["reset_token"] is None

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": body["reset_token"], "new_password": "Student999!"},
    )
    assert reset.status_code == 204

    old = client.post(
        "/api/v1/auth/login",
        json={"username": "student1", "password": "Student123!"},
    )
    assert old.status_code == 401
    new = client.post(
        "/api/v1/auth/login",
        json={"username": "student1", "password": "Student999!"},
    )
    assert new.status_code == 200


@pytest.mark.unit
def test_admin_set_password(client, auth_header):
    users = client.get("/api/v1/users", headers=auth_header).json()
    student = next(u for u in users if u["username"] == "student1")
    res = client.post(
        f"/api/v1/users/{student['id']}/password",
        headers=auth_header,
        json={"new_password": "ResetByAdmin1!"},
    )
    assert res.status_code == 204
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "student1", "password": "ResetByAdmin1!"},
    )
    assert login.status_code == 200


@pytest.mark.unit
def test_role_create_and_protected_delete(client, auth_header, student_header):
    created = client.post(
        "/api/v1/roles",
        headers=auth_header,
        json={"code": "auditor", "name": "Auditor lab"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["code"] == "AUDITOR"
    assert created.json()["is_active"] is True

    denied = client.post(
        "/api/v1/roles",
        headers=student_header,
        json={"code": "hacker", "name": "No"},
    )
    assert denied.status_code == 403

    protected = client.delete("/api/v1/roles/ADMINISTRATOR", headers=auth_header)
    assert protected.status_code == 400
    assert protected.json()["detail"] == "ROLE_PROTECTED"

    gone = client.delete("/api/v1/roles/AUDITOR", headers=auth_header)
    assert gone.status_code == 200
    assert gone.json()["is_active"] is False
