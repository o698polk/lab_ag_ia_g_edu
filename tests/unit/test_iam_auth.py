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
    assert res.json()["phase"].startswith("F8")
