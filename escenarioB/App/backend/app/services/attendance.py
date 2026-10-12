from app.models import Attendance


def absence_rate(student_id: int, course_id: int) -> float:
    records = Attendance.query.filter_by(student_id=student_id, course_id=course_id).all()
    if not records:
        return 0.0
    absences = sum(1 for r in records if r.status == "ausente")
    return absences / len(records)


def is_critical_absence(student_id: int, course_id: int, threshold: float = 0.25) -> bool:
    return absence_rate(student_id, course_id) > threshold
