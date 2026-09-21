# Ref: BL-O1-007 | Skill: K-024 | Fase: F6
"""Seed IAM: roles ADMINISTRATOR/TEACHER/STUDENT + permissions + admin user."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from sqlalchemy import select

from app.auth.password import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Permission, Role, User

PERMISSIONS = [
    ("users.view", "View users", "users"),
    ("users.create", "Create users", "users"),
    ("users.update", "Update users", "users"),
    ("users.delete", "Delete users", "users"),
    ("roles.view", "View roles", "roles"),
    ("roles.create", "Create roles", "roles"),
    ("roles.update", "Update roles", "roles"),
    ("roles.delete", "Delete roles", "roles"),
    ("permissions.view", "View permissions", "permissions"),
    ("permissions.assign", "Assign permissions", "permissions"),
    ("students.view", "View students", "students"),
    ("students.create", "Create students", "students"),
    ("students.update", "Update students", "students"),
    ("teachers.view", "View teachers", "teachers"),
    ("teachers.create", "Create teachers", "teachers"),
    ("teachers.update", "Update teachers", "teachers"),
    ("careers.view", "View careers", "careers"),
    ("careers.create", "Create careers", "careers"),
    ("careers.update", "Update careers", "careers"),
    ("subjects.view", "View subjects", "subjects"),
    ("subjects.create", "Create subjects", "subjects"),
    ("subjects.update", "Update subjects", "subjects"),
    ("curriculum.view", "View curriculum", "curriculum"),
    ("curriculum.create", "Create curriculum", "curriculum"),
    ("terms.view", "View terms", "terms"),
    ("terms.create", "Create terms", "terms"),
    ("terms.update", "Update terms", "terms"),
    ("courses.view", "View courses", "courses"),
    ("courses.create", "Create courses", "courses"),
    ("courses.update", "Update courses", "courses"),
    ("assignments.view", "View teaching assignments", "assignments"),
    ("assignments.create", "Create teaching assignments", "assignments"),
    ("enrollments.view", "View enrollments", "enrollments"),
    ("enrollments.create", "Create enrollments", "enrollments"),
    ("enrollments.cancel", "Cancel enrollments", "enrollments"),
    ("schedules.view", "View schedules", "schedules"),
    ("schedules.create", "Create schedules", "schedules"),
    ("grades.view", "View grades", "grades"),
    ("grades.update", "Update grades", "grades"),
    ("attendance.view", "View attendance", "attendance"),
    ("attendance.update", "Update attendance", "attendance"),
    ("kardex.view", "View kardex", "kardex"),
    ("kardex.update", "Update kardex", "kardex"),
    ("dashboard.view", "View dashboard", "dashboard"),
    ("reports.view", "View reports", "reports"),
    ("reports.generate", "Generate reports", "reports"),
    ("reports.export", "Export reports", "reports"),
    ("notifications.view", "View notifications", "notifications"),
    ("notifications.create", "Create notifications", "notifications"),
    ("history.view", "View user history", "history"),
    ("ai.use", "Use AI assistant", "ai"),
    ("audit.view", "View audit", "audit"),
]

ADMIN_PERMS = [p[0] for p in PERMISSIONS]
TEACHER_PERMS = [
    "students.view",
    "careers.view",
    "subjects.view",
    "curriculum.view",
    "terms.view",
    "courses.view",
    "enrollments.view",
    "grades.view",
    "grades.update",
    "attendance.view",
    "attendance.update",
    "dashboard.view",
    "reports.view",
    "reports.generate",
    "notifications.view",
    "history.view",
    "ai.use",
]
STUDENT_PERMS = [
    "grades.view",
    "attendance.view",
    "kardex.view",
    "dashboard.view",
    "notifications.view",
    "history.view",
    "ai.use",
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        perm_map: dict[str, Permission] = {}
        for code, desc, module in PERMISSIONS:
            existing = db.scalar(select(Permission).where(Permission.code == code))
            if existing:
                perm_map[code] = existing
            else:
                perm = Permission(code=code, description=desc, module=module)
                db.add(perm)
                db.flush()
                perm_map[code] = perm

        def upsert_role(code: str, name: str, codes: list[str]) -> Role:
            role = db.scalar(select(Role).where(Role.code == code))
            if role is None:
                role = Role(code=code, name=name, is_active=True)
                db.add(role)
                db.flush()
            role.permissions = [perm_map[c] for c in codes if c in perm_map]
            return role

        admin_role = upsert_role("ADMINISTRATOR", "Administrator", ADMIN_PERMS)
        upsert_role("TEACHER", "Teacher", TEACHER_PERMS)
        upsert_role("STUDENT", "Student", STUDENT_PERMS)

        admin = db.scalar(select(User).where(User.username == "admin"))
        if admin is None:
            admin = User(
                username="admin",
                email="admin@siga.local",
                password_hash=hash_password("Admin123!"),
                status="ACTIVE",
            )
            admin.roles.append(admin_role)
            db.add(admin)
        else:
            # Lab: always restore known demo password so UI login stays predictable.
            admin.password_hash = hash_password("Admin123!")
            admin.status = "ACTIVE"
            if admin_role not in admin.roles:
                admin.roles.append(admin_role)

        teacher = db.scalar(select(User).where(User.username == "teacher1"))
        if teacher is None:
            t_role = db.scalar(select(Role).where(Role.code == "TEACHER"))
            teacher = User(
                username="teacher1",
                email="teacher1@siga.local",
                password_hash=hash_password("Teacher123!"),
                status="ACTIVE",
            )
            if t_role:
                teacher.roles.append(t_role)
            db.add(teacher)
        else:
            teacher.password_hash = hash_password("Teacher123!")
            teacher.status = "ACTIVE"

        student = db.scalar(select(User).where(User.username == "student1"))
        if student is None:
            s_role = db.scalar(select(Role).where(Role.code == "STUDENT"))
            student = User(
                username="student1",
                email="student1@siga.local",
                password_hash=hash_password("Student123!"),
                status="ACTIVE",
            )
            if s_role:
                student.roles.append(s_role)
            db.add(student)
        else:
            student.password_hash = hash_password("Student123!")
            student.status = "ACTIVE"

        db.commit()
        print("OK: IAM seed completed")
        print("  users: admin / teacher1 / student1")
        print("  default passwords: Admin123! / Teacher123! / Student123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
