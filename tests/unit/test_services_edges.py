# Ref: BL-QA-002 | Skill: K-006 | Fase: F7
"""User/role service edge cases."""

from __future__ import annotations

import pytest

from app.auth.password import hash_password, verify_password


@pytest.mark.unit
def test_password_hash_verify_roundtrip():
    h = hash_password("Secret123!")
    assert verify_password("Secret123!", h)
    assert not verify_password("wrong", h)


@pytest.mark.unit
def test_user_service_create_update_status(client, auth_header):
    # API path covers service
    created = client.post(
        "/api/v1/users",
        headers=auth_header,
        json={
            "username": "edgeuser",
            "email": "edge@test.local",
            "password": "Edge1234!",
            "role_codes": ["STUDENT"],
        },
    )
    assert created.status_code == 201, created.text
    uid = created.json()["id"]
    upd = client.patch(
        f"/api/v1/users/{uid}/status",
        headers=auth_header,
        json={"status": "BLOCKED"},
    )
    # endpoint may be PUT or PATCH
    if upd.status_code == 405:
        upd = client.put(
            f"/api/v1/users/{uid}/status",
            headers=auth_header,
            json={"status": "BLOCKED"},
        )
    assert upd.status_code in (200, 204), upd.text
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "edgeuser", "password": "Edge1234!"},
    )
    assert login.status_code == 403


@pytest.mark.unit
def test_role_service_list_and_assign(client, auth_header):
    roles = client.get("/api/v1/roles", headers=auth_header)
    assert roles.status_code == 200
    assert len(roles.json()) >= 3
    perms = client.get("/api/v1/permissions", headers=auth_header)
    assert perms.status_code == 200
    codes = [p["code"] for p in perms.json()]
    assert "grades.view" in codes
    assigned = client.put(
        "/api/v1/roles/STUDENT/permissions",
        headers=auth_header,
        json={"permission_codes": ["grades.view", "attendance.view", "kardex.view", "ai.use", "dashboard.view", "notifications.view", "history.view", "students.view"]},
    )
    assert assigned.status_code == 200


@pytest.mark.unit
def test_change_password(client, auth_header):
    # create user
    client.post(
        "/api/v1/users",
        headers=auth_header,
        json={
            "username": "pwduser",
            "email": "pwd@test.local",
            "password": "OldPass123!",
            "role_codes": ["STUDENT"],
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "pwduser", "password": "OldPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
    )
    assert res.status_code == 204
    again = client.post(
        "/api/v1/auth/login",
        json={"username": "pwduser", "password": "NewPass123!"},
    )
    assert again.status_code == 200
