# Ref: seeder integral | Skill: K-024 | Fase: pruebas funcionales
"""Coherent academic campus: 3 careers, 15 subjects, 16 teachers, 300 students."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, timedelta, time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from sqlalchemy import delete, or_, select

from app.auth.password import hash_password
from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.models import (
    AcademicTerm,
    AttendanceRecord,
    AttendanceSession,
    Career,
    Classroom,
    Course,
    Curriculum,
    CurriculumSubject,
    Enrollment,
    Evaluation,
    Grade,
    KardexEntry,
    Role,
    Schedule,
    Student,
    Subject,
    Teacher,
    TeachingAssignment,
    User,
)
from app.services.grade_rules import resolve_course_grade

TEACHER_PASSWORD = "Teacher123!"
STUDENT_PASSWORD = "Student123!"

CAREERS = [
    {"code": "DSW", "name": "Desarrollo de Software", "duration": 6, "teachers": 6, "students": 120},
    {"code": "MAU", "name": "Mecánica Automotriz", "duration": 6, "teachers": 5, "students": 90},
    {"code": "MAG", "name": "Mecanización Agrícola", "duration": 6, "teachers": 5, "students": 90},
]

SUBJECTS = [
    ("DSW", 1, "DSW101", "Fundamentos de Programación", 4, 2, 1, 2),
    ("DSW", 1, "DSW102", "Bases de Datos", 4, 2, 1, 2),
    ("DSW", 2, "DSW201", "Programación Web", 4, 2, 1, 2),
    ("DSW", 2, "DSW202", "Desarrollo de Aplicaciones Móviles", 4, 2, 1, 2),
    ("DSW", 3, "DSW301", "Seguridad Informática", 3, 2, 1, 1),
    ("MAU", 1, "MAU101", "Motores de Combustión", 4, 2, 2, 1),
    ("MAU", 1, "MAU102", "Sistemas Eléctricos Automotrices", 4, 2, 2, 1),
    ("MAU", 2, "MAU201", "Sistemas de Transmisión", 4, 2, 2, 1),
    ("MAU", 2, "MAU202", "Frenos y Suspensión", 3, 2, 1, 1),
    ("MAU", 3, "MAU301", "Diagnóstico Automotriz", 3, 1, 2, 1),
    ("MAG", 1, "MAG101", "Tractores Agrícolas", 4, 2, 2, 1),
    ("MAG", 1, "MAG102", "Maquinaria Agrícola", 4, 2, 2, 1),
    ("MAG", 2, "MAG201", "Sistemas Hidráulicos", 4, 2, 2, 1),
    ("MAG", 2, "MAG202", "Motores Diésel", 3, 2, 1, 1),
    ("MAG", 3, "MAG301", "Mantenimiento de Maquinaria", 3, 1, 2, 1),
]

TERMS = [
    {
        "code": "IPA-2026",
        "name": "IPA 2026",
        "start": date(2026, 1, 6),
        "end": date(2026, 5, 29),
        "status": "CLOSED",
        "current": False,
        "levels": {1, 2},
    },
    {
        "code": "IIPA-2026",
        "name": "IIPA 2026",
        "start": date(2026, 6, 1),
        "end": date(2026, 10, 30),
        "status": "ACTIVE",
        "current": True,
        "levels": {1, 2, 3},
    },
    {
        "code": "IPA-2027",
        "name": "IPA 2027",
        "start": date(2027, 1, 5),
        "end": date(2027, 5, 28),
        "status": "PLANNED",
        "current": False,
        "levels": {2, 3},
    },
]

TEACHERS = [
    ("teacher1", "Juan", "Pérez", "DSW", "Ingeniería de software"),
    ("teacher2", "Lucía", "Morales", "DSW", "Bases de datos"),
    ("teacher3", "Andrés", "Cevallos", "DSW", "Desarrollo web"),
    ("teacher4", "Paola", "Andrade", "DSW", "Desarrollo móvil"),
    ("teacher5", "Diego", "Salazar", "DSW", "Redes y seguridad"),
    ("teacher6", "Elena", "Vásquez", "DSW", "Sistemas operativos"),
    ("teacher7", "Héctor", "Ríos", "MAU", "Motores"),
    ("teacher8", "Mónica", "Paredes", "MAU", "Electricidad automotriz"),
    ("teacher9", "Iván", "Chávez", "MAU", "Transmisiones"),
    ("teacher10", "Karla", "Bustos", "MAU", "Frenos y suspensión"),
    ("teacher11", "Oscar", "Miranda", "MAU", "Diagnóstico"),
    ("teacher12", "Rosa", "Cabrera", "MAG", "Tractores"),
    ("teacher13", "Fabián", "León", "MAG", "Maquinaria agrícola"),
    ("teacher14", "Natalia", "Espinoza", "MAG", "Hidráulica"),
    ("teacher15", "Pedro", "Aguirre", "MAG", "Motores diésel"),
    ("teacher16", "Gloria", "Zambrano", "MAG", "Mantenimiento"),
]

CLASSROOMS = [
    ("AULA-101", "Aula 101", 40),
    ("AULA-102", "Aula 102", 40),
    ("AULA-201", "Aula 201", 40),
    ("AULA-301", "Aula 301", 40),
    ("LAB-SOFT", "Laboratorio de Software", 30),
    ("LAB-AUTO", "Laboratorio Automotriz", 24),
    ("LAB-AGRO", "Laboratorio Agrícola", 24),
    ("TALLER-1", "Taller 1", 20),
    ("TALLER-2", "Taller 2", 20),
    ("AUD-01", "Auditorio 1", 80),
]

SLOTS = [
    ("MON", time(8, 0), time(10, 0)),
    ("MON", time(10, 0), time(12, 0)),
    ("TUE", time(8, 0), time(10, 0)),
    ("TUE", time(10, 0), time(12, 0)),
    ("WED", time(8, 0), time(10, 0)),
    ("WED", time(14, 0), time(16, 0)),
    ("THU", time(8, 0), time(10, 0)),
    ("THU", time(10, 0), time(12, 0)),
    ("FRI", time(8, 0), time(10, 0)),
    ("FRI", time(10, 0), time(12, 0)),
]

WEEKDAY = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}

FIRST_NAMES = [
    "María Fernanda", "Juan Carlos", "Ana Lucía", "Carlos Andrés", "Sofía",
    "Luis", "Valentina", "José", "Camila", "Miguel", "Daniela", "Fernando",
    "Gabriela", "Ricardo", "Paula", "Sebastián", "Andrea", "Mateo", "Carolina",
    "Emilio", "Isabel", "Nicolás", "Patricia", "Álvaro", "Doménica", "Esteban",
    "Melissa", "Pablo", "Alejandra", "David", "Romina", "Cristian", "Emily",
    "Jonathan", "Katherine", "Mauricio", "Nicole", "Roberto", "Stephanie", "Xavier",
]
LAST_NAMES = [
    "López", "Pérez", "Vera", "Torres", "Ruiz", "García", "Castro", "Mendoza",
    "Ortiz", "Flores", "Herrera", "Jiménez", "Navarro", "Ramos", "Suárez",
    "Vargas", "Benítez", "Delgado", "Acosta", "Pacheco", "Quiroz", "Reyes",
    "Santos", "Valencia", "Yépez", "Alarcón", "Bravo", "Córdova", "Dávila", "Enríquez",
]

GRADE_PAIRS = [
    (Decimal("8.50"), Decimal("9.00"), None),
    (Decimal("10.00"), Decimal("8.00"), None),
    (Decimal("7.25"), Decimal("7.75"), None),
    (Decimal("9.50"), Decimal("9.00"), None),
    (Decimal("8.00"), Decimal("7.50"), None),
    (Decimal("7.00"), Decimal("7.00"), None),
    (Decimal("6.75"), Decimal("6.25"), None),
    (Decimal("6.00"), Decimal("6.50"), Decimal("7.50")),
    (Decimal("5.50"), Decimal("6.00"), Decimal("6.25")),
    (Decimal("9.25"), Decimal("8.75"), None),
]


def _one(db, model, **filters):
    return db.scalar(select(model).filter_by(**filters))


def _upsert(db, model, where: dict, values: dict):
    row = _one(db, model, **where)
    if row is None:
        row = model(**where, **values)
        db.add(row)
        db.flush()
        return row
    for key, value in values.items():
        setattr(row, key, value)
    return row


def _level_for_index(index: int, total: int) -> int:
    if index < int(total * 0.40):
        return 1
    if index < int(total * 0.73):
        return 2
    return 3


def _enroll_levels(student_level: int, term_code: str) -> set[int]:
    if term_code == "IPA-2026":
        if student_level == 2:
            return {1}
        if student_level == 3:
            return {2}
        return set()
    if term_code == "IIPA-2026":
        return {student_level}
    if term_code == "IPA-2027":
        if student_level == 1:
            return {2}
        if student_level == 2:
            return {3}
        return set()
    return set()


def _iter_dates(start: date, end: date, weekday: int, limit: int, cap: date | None) -> list[date]:
    out: list[date] = []
    cursor = start
    last = min(end, cap) if cap else end
    while cursor <= last and len(out) < limit:
        if cursor.weekday() == weekday:
            out.append(cursor)
        cursor += timedelta(days=1)
    return out


def _retire_legacy_demo(db) -> None:
    subject = _one(db, Subject, code="ZT101")
    term = _one(db, AcademicTerm, code="2026-DEMO")
    career = _one(db, Career, code="IS-DEMO")
    course_ids = []
    if subject and term:
        course_ids = [
            row.id
            for row in db.scalars(
                select(Course).where(Course.subject_id == subject.id, Course.term_id == term.id)
            )
        ]
    if course_ids:
        session_ids = [
            row.id
            for row in db.scalars(select(AttendanceSession).where(AttendanceSession.course_id.in_(course_ids)))
        ]
        if session_ids:
            db.execute(delete(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids)))
            db.execute(delete(AttendanceSession).where(AttendanceSession.id.in_(session_ids)))
        eval_ids = [row.id for row in db.scalars(select(Evaluation).where(Evaluation.course_id.in_(course_ids)))]
        if eval_ids:
            db.execute(delete(Grade).where(Grade.evaluation_id.in_(eval_ids)))
            db.execute(delete(Evaluation).where(Evaluation.id.in_(eval_ids)))
        db.execute(delete(KardexEntry).where(KardexEntry.course_id.in_(course_ids)))
        db.execute(delete(Enrollment).where(Enrollment.course_id.in_(course_ids)))
        db.execute(delete(Schedule).where(Schedule.course_id.in_(course_ids)))
        db.execute(delete(TeachingAssignment).where(TeachingAssignment.course_id.in_(course_ids)))
        db.execute(delete(Course).where(Course.id.in_(course_ids)))
    if subject:
        db.execute(delete(CurriculumSubject).where(CurriculumSubject.subject_id == subject.id))
        db.execute(delete(KardexEntry).where(KardexEntry.subject_id == subject.id))
        db.delete(subject)
    if term:
        db.execute(delete(KardexEntry).where(KardexEntry.term_id == term.id))
        db.delete(term)
    if career:
        for curriculum in db.scalars(select(Curriculum).where(Curriculum.career_id == career.id)):
            db.execute(delete(CurriculumSubject).where(CurriculumSubject.curriculum_id == curriculum.id))
            db.delete(curriculum)
        db.delete(career)
    db.flush()


def _seed_catalog(db) -> dict:
    careers = {}
    for item in CAREERS:
        careers[item["code"]] = _upsert(
            db,
            Career,
            {"code": item["code"]},
            {
                "name": item["name"],
                "modality": "PRESENCIAL",
                "duration_semesters": item["duration"],
                "status": "ACTIVE",
            },
        )
    terms = {}
    for item in TERMS:
        terms[item["code"]] = _upsert(
            db,
            AcademicTerm,
            {"code": item["code"]},
            {
                "name": item["name"],
                "start_date": item["start"],
                "end_date": item["end"],
                "status": item["status"],
                "is_current": item["current"],
            },
        )
    subjects = {}
    curricula = {}
    for career in CAREERS:
        curricula[career["code"]] = _upsert(
            db,
            Curriculum,
            {"career_id": careers[career["code"]].id, "version": "2026.1"},
            {"status": "ACTIVE"},
        )
    for career_code, level, code, name, credits, theory, practical, autonomous in SUBJECTS:
        subject = _upsert(
            db,
            Subject,
            {"code": code},
            {
                "name": name,
                "description": f"Asignatura de {careers[career_code].name}",
                "credits": Decimal(credits),
                "hours": (theory + practical) * 16,
                "type": "OBLIGATORIA",
                "status": "ACTIVE",
            },
        )
        subjects[code] = {
            "row": subject,
            "career": career_code,
            "level": level,
            "theory": theory,
            "practical": practical,
            "autonomous": autonomous,
            "credits": Decimal(credits),
        }
        _upsert(
            db,
            CurriculumSubject,
            {"curriculum_id": curricula[career_code].id, "subject_id": subject.id},
            {"level": level, "semester": level, "credits": Decimal(credits)},
        )
    rooms = [
        _upsert(db, Classroom, {"code": code}, {"name": name, "capacity": cap})
        for code, name, cap in CLASSROOMS
    ]
    return {"careers": careers, "terms": terms, "subjects": subjects, "rooms": rooms}


def _seed_teachers(db, careers: dict, teacher_role: Role | None) -> dict:
    password_hash = hash_password(TEACHER_PASSWORD)
    by_career = defaultdict(list)
    for index, (username, first, last, career_code, specialty) in enumerate(TEACHERS, start=1):
        user = _one(db, User, username=username)
        cedula = user.cedula if user and user.cedula else f"19{index:08d}"
        if user is None:
            user = User(
                username=username,
                email=f"{username}@siga.local",
                cedula=cedula,
                first_name=first,
                last_name=last,
                password_hash=password_hash,
                status="ACTIVE",
            )
            if teacher_role:
                user.roles.append(teacher_role)
            db.add(user)
            db.flush()
        else:
            user.first_name = first
            user.last_name = last
            user.status = "ACTIVE"
            user.email = user.email or f"{username}@siga.local"
            user.password_hash = password_hash
            if teacher_role and teacher_role not in user.roles:
                user.roles.append(teacher_role)
        teacher = _upsert(
            db,
            Teacher,
            {"user_id": user.id},
            {
                "teacher_code": f"DOC-{career_code}-{index:02d}",
                "specialty": specialty,
                "status": "ACTIVE",
            },
        )
        by_career[career_code].append(teacher)
    return by_career


def _seed_students(db, careers: dict, student_role: Role | None) -> dict:
    password_hash = hash_password(STUDENT_PASSWORD)
    by_career = defaultdict(list)
    number = 0
    for career in CAREERS:
        for local_index in range(career["students"]):
            number += 1
            username = f"student{number}"
            first = FIRST_NAMES[(number - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[((number - 1) * 7) % len(LAST_NAMES)]
            if number == 1:
                first, last = "María Fernanda", "López"
            user = _one(db, User, username=username)
            cedula = user.cedula if user and user.cedula else f"18{number:08d}"
            if user is None:
                user = User(
                    username=username,
                    email=f"{username}@siga.local",
                    cedula=cedula,
                    first_name=first,
                    last_name=last,
                    password_hash=password_hash,
                    status="ACTIVE",
                )
                if student_role:
                    user.roles.append(student_role)
                db.add(user)
                db.flush()
            else:
                user.first_name = first
                user.last_name = last
                user.status = "ACTIVE"
                if student_role and student_role not in user.roles:
                    user.roles.append(student_role)
                user.password_hash = password_hash
            level = 2 if number == 1 else _level_for_index(local_index, career["students"])
            student = _upsert(
                db,
                Student,
                {"user_id": user.id},
                {
                    "student_code": f"EST-{career['code']}-{local_index + 1:04d}",
                    "career_id": careers[career["code"]].id,
                    "level": str(level),
                    "admission_date": date(2025 if level > 1 else 2026, 1, 10),
                    "status": "ACTIVE",
                },
            )
            by_career[career["code"]].append((student, level))
    return by_career


def _assign_teacher(teachers_by_career: dict, career_code: str, term_code: str, subject_code: str, cursor: dict):
    teachers = teachers_by_career[career_code]
    teacher1 = teachers_by_career["DSW"][0]
    if career_code == "DSW" and term_code == "IIPA-2026" and subject_code in {"DSW201", "DSW202", "DSW301"}:
        return teacher1
    pool = [row for row in teachers if row.id != teacher1.id] or teachers
    teacher = pool[cursor[career_code] % len(pool)]
    cursor[career_code] += 1
    return teacher


def _seed_offer(db, catalog: dict, teachers_by_career: dict) -> list[dict]:
    offered = []
    teacher_cursor = defaultdict(int)
    for term_code, term in catalog["terms"].items():
        allowed_levels = next(item["levels"] for item in TERMS if item["code"] == term_code)
        for subject_code, meta in catalog["subjects"].items():
            if meta["level"] not in allowed_levels:
                continue
            career_code = meta["career"]
            teacher = _assign_teacher(teachers_by_career, career_code, term_code, subject_code, teacher_cursor)
            course = _upsert(
                db,
                Course,
                {
                    "subject_id": meta["row"].id,
                    "term_id": term.id,
                    "parallel_code": f"{meta['level']}A",
                },
                {
                    "capacity": 80,
                    "hours_theory": meta["theory"],
                    "hours_practical": meta["practical"],
                    "hours_autonomous": meta["autonomous"],
                    "status": "ACTIVE" if term.status != "PLANNED" else "PLANNED",
                },
            )
            _upsert(
                db,
                TeachingAssignment,
                {"teacher_id": teacher.id, "course_id": course.id, "term_id": term.id},
                {"status": "ACTIVE"},
            )
            for other in db.scalars(
                select(TeachingAssignment).where(TeachingAssignment.course_id == course.id)
            ):
                if other.teacher_id != teacher.id:
                    other.status = "INACTIVE"
            offered.append(
                {
                    "course": course,
                    "term": term,
                    "term_code": term_code,
                    "subject": meta,
                    "teacher": teacher,
                    "career": career_code,
                    "level": meta["level"],
                }
            )
    return offered


def _seed_enrollments(db, offered: list[dict], students_by_career: dict) -> list[tuple]:
    pairs = []
    for item in offered:
        for student, student_level in students_by_career[item["career"]]:
            if item["level"] not in _enroll_levels(student_level, item["term_code"]):
                continue
            enrollment = _one(
                db,
                Enrollment,
                student_id=student.id,
                course_id=item["course"].id,
                term_id=item["term"].id,
            )
            if enrollment is None:
                db.add(
                    Enrollment(
                        student_id=student.id,
                        course_id=item["course"].id,
                        term_id=item["term"].id,
                        status="ACTIVE",
                    )
                )
            else:
                enrollment.status = "ACTIVE"
            pairs.append((student, item))
    db.flush()
    _purge_stale_enrollments(db, pairs)
    return pairs


def _purge_stale_enrollments(db, pairs: list[tuple]) -> None:
    intended = {(student.id, item["course"].id) for student, item in pairs}
    official_students = {student.id for student, _item in pairs}
    official_students.update(
        row.id for row in db.scalars(select(Student).where(Student.student_code.like("EST-%")))
    )
    official_courses = {item["course"].id for _student, item in pairs}
    if not official_students or not official_courses:
        return
    stale = [
        row
        for row in db.scalars(
            select(Enrollment).where(
                Enrollment.student_id.in_(official_students),
                Enrollment.course_id.in_(official_courses),
            )
        )
        if (row.student_id, row.course_id) not in intended
    ]
    for enrollment in stale:
        course = db.get(Course, enrollment.course_id)
        session_ids = [
            row.id
            for row in db.scalars(
                select(AttendanceSession).where(AttendanceSession.course_id == enrollment.course_id)
            )
        ]
        if session_ids:
            db.execute(
                delete(AttendanceRecord).where(
                    AttendanceRecord.session_id.in_(session_ids),
                    AttendanceRecord.student_id == enrollment.student_id,
                )
            )
        if course is not None:
            db.execute(
                delete(KardexEntry).where(
                    KardexEntry.student_id == enrollment.student_id,
                    KardexEntry.term_id == enrollment.term_id,
                    KardexEntry.subject_id == course.subject_id,
                )
            )
        db.delete(enrollment)
    if stale:
        db.flush()


def _seed_schedules(db, offered: list[dict], rooms: list[Classroom]) -> dict[int, Schedule]:
    busy_teacher = set()
    busy_room = set()
    existing = {
        row.course_id: row
        for row in db.scalars(select(Schedule)).all()
    }
    by_course = {}
    room_index = 0
    slot_index = 0
    for item in offered:
        course = item["course"]
        if course.id in existing:
            by_course[course.id] = existing[course.id]
            continue
        assigned = None
        for offset in range(len(SLOTS)):
            day, start, end = SLOTS[(slot_index + offset) % len(SLOTS)]
            room = rooms[(room_index + offset) % len(rooms)]
            t_key = (item["teacher"].id, item["term"].id, day, start)
            r_key = (room.id, item["term"].id, day, start)
            if t_key in busy_teacher or r_key in busy_room:
                continue
            assigned = Schedule(
                course_id=course.id,
                teacher_id=item["teacher"].id,
                classroom_id=room.id,
                term_id=item["term"].id,
                day_of_week=day,
                start_time=start,
                end_time=end,
            )
            busy_teacher.add(t_key)
            busy_room.add(r_key)
            slot_index += 1
            room_index += 1
            break
        if assigned is None:
            day, start, end = SLOTS[slot_index % len(SLOTS)]
            room = rooms[room_index % len(rooms)]
            assigned = Schedule(
                course_id=course.id,
                teacher_id=item["teacher"].id,
                classroom_id=room.id,
                term_id=item["term"].id,
                day_of_week=day,
                start_time=start,
                end_time=end,
            )
            slot_index += 1
            room_index += 1
        db.add(assigned)
        by_course[course.id] = assigned
    db.flush()
    return by_course


def _seed_attendance(db, offered: list[dict], pairs: list[tuple], schedules: dict[int, Schedule]) -> None:
    existing_sessions = {
        (row.course_id, row.session_date, row.hour_slot): row
        for row in db.scalars(select(AttendanceSession)).all()
    }
    students_by_course = defaultdict(list)
    for student, item in pairs:
        students_by_course[item["course"].id].append(student)
    today = date.today()
    for item in offered:
        schedule = schedules.get(item["course"].id)
        if schedule is None:
            continue
        if item["term"].status == "ACTIVE":
            cap = today
        elif item["term"].status == "CLOSED":
            cap = item["term"].end_date
        else:
            cap = None
        dates = _iter_dates(
            item["term"].start_date,
            item["term"].end_date,
            WEEKDAY[schedule.day_of_week],
            6,
            cap,
        )
        slots = max(1, item["subject"]["theory"] + item["subject"]["practical"])
        slots = min(slots, 3)
        for session_date in dates:
            for hour in range(1, slots + 1):
                key = (item["course"].id, session_date, hour)
                session = existing_sessions.get(key)
                if session is None:
                    session = AttendanceSession(
                        course_id=item["course"].id,
                        session_date=session_date,
                        hour_slot=hour,
                        topic=f"{item['subject']['row'].name} · hora {hour}",
                    )
                    db.add(session)
                    db.flush()
                    existing_sessions[key] = session
                present_ids = {
                    row.student_id
                    for row in db.scalars(
                        select(AttendanceRecord).where(AttendanceRecord.session_id == session.id)
                    )
                }
                for student in students_by_course[item["course"].id]:
                    if student.id in present_ids:
                        continue
                    pattern = student.id % 4
                    if pattern == 0:
                        status = "PRESENT"
                    elif pattern == 1:
                        status = "LATE" if hour == 1 and session_date.day % 2 == 0 else "PRESENT"
                    elif pattern == 2:
                        status = "ABSENT" if session_date.day % 3 == 0 else "PRESENT"
                    else:
                        status = "ABSENT" if session_date.day % 2 == 0 else "PRESENT"
                    db.add(
                        AttendanceRecord(
                            session_id=session.id,
                            student_id=student.id,
                            status=status,
                            notes=None,
                        )
                    )
    db.flush()


def _seed_grades(db, pairs: list[tuple]) -> None:
    existing = {
        (row.student_id, row.term_id, row.subject_id): row
        for row in db.scalars(select(KardexEntry)).all()
    }
    for student, item in pairs:
        first, second, recovery = GRADE_PAIRS[(student.id + item["course"].id) % len(GRADE_PAIRS)]
        resolved = resolve_course_grade(first, second, recovery)
        key = (student.id, item["term"].id, item["subject"]["row"].id)
        row = existing.get(key)
        if row is None:
            row = KardexEntry(
                student_id=student.id,
                term_id=item["term"].id,
                subject_id=item["subject"]["row"].id,
                course_id=item["course"].id,
                credits=item["subject"]["credits"],
            )
            db.add(row)
            existing[key] = row
        row.course_id = item["course"].id
        row.first_partial = resolved.first_partial
        row.second_partial = resolved.second_partial
        row.recovery_grade = resolved.recovery_grade
        row.final_grade = resolved.official_grade
        row.academic_status = resolved.academic_status
        row.credits = item["subject"]["credits"]
    db.flush()


def _validate(db) -> None:
    careers = db.scalars(select(Career).where(Career.code.in_(["DSW", "MAU", "MAG"]))).all()
    career_ids = {row.id for row in careers}
    subjects = db.scalars(
        select(Subject).where(
            or_(
                Subject.code.like("DSW%"),
                Subject.code.like("MAU%"),
                Subject.code.like("MAG%"),
            )
        )
    ).all()
    terms = {
        row.code: row
        for row in db.scalars(select(AcademicTerm).where(AcademicTerm.code.in_([item["code"] for item in TERMS])))
    }
    teachers = db.scalars(select(Teacher).where(Teacher.teacher_code.like("DOC-%"))).all()
    students = db.scalars(select(Student).where(Student.student_code.like("EST-%"))).all()
    official_students = [row for row in students if row.career_id in career_ids]
    curricula = db.scalars(select(Curriculum).where(Curriculum.career_id.in_(career_ids))).all()
    subject_ids = {row.id for row in subjects}
    courses = db.scalars(select(Course).where(Course.subject_id.in_(subject_ids))).all()
    course_ids = {row.id for row in courses}
    assignments = db.scalars(
        select(TeachingAssignment).where(
            TeachingAssignment.status == "ACTIVE",
            TeachingAssignment.course_id.in_(course_ids),
        )
    ).all()
    enrollments = db.scalars(
        select(Enrollment).where(Enrollment.status == "ACTIVE", Enrollment.course_id.in_(course_ids))
    ).all()
    schedules = db.scalars(select(Schedule).where(Schedule.course_id.in_(course_ids))).all()
    sessions = db.scalars(select(AttendanceSession).where(AttendanceSession.course_id.in_(course_ids))).all()
    session_ids = {row.id for row in sessions}
    records = (
        db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids))).all()
        if session_ids
        else []
    )
    notes = db.scalars(select(KardexEntry).where(KardexEntry.subject_id.in_(subject_ids))).all()

    errors = []
    if len(careers) != 3:
        errors.append(f"carreras={len(careers)}")
    if len(subjects) != 15:
        errors.append(f"materias={len(subjects)}")
    if len(terms) != 3:
        errors.append(f"periodos={len(terms)}")
    active_terms = [row for row in terms.values() if row.status == "ACTIVE"]
    if len(active_terms) != 1:
        errors.append(f"periodos_activos={len(active_terms)}")
    if len(teachers) < 16:
        errors.append(f"docentes={len(teachers)}")
    if len(official_students) < 300:
        errors.append(f"estudiantes={len(official_students)}")
    if len(curricula) < 3:
        errors.append("mallas incompletas")
    if not courses:
        errors.append("sin cursos")
    if not assignments:
        errors.append("sin asignaciones")
    if not enrollments:
        errors.append("sin matrículas")
    if not schedules:
        errors.append("sin horarios")
    if not records:
        errors.append("sin asistencias")
    if not notes:
        errors.append("sin notas")

    assigned_courses = {row.course_id for row in assignments}
    scheduled_courses = {row.course_id for row in schedules}
    enrolled_courses = {row.course_id for row in enrollments}
    enrolled_pairs = {(row.student_id, row.course_id) for row in enrollments}
    for course in courses:
        if course.id not in assigned_courses:
            errors.append(f"curso {course.parallel_code} sin docente")
            break
        if course.id not in scheduled_courses:
            errors.append(f"curso {course.parallel_code} sin horario")
            break
        if course.id not in enrolled_courses:
            errors.append(f"curso {course.parallel_code} sin matriculas")
            break

    student_career = {row.id: row.career_id for row in official_students}
    subject_career = {}
    for career_code, _level, code, *_rest in SUBJECTS:
        subject = next((row for row in subjects if row.code == code), None)
        if subject:
            subject_career[subject.id] = next(row.id for row in careers if row.code == career_code)
    for enrollment in enrollments:
        course = next((row for row in courses if row.id == enrollment.course_id), None)
        career_id = student_career.get(enrollment.student_id)
        expected = subject_career.get(course.subject_id) if course else None
        if career_id and expected and career_id != expected:
            errors.append("matricula cruzada entre carreras")
            break

    session_course = {row.id: row.course_id for row in sessions}
    for record in records:
        course_id = session_course.get(record.session_id)
        if course_id and (record.student_id, course_id) not in enrolled_pairs:
            errors.append("asistencia sin matricula")
            break

    for entry in notes:
        course = next((row for row in courses if row.id == entry.course_id), None)
        if course is None or (entry.student_id, course.id) not in enrolled_pairs:
            errors.append("nota sin matricula")
            break

    for term in terms.values():
        term_courses = [row for row in courses if row.term_id == term.id]
        if not term_courses:
            errors.append(f"periodo {term.code} sin cursos")
        if not any(row.term_id == term.id for row in enrollments):
            errors.append(f"periodo {term.code} sin matriculas")
        if not any(row.term_id == term.id for row in notes):
            errors.append(f"periodo {term.code} sin notas")
        term_course_ids = {row.id for row in term_courses}
        if not any(row.course_id in term_course_ids for row in sessions):
            errors.append(f"periodo {term.code} sin asistencias")

    teacher1 = _one(db, User, username="teacher1")
    student1 = _one(db, User, username="student1")
    teacher_profile = _one(db, Teacher, user_id=teacher1.id) if teacher1 else None
    student_profile = _one(db, Student, user_id=student1.id) if student1 else None
    teacher_courses = []
    student_enrollments = []
    if teacher_profile:
        teacher_courses = db.scalars(
            select(TeachingAssignment).where(
                TeachingAssignment.teacher_id == teacher_profile.id,
                TeachingAssignment.status == "ACTIVE",
            )
        ).all()
    if student_profile:
        student_enrollments = db.scalars(
            select(Enrollment).where(
                Enrollment.student_id == student_profile.id,
                Enrollment.status == "ACTIVE",
            )
        ).all()
    if not teacher_courses:
        errors.append("teacher1 sin cursos")
    if not student_enrollments:
        errors.append("student1 sin matriculas")
    active_term = terms.get("IIPA-2026")
    overlap = []
    if active_term and teacher_courses and student_enrollments:
        student_course_ids = {row.course_id for row in student_enrollments}
        overlap = [
            row
            for row in teacher_courses
            if row.course_id in student_course_ids
            and (db.get(Course, row.course_id).term_id == active_term.id)
        ]
        if not overlap:
            errors.append("teacher1 y student1 no comparten curso activo")
        if student_profile and str(student_profile.level) != "2":
            errors.append("student1 no esta en nivel 2")

    print("VALIDACION")
    print(f"  carreras={len(careers)} materias={len(subjects)} periodos={len(terms)}")
    print(f"  docentes={len(teachers)} estudiantes={len(official_students)}")
    print(f"  mallas={len(curricula)} cursos={len(courses)} asignaciones={len(assignments)}")
    print(f"  matriculas={len(enrollments)} horarios={len(schedules)}")
    print(f"  sesiones_asistencia={len(sessions)} registros_asistencia={len(records)} notas={len(notes)}")
    print(f"  teacher1 cursos={len(teacher_courses)} student1 matriculas={len(student_enrollments)} overlap_activo={len(overlap)}")
    if errors:
        raise SystemExit("FAIL: " + ", ".join(errors))
    print("OK: relaciones coherentes, sin faltantes oficiales")


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        teacher_role = _one(db, Role, code="TEACHER")
        student_role = _one(db, Role, code="STUDENT")
        if teacher_role is None or student_role is None:
            raise SystemExit("FAIL: ejecute primero scripts/seed_iam.py")

        _retire_legacy_demo(db)
        catalog = _seed_catalog(db)
        db.commit()
        teachers = _seed_teachers(db, catalog["careers"], teacher_role)
        students = _seed_students(db, catalog["careers"], student_role)
        db.commit()
        offered = _seed_offer(db, catalog, teachers)
        pairs = _seed_enrollments(db, offered, students)
        schedules = _seed_schedules(db, offered, catalog["rooms"])
        db.commit()
        _seed_attendance(db, offered, pairs, schedules)
        _seed_grades(db, pairs)
        db.commit()
        _validate(db)
        print("OK: seeder académico integral completado")
        print(f"  docentes: teacher1..teacher16 / {TEACHER_PASSWORD}")
        print(f"  estudiantes: student1..student300 / {STUDENT_PASSWORD}")
        print("  teacher1 (Juan Perez): IIPA 2026 Web, Movil y Seguridad")
        print("  student1 (Maria Fernanda Lopez): DSW nivel 2, misma oferta activa que teacher1")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
