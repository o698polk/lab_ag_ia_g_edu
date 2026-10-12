"""
Seeder académico coherente — SPEC-011 / SKILL-010 (laboratorio avanzado).

- 3 carreras (DSW, MAU, MAG)
- 2 periodos activos (2025-1, 2025-2)
- 20 docentes (7/7/6)
- 400 estudiantes (134/133/133)
- Staff: rector, auditor, 3 coordinadores, secretaría, tutor, soporte TI
- Cursos, asignaciones, horarios, matrículas, notas y asistencias coherentes
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from seed_massive import (
    CAREERS_DEF,
    FIRST_NAMES,
    LAST_NAMES,
    clear_academic_data,
)

# Periodo → índices de materias (0..5) — progresión en 2 periodos
TERM_SUBJECT_MAP = {
    "2025-1": (0, 1, 2),
    "2025-2": (3, 4, 5),
}

TERMS_COHERENT = [
    # code, name, start_offset_days, end_offset_days, is_active, grades_closed
    ("2025-1", "Periodo 2025-1", 200, 40, True, False),
    ("2025-2", "Periodo 2025-2", 30, -130, True, False),
]

SESSIONS_PER_COURSE = 10
# 400 estudiantes: 134 + 133 + 133
STUDENTS_PER_CAREER = (134, 133, 133)
# 20 docentes: 7 + 7 + 6
TEACHERS_PER_CAREER = (7, 7, 6)

STAFF_USERS = [
    ("rector", "rector@institucion.edu", "Ana", "Rectora", "RECTOR", "Rector123!"),
    ("auditor", "auditor@institucion.edu", "Luis", "Auditor", "AUDITOR", "Auditor123!"),
    ("coord01", "coord01@institucion.edu", "María", "Coordinadora DSW", "COORDINATOR", "Coord123!"),
    ("coord02", "coord02@institucion.edu", "Carlos", "Coordinador MAU", "COORDINATOR", "Coord123!"),
    ("coord03", "coord03@institucion.edu", "Sofía", "Coordinadora MAG", "COORDINATOR", "Coord123!"),
    ("secretaria", "secretaria@institucion.edu", "Elena", "Secretaría", "SECRETARY", "Secretaria123!"),
    ("tutor1", "tutor1@institucion.edu", "Pedro", "Tutor", "GUARDIAN", "Tutor123!"),
    ("itsupport", "itsupport@institucion.edu", "Diego", "Soporte", "IT_SUPPORT", "Soporte123!"),
]

# Perfil: (p1_lo, p1_hi, p2_lo, p2_hi, presente, ausente, tardanza, justificada)
PROFILES = [
    (8.5, 10.0, 8.5, 10.0, 0.92, 0.03, 0.03, 0.02),
    (7.5, 9.2, 7.5, 9.2, 0.85, 0.06, 0.06, 0.03),
    (6.0, 8.2, 6.0, 8.2, 0.75, 0.12, 0.08, 0.05),
    (4.5, 7.2, 4.5, 7.2, 0.62, 0.22, 0.10, 0.06),
    (5.0, 8.8, 5.0, 8.8, 0.68, 0.15, 0.12, 0.05),
]


def _clamp_grade(v: float) -> float:
    return round(min(10.0, max(1.0, v)), 1)


def _profile_for(student_id: int):
    return PROFILES[student_id % len(PROFILES)]


def _session_dates(term_start: date, term_end: date, weekday: int, count: int) -> list[date]:
    start = term_start
    while start.weekday() != weekday:
        start += timedelta(days=1)
        if start > term_end:
            return []
    dates = []
    cur = start
    while cur <= term_end and len(dates) < count:
        dates.append(cur)
        cur += timedelta(days=7)
    return dates


def _pick_status(weights, rng: random.Random) -> str:
    labels = ["presente", "ausente", "tardanza", "justificada"]
    return rng.choices(labels, weights=weights, k=1)[0]


def _make_grades(profile, absence_ratio: float, rng: random.Random):
    p1_lo, p1_hi, p2_lo, p2_hi, *_ = profile
    penalty = min(1.5, absence_ratio * 2.5)
    p1 = _clamp_grade(rng.uniform(p1_lo, p1_hi) - penalty * rng.uniform(0, 1))
    p2 = _clamp_grade(rng.uniform(p2_lo, p2_hi) - penalty * rng.uniform(0, 1))
    avg = (p1 + p2) / 2.0
    supp = None
    if avg < 7.0:
        base = 5.5 + (p1_lo - 4.5) * 0.4
        supp = _clamp_grade(rng.uniform(base, min(10.0, base + 3.0)))
    return p1, p2, supp


def _seed_staff(db, role_map, rng: random.Random):
    from app.models import User

    created = []
    for username, email, first, last, role_code, password in STAFF_USERS:
        existing = User.query.filter_by(username=username).first()
        if existing:
            created.append(existing)
            continue
        u = User(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            must_change_password=False,
            is_active=True,
        )
        u.set_password(password)
        role = role_map.get(role_code)
        if role:
            u.roles.append(role)
        db.session.add(u)
        created.append(u)
    db.session.flush()
    return {u.username: u for u in created}


def seed_coherent(app, reset: bool = True):
    from app.extensions import db
    from app.models import (
        Assignment,
        Attendance,
        Career,
        Course,
        Curriculum,
        Enrollment,
        Grade,
        Role,
        Schedule,
        Student,
        Subject,
        Teacher,
        Term,
        User,
    )
    from seed_data import seed_all, sync_profile_visibility_perms

    rng = random.Random(42)

    with app.app_context():
        if not Role.query.first():
            seed_all(app)

        if reset:
            print("SPEC-011: limpiando datos académicos…")
            clear_academic_data(db)

        role_map = {r.code: r for r in Role.query.all()}
        role_teacher = role_map["TEACHER"]
        role_student = role_map["STUDENT"]

        staff = _seed_staff(db, role_map, rng)
        print("Staff:", ", ".join(staff.keys()))

        today = date.today()
        terms = []
        for code, name, start_off, end_off, active, closed in TERMS_COHERENT:
            t = Term(
                code=code,
                name=name,
                start_date=today - timedelta(days=start_off),
                end_date=today - timedelta(days=end_off),
                is_active=active,
                grades_closed=closed,
            )
            db.session.add(t)
            terms.append(t)
        db.session.flush()
        print("Periodos:", [(t.code, t.is_active, str(t.start_date), str(t.end_date)) for t in terms])

        careers = []
        subjects_by_career = {}
        for cdef in CAREERS_DEF:
            c = Career(
                code=cdef["code"],
                name=cdef["name"],
                description=f"Carrera técnica de {cdef['name']}",
                duration_semesters=6,
                is_active=True,
            )
            db.session.add(c)
            db.session.flush()
            careers.append(c)
            subjects_by_career[c.id] = []
            for level, (scode, sname, credits) in enumerate(cdef["subjects"], start=1):
                s = Subject(
                    code=scode,
                    name=sname,
                    credits=credits,
                    career_id=c.id,
                    is_active=True,
                )
                db.session.add(s)
                db.session.flush()
                subjects_by_career[c.id].append(s)
                db.session.add(
                    Curriculum(
                        career_id=c.id,
                        subject_id=s.id,
                        level=level,
                        prerequisite_subject_id=(
                            subjects_by_career[c.id][level - 2].id if level > 1 else None
                        ),
                    )
                )
        db.session.flush()
        print("Carreras:", [c.name for c in careers])

        teachers_by_career = {c.id: [] for c in careers}
        ti = 1
        for career, n_teach in zip(careers, TEACHERS_PER_CAREER):
            for _ in range(n_teach):
                u = User(
                    username=f"docente{ti:02d}",
                    email=f"docente{ti:02d}@institucion.edu",
                    first_name=rng.choice(FIRST_NAMES),
                    last_name=rng.choice(LAST_NAMES),
                    must_change_password=False,
                    is_active=True,
                )
                u.set_password("Docente123!")
                u.roles.append(role_teacher)
                db.session.add(u)
                db.session.flush()
                tch = Teacher(
                    user_id=u.id,
                    teacher_code=f"D-{ti:03d}",
                    specialty=career.name,
                    title="Ing.",
                )
                db.session.add(tch)
                db.session.flush()
                teachers_by_career[career.id].append(tch)
                ti += 1
        db.session.flush()

        students_by_career = {c.id: [] for c in careers}
        si = 1
        tutor = staff.get("tutor1")
        for career, n_stu in zip(careers, STUDENTS_PER_CAREER):
            for j in range(n_stu):
                u = User(
                    username=f"est{si:04d}",
                    email=f"est{si:04d}@estudiante.edu",
                    first_name=rng.choice(FIRST_NAMES),
                    last_name=rng.choice(LAST_NAMES),
                    must_change_password=False,
                    is_active=True,
                )
                u.set_password("Estudiante123!")
                u.roles.append(role_student)
                db.session.add(u)
                db.session.flush()
                st = Student(
                    user_id=u.id,
                    student_code=f"E-{si:04d}",
                    career_id=career.id,
                    phone=f"09{20000000 + si}",
                    status="active",
                    guardian_user_id=tutor.id if tutor and j == 0 else None,
                    guardian_name=tutor.full_name if tutor and j == 0 else None,
                    guardian_phone="0987654321" if tutor and j == 0 else None,
                )
                db.session.add(st)
                db.session.flush()
                students_by_career[career.id].append(st)
                si += 1
            db.session.commit()
        print(f"Docentes: {ti - 1} | Estudiantes: {si - 1}")

        classrooms = {
            careers[0].id: ["Lab-Soft-1", "Lab-Soft-2", "Aula-DSW-101", "Aula-DSW-102"],
            careers[1].id: ["Taller-Auto-1", "Taller-Auto-2", "Aula-MAU-201", "Lab-Electro"],
            careers[2].id: ["Campo-1", "Taller-Agro", "Aula-MAG-301", "Lab-Riego"],
        }

        enroll_count = grade_count = attend_count = course_count = 0

        for term_idx, term in enumerate(terms):
            subj_idxs = TERM_SUBJECT_MAP[term.code]
            for career in careers:
                subjects = subjects_by_career[career.id]
                teachers = teachers_by_career[career.id]
                students = students_by_career[career.id]
                rooms = classrooms[career.id]
                capacity = max(160, len(students) + 10)

                for local_i, sidx in enumerate(subj_idxs):
                    subject = subjects[sidx]
                    teacher = teachers[(term_idx * 3 + local_i) % len(teachers)]
                    course = Course(
                        code=f"{subject.code}-{term.code}-A",
                        name=f"{subject.name} ({term.code})",
                        subject_id=subject.id,
                        term_id=term.id,
                        career_id=career.id,
                        parallel="A",
                        capacity=capacity,
                        is_active=True,
                    )
                    db.session.add(course)
                    db.session.flush()
                    course_count += 1

                    db.session.add(Assignment(teacher_id=teacher.id, course_id=course.id))
                    weekday = (sidx + term_idx) % 5
                    hour = 8 + (local_i % 4) * 2
                    db.session.add(
                        Schedule(
                            course_id=course.id,
                            day_of_week=weekday,
                            start_time=f"{hour:02d}:00",
                            end_time=f"{hour + 2:02d}:00",
                            classroom=rooms[local_i % len(rooms)],
                        )
                    )

                    session_dates = _session_dates(
                        term.start_date, term.end_date, weekday, SESSIONS_PER_COURSE
                    )
                    if len(session_dates) < 4:
                        session_dates = [
                            term.start_date + timedelta(days=7 * i)
                            for i in range(SESSIONS_PER_COURSE)
                            if term.start_date + timedelta(days=7 * i) <= term.end_date
                        ]

                    batch = []
                    for st in students:
                        batch.append(
                            Enrollment(
                                student_id=st.id,
                                course_id=course.id,
                                status="activa",
                            )
                        )
                        enroll_count += 1

                        profile = _profile_for(st.id)
                        weights = profile[4:8]
                        statuses = [_pick_status(weights, rng) for _ in session_dates]
                        absences = sum(1 for s in statuses if s == "ausente")
                        absence_ratio = absences / max(1, len(statuses))

                        for d, status in zip(session_dates, statuses):
                            batch.append(
                                Attendance(
                                    student_id=st.id,
                                    course_id=course.id,
                                    session_date=d,
                                    status=status,
                                    notes="Justificado médico" if status == "justificada" else None,
                                    recorded_by=teacher.user_id,
                                )
                            )
                            attend_count += 1

                        p1, p2, supp = _make_grades(profile, absence_ratio, rng)
                        g = Grade(
                            student_id=st.id,
                            course_id=course.id,
                            partial1=p1,
                            partial2=p2,
                            supplementary=supp,
                            updated_by=teacher.user_id,
                        )
                        g.compute()
                        batch.append(g)
                        grade_count += 1

                    db.session.add_all(batch)
                    db.session.flush()

                db.session.commit()
                print(f"  {term.code} / {career.code}: cohortes OK ({len(students)} est.)")

            print(f"Periodo {term.code}: cursos OK (active={term.is_active})")

        sync_profile_visibility_perms(db)

        summary = {
            "careers": [c.name for c in careers],
            "teachers": ti - 1,
            "students": si - 1,
            "terms": [t.code for t in terms],
            "active_terms": [t.code for t in terms if t.is_active],
            "courses": course_count,
            "enrollments": enroll_count,
            "grades": grade_count,
            "attendance": attend_count,
            "staff": list(staff.keys()),
        }
        print(
            f"OK — Cursos: {course_count} | Matrículas: {enroll_count} | "
            f"Notas: {grade_count} | Asistencias: {attend_count}"
        )
        print("Periodos visibles:", summary["active_terms"])
        print("Credenciales docentes: docente01..docente20 / Docente123!")
        print("Credenciales estudiantes: est0001..est0400 / Estudiante123!")
        print(
            "Staff: rector/Rector123! auditor/Auditor123! coord01..03/Coord123! "
            "secretaria/Secretaria123! tutor1/Tutor123! itsupport/Soporte123!"
        )
        return summary


if __name__ == "__main__":
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run import app

    print(seed_coherent(app, reset=True))
