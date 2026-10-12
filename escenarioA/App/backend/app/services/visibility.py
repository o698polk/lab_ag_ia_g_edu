"""Visibilidad por perfil — SPEC-009 / SKILL-008.

Estudiantes y docentes solo ven periodos habilitados y datos de sus propios cursos.
"""

from app.models import Assignment, Course, Enrollment, Term, User


RESTRICTED_ROLES = {"STUDENT", "TEACHER", "GUARDIAN"}
STAFF_BYPASS = {
    "ADMIN",
    "RECTOR",
    "COORDINATOR",
    "SECRETARY",
    "REVIEWER",
    "AUDITOR",
    "IT_SUPPORT",
}


def is_term_restricted(user: User) -> bool:
    roles = set(user.get_role_codes())
    if roles & STAFF_BYPASS:
        return False
    return bool(roles & RESTRICTED_ROLES)


def visible_term_ids(user: User) -> list[int] | None:
    """None = sin filtro (ve todos). Lista = solo periodos habilitados."""
    if not is_term_restricted(user):
        return None
    return [t.id for t in Term.query.filter_by(is_active=True).all()]


def owned_course_ids(user: User) -> list[int] | None:
    """None = sin restricción de propiedad. Lista = cursos del perfil (puede ser vacía)."""
    roles = set(user.get_role_codes())
    if roles & STAFF_BYPASS:
        return None

    if "TEACHER" in roles and user.teacher:
        ids = [
            a.course_id
            for a in Assignment.query.filter_by(teacher_id=user.teacher.id).all()
        ]
        term_ids = visible_term_ids(user)
        if term_ids is not None:
            allowed = {
                c.id
                for c in Course.query.filter(
                    Course.id.in_(ids or [-1]),
                    Course.term_id.in_(term_ids or [-1]),
                ).all()
            }
            return list(allowed)
        return ids

    if "STUDENT" in roles and user.student:
        ids = [
            e.course_id
            for e in Enrollment.query.filter_by(
                student_id=user.student.id, status="activa"
            ).all()
        ]
        term_ids = visible_term_ids(user)
        if term_ids is not None:
            allowed = {
                c.id
                for c in Course.query.filter(
                    Course.id.in_(ids or [-1]),
                    Course.term_id.in_(term_ids or [-1]),
                ).all()
            }
            return list(allowed)
        return ids

    if roles & RESTRICTED_ROLES:
        return []
    return None


def filter_courses_query(query, user: User):
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        query = query.filter(Course.id.in_(course_ids or [-1]))
        return query

    term_ids = visible_term_ids(user)
    if term_ids is not None:
        query = query.filter(Course.term_id.in_(term_ids or [-1]))
    return query


def apply_course_scope(query, user: User, course_column=Course.id):
    """Filtra un query ya unido a Course (o con course_id) al ámbito del usuario."""
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        return query.filter(course_column.in_(course_ids or [-1]))
    term_ids = visible_term_ids(user)
    if term_ids is not None:
        return query.filter(Course.term_id.in_(term_ids or [-1]))
    return query
