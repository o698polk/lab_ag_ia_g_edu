"""Impersonation: login-as and return-to-admin."""

from __future__ import annotations

import pytest


def _users(client, headers):
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200
    return {u["username"]: u for u in res.json()}


def _login_as(client, headers, user_id):
    return client.post(f"/api/v1/users/{user_id}/login-as", headers=headers)


@pytest.mark.unit
def test_login_as_see_as_target_and_return(client, auth_header):
    by_name = _users(client, auth_header)
    student = by_name["student1"]
    admin = by_name["admin"]

    entered = _login_as(client, auth_header, student["id"])
    assert entered.status_code == 200, entered.text
    tokens = entered.json()
    as_student = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = client.get("/api/v1/auth/me", headers=as_student)
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "student1"
    assert body["impersonating"] is True
    assert body["impersonator_id"] == admin["id"]
    assert body["impersonator_username"] == "admin"

    back = client.post(
        "/api/v1/auth/return-to-admin",
        headers=as_student,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert back.status_code == 200, back.text
    as_admin = {"Authorization": f"Bearer {back.json()['access_token']}"}
    restored = client.get("/api/v1/auth/me", headers=as_admin)
    assert restored.status_code == 200
    assert restored.json()["username"] == "admin"
    assert restored.json()["impersonating"] is False
    assert restored.json()["impersonator_id"] is None


@pytest.mark.unit
def test_return_to_admin_get_without_impersonated_permission(client, auth_header):
    by_name = _users(client, auth_header)
    entered = _login_as(client, auth_header, by_name["student1"]["id"])
    as_student = {"Authorization": f"Bearer {entered.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=as_student).json()
    assert "users.login-as" not in me["permissions"]

    back = client.get("/api/v1/auth/return-to-admin", headers=as_student)
    assert back.status_code == 200, back.text
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {back.json()['access_token']}"},
    ).json()["username"] == "admin"


@pytest.mark.unit
def test_cannot_impersonate_self(client, auth_header):
    admin = _users(client, auth_header)["admin"]
    res = _login_as(client, auth_header, admin["id"])
    assert res.status_code == 400
    assert res.json()["detail"] == "CANNOT_IMPERSONATE_SELF"


@pytest.mark.unit
def test_cannot_impersonate_protected_admin(client, auth_header):
    admin = _users(client, auth_header)["admin"]
    # Protected by username `admin` even if called by another path.
    res = _login_as(client, auth_header, admin["id"])
    assert res.status_code == 400
    assert res.json()["detail"] in {"CANNOT_IMPERSONATE_SELF", "CANNOT_IMPERSONATE_PROTECTED"}


@pytest.mark.unit
def test_login_as_forbidden_without_permission(client, student_header, auth_header):
    teacher = _users(client, auth_header)["teacher1"]
    res = _login_as(client, student_header, teacher["id"])
    assert res.status_code == 403


@pytest.mark.unit
def test_cannot_nest_impersonation(client, auth_header):
    by_name = _users(client, auth_header)
    entered = _login_as(client, auth_header, by_name["student1"]["id"])
    as_student = {"Authorization": f"Bearer {entered.json()['access_token']}"}
    nested = _login_as(client, as_student, by_name["teacher1"]["id"])
    assert nested.status_code in {400, 403}


@pytest.mark.unit
def test_refresh_keeps_impersonation(client, auth_header):
    student = _users(client, auth_header)["student1"]
    entered = _login_as(client, auth_header, student["id"])
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": entered.json()["refresh_token"]},
    )
    assert refreshed.status_code == 200
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert me.json()["username"] == "student1"
    assert me.json()["impersonating"] is True


@pytest.mark.unit
def test_impersonating_admin_can_toggle_lab_guard(client, auth_header):
    student = _users(client, auth_header)["student1"]
    entered = _login_as(client, auth_header, student["id"])
    as_student = {"Authorization": f"Bearer {entered.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=as_student).json()
    assert me["impersonating"] is True
    assert me["can_toggle_policies"] is True

    opened = client.put(
        "/api/v1/ai/guard",
        headers=as_student,
        json={"policies_enforced": False},
    )
    assert opened.status_code == 200, opened.text
    assert opened.json()["policies_enforced"] is False

    closed = client.put(
        "/api/v1/ai/guard",
        headers=as_student,
        json={"policies_enforced": True},
    )
    assert closed.status_code == 200
    assert closed.json()["policies_enforced"] is True


@pytest.mark.unit
def test_return_to_admin_without_session_claim(client, auth_header):
    res = client.post("/api/v1/auth/return-to-admin", headers=auth_header, json={})
    assert res.status_code == 400
    assert res.json()["detail"] == "NOT_IMPERSONATING"
