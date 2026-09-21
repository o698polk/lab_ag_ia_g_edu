# Ref: BL-O1-008 / BL-O4-* | Skill: K-006 | Fase: F6
"""Pytest fixtures — SQLite in-memory."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long"
os.environ["PASSWORD_HASHER"] = "argon2"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

get_settings.cache_clear()

from app.db import session as db_session

db_session.reset_engine()

from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.auth.password import hash_password
from app.main import app
from app.models import Permission, Role, User

PERMISSIONS = [
    ("users.view", "users"),
    ("users.create", "users"),
    ("users.update", "users"),
    ("users.delete", "users"),
    ("roles.view", "roles"),
    ("permissions.view", "permissions"),
    ("permissions.assign", "permissions"),
    ("students.view", "students"),
    ("students.create", "students"),
    ("teachers.view", "teachers"),
    ("teachers.create", "teachers"),
    ("careers.view", "careers"),
    ("careers.create", "careers"),
    ("subjects.view", "subjects"),
    ("subjects.create", "subjects"),
    ("curriculum.view", "curriculum"),
    ("curriculum.create", "curriculum"),
    ("terms.view", "terms"),
    ("terms.create", "terms"),
    ("terms.update", "terms"),
    ("courses.view", "courses"),
    ("courses.create", "courses"),
    ("assignments.view", "assignments"),
    ("assignments.create", "assignments"),
    ("enrollments.view", "enrollments"),
    ("enrollments.create", "enrollments"),
    ("enrollments.cancel", "enrollments"),
    ("schedules.view", "schedules"),
    ("schedules.create", "schedules"),
    ("grades.view", "grades"),
    ("grades.update", "grades"),
    ("attendance.view", "attendance"),
    ("attendance.update", "attendance"),
    ("kardex.view", "kardex"),
    ("kardex.update", "kardex"),
    ("dashboard.view", "dashboard"),
    ("reports.view", "reports"),
    ("reports.generate", "reports"),
    ("reports.export", "reports"),
    ("notifications.view", "notifications"),
    ("notifications.create", "notifications"),
    ("history.view", "history"),
]


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        perm_map = {}
        for code, module in PERMISSIONS:
            p = Permission(code=code, description=code, module=module)
            db.add(p)
            db.flush()
            perm_map[code] = p

        admin_role = Role(code="ADMINISTRATOR", name="Administrator", is_active=True)
        admin_role.permissions = list(perm_map.values())
        teacher_role = Role(code="TEACHER", name="Teacher", is_active=True)
        teacher_role.permissions = [
            perm_map[c]
            for c in [
                "students.view",
                "grades.view",
                "grades.update",
                "attendance.view",
                "attendance.update",
                "dashboard.view",
                "reports.view",
                "reports.generate",
                "notifications.view",
                "history.view",
            ]
        ]
        student_role = Role(code="STUDENT", name="Student", is_active=True)
        student_role.permissions = [
            perm_map["grades.view"],
            perm_map["attendance.view"],
            perm_map["kardex.view"],
            perm_map["dashboard.view"],
            perm_map["notifications.view"],
            perm_map["history.view"],
        ]
        db.add_all([admin_role, teacher_role, student_role])

        admin = User(
            username="admin",
            email="admin@test.local",
            password_hash=hash_password("Admin123!"),
            status="ACTIVE",
        )
        admin.roles.append(admin_role)
        teacher = User(
            username="teacher1",
            email="teacher@test.local",
            password_hash=hash_password("Teacher123!"),
            status="ACTIVE",
        )
        teacher.roles.append(teacher_role)
        student = User(
            username="student1",
            email="student@test.local",
            password_hash=hash_password("Student123!"),
            status="ACTIVE",
        )
        student.roles.append(student_role)
        blocked = User(
            username="blocked",
            email="blocked@test.local",
            password_hash=hash_password("Blocked123!"),
            status="BLOCKED",
        )
        db.add_all([admin, teacher, student, blocked])
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def teacher_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher1", "password": "Teacher123!"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def student_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "student1", "password": "Student123!"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def auth_header(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def teacher_header(teacher_token: str) -> dict:
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def student_header(student_token: str) -> dict:
    return {"Authorization": f"Bearer {student_token}"}
