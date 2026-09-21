# Ref: BL-QA-001 | Skill: K-006 | Fase: F5/F6
"""Health endpoint unit/smoke tests."""

import pytest


@pytest.mark.unit
def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "SIGA"
    assert "health" in body


@pytest.mark.unit
def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["phase"].startswith("F6")


@pytest.mark.unit
def test_ready(client):
    res = client.get("/api/v1/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
