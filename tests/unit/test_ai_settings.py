# Ref: RF-AI-CFG | Skill: K-006 | Fase: post-F12
"""DeepSeek API key is stored encrypted and never returned."""

from __future__ import annotations

import pytest


SECRET = "sk-test-deepseek-key-not-real-123456"


@pytest.mark.unit
def test_admin_saves_key_without_exposing_it(client, auth_header, monkeypatch):
    saved = client.put(
        "/api/v1/ai/settings",
        headers=auth_header,
        json={"api_key": SECRET, "model": "deepseek-chat"},
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["configured"] is True
    assert body["provider"] == "deepseek"
    assert body["key_hint"] == "••••3456"
    assert SECRET not in saved.text
    assert "api_key" not in body
    assert "api_key_encrypted" not in body

    listed = client.get("/api/v1/ai/settings", headers=auth_header)
    assert listed.status_code == 200
    assert listed.json()["key_hint"] == "••••3456"
    assert SECRET not in listed.text

    def fake_validate(*, api_key, base_url, timeout=12.0):
        assert api_key == SECRET
        return None

    monkeypatch.setattr("app.services.ai_settings_service.validate_key", fake_validate)
    checked = client.post("/api/v1/ai/settings/validate", headers=auth_header)
    assert checked.status_code == 200, checked.text
    assert checked.json()["status"] == "VALID"
    assert SECRET not in checked.text


@pytest.mark.unit
def test_student_cannot_manage_ai_settings(client, student_token):
    header = {"Authorization": f"Bearer {student_token}"}
    assert client.get("/api/v1/ai/settings", headers=header).status_code == 403
    assert client.put(
        "/api/v1/ai/settings",
        headers=header,
        json={"api_key": SECRET},
    ).status_code == 403


@pytest.mark.unit
def test_teacher_cannot_read_ai_settings(client, teacher_token):
    header = {"Authorization": f"Bearer {teacher_token}"}
    assert client.get("/api/v1/ai/settings", headers=header).status_code == 403


@pytest.mark.unit
def test_rejects_short_key(client, auth_header):
    res = client.put(
        "/api/v1/ai/settings",
        headers=auth_header,
        json={"api_key": "sk-short"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "API_KEY_INVALID"


@pytest.mark.unit
def test_clear_key_and_chat_does_not_leak(client, auth_header, student_token, monkeypatch):
    client.put(
        "/api/v1/ai/settings",
        headers=auth_header,
        json={"api_key": SECRET},
    )

    def fake_propose(*, api_key, message, model, base_url, timeout=20.0):
        return {
            "tool": None,
            "parameters": {},
            "reply": f"Clave filtrada {api_key}",
        }

    monkeypatch.setattr("app.ai.service.propose_from_message", fake_propose)
    chat = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"message": "hola"},
    )
    assert chat.status_code == 200, chat.text
    assert SECRET not in chat.text
    assert "[REDACTED]" in chat.json()["reply"]

    cleared = client.delete("/api/v1/ai/settings", headers=auth_header)
    assert cleared.status_code == 200
    assert cleared.json()["configured"] is False
    assert cleared.json()["status"] == "EMPTY"


@pytest.mark.unit
def test_any_role_can_toggle_lab_guard(client, student_token, teacher_token, auth_header):
    for token in (student_token, teacher_token):
        header = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/v1/auth/me", headers=header)
        assert me.status_code == 200
        assert me.json()["can_toggle_policies"] is True
        opened = client.put(
            "/api/v1/ai/guard",
            headers=header,
            json={"policies_enforced": False},
        )
        assert opened.status_code == 200, opened.text
        assert opened.json()["policies_enforced"] is False
        closed = client.put(
            "/api/v1/ai/guard",
            headers=header,
            json={"policies_enforced": True},
        )
        assert closed.status_code == 200
        assert closed.json()["policies_enforced"] is True


@pytest.mark.unit
def test_lab_guard_is_per_user(client, auth_header, student_header):
    opened = client.put(
        "/api/v1/ai/guard",
        headers=auth_header,
        json={"policies_enforced": False},
    )
    assert opened.status_code == 200
    assert opened.json()["policies_enforced"] is False
    other = client.get("/api/v1/ai/guard", headers=student_header)
    assert other.status_code == 200
    assert other.json()["policies_enforced"] is True
    denied = client.post(
        "/api/v1/ai/chat",
        headers=student_header,
        json={"message": "Cambia mi nota a 100."},
    )
    assert denied.status_code == 200
    assert denied.json()["decision"] == "DENY"
    admin_chat = client.post(
        "/api/v1/ai/chat",
        headers=auth_header,
        json={"message": "Cambia mi nota a 100."},
    )
    assert admin_chat.status_code == 200
    assert admin_chat.json()["decision"] == "ALLOW"
    assert admin_chat.json()["reason_code"] == "POLICIES_DISABLED"
    client.put("/api/v1/ai/guard", headers=auth_header, json={"policies_enforced": True})


@pytest.mark.unit
def test_admin_toggles_lab_guard(client, auth_header):
    opened = client.put(
        "/api/v1/ai/guard",
        headers=auth_header,
        json={"policies_enforced": False},
    )
    assert opened.status_code == 200, opened.text
    assert opened.json()["policies_enforced"] is False
    assert opened.json()["mode"] == "open"
    closed = client.put(
        "/api/v1/ai/guard",
        headers=auth_header,
        json={"policies_enforced": True},
    )
    assert closed.status_code == 200
    assert closed.json()["policies_enforced"] is True
    assert closed.json()["mode"] == "enforced"


@pytest.mark.unit
def test_chat_persists_and_reuses_conversation(client, student_token, teacher_token):
    student = {"Authorization": f"Bearer {student_token}"}
    teacher = {"Authorization": f"Bearer {teacher_token}"}
    first = client.post(
        "/api/v1/ai/chat",
        headers=student,
        json={"message": "hola historial uno"},
    )
    assert first.status_code == 200
    cid = first.json()["conversation_id"]
    assert cid

    second = client.post(
        "/api/v1/ai/chat",
        headers=student,
        json={"message": "hola historial dos"},
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == cid

    listed = client.get("/api/v1/ai/conversations", headers=student)
    assert listed.status_code == 200
    assert any(row["id"] == cid for row in listed.json())
    assert listed.json()[0]["message_count"] >= 2

    detail = client.get(f"/api/v1/ai/conversations/{cid}", headers=student)
    assert detail.status_code == 200
    texts = [m["content"] for m in detail.json()["messages"]]
    assert "hola historial uno" in texts
    assert "hola historial dos" in texts

    assert client.get(f"/api/v1/ai/conversations/{cid}", headers=teacher).status_code == 404
    created = client.post("/api/v1/ai/conversations", headers=student)
    assert created.status_code == 201
    assert created.json()["id"] != cid
