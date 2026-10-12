"""Validación de cupo por curso/paralelo."""

from app.models import Enrollment

MAX_COURSE_CAPACITY = 60


def count_active_enrollments(course_id: int) -> int:
    return Enrollment.query.filter_by(course_id=course_id, status="activa").count()


def validate_course_capacity(course) -> str | None:
    cap = min(int(course.capacity or MAX_COURSE_CAPACITY), MAX_COURSE_CAPACITY)
    active = count_active_enrollments(course.id)
    if active >= cap:
        return (
            f"Cupo lleno ({active}/{cap}). "
            "Matricule al estudiante en otro paralelo del mismo periodo."
        )
    return None
