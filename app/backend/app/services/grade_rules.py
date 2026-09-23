# Ref: RF-GRD | Skill: K-017 | Fase: calificaciones
"""Academic grade rules: two partials, automatic average, recovery."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

TWOPLACES = Decimal("0.01")
PASSING = Decimal("7.00")

STATUS_APPROVED = "APROBADO"
STATUS_RECOVERY_PENDING = "SUPLETORIO PENDIENTE"
STATUS_APPROVED_RECOVERY = "APROBADO POR RECUPERACIÓN"
STATUS_FAILED = "REPROBADO"
STATUS_IN_PROGRESS = "IN_PROGRESS"

COURSE_STATUSES = {
    STATUS_APPROVED,
    STATUS_RECOVERY_PENDING,
    STATUS_APPROVED_RECOVERY,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
}


class RecoveryNotAllowedError(ValueError):
    def __init__(self) -> None:
        super().__init__("RECOVERY_NOT_ALLOWED")


def quantize_grade(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def parse_grade(value) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    grade = quantize_grade(Decimal(str(value)))
    if grade < 0 or grade > 10:
        raise ValueError("INVALID_GRADE")
    return grade


@dataclass(frozen=True)
class CourseGradeResult:
    first_partial: Optional[Decimal]
    second_partial: Optional[Decimal]
    final_average: Optional[Decimal]
    recovery_grade: Optional[Decimal]
    academic_status: str
    official_grade: Optional[Decimal]
    recovery_allowed: bool


def resolve_course_grade(
    first_partial,
    second_partial,
    recovery_grade,
) -> CourseGradeResult:
    first = parse_grade(first_partial)
    second = parse_grade(second_partial)
    recovery = parse_grade(recovery_grade)

    if first is None or second is None:
        if recovery is not None:
            raise RecoveryNotAllowedError()
        return CourseGradeResult(
            first_partial=first,
            second_partial=second,
            final_average=None,
            recovery_grade=None,
            academic_status=STATUS_IN_PROGRESS,
            official_grade=None,
            recovery_allowed=False,
        )

    average = quantize_grade((first + second) / Decimal("2"))
    if average >= PASSING:
        if recovery is not None:
            raise RecoveryNotAllowedError()
        return CourseGradeResult(
            first_partial=first,
            second_partial=second,
            final_average=average,
            recovery_grade=None,
            academic_status=STATUS_APPROVED,
            official_grade=average,
            recovery_allowed=False,
        )

    if recovery is None:
        return CourseGradeResult(
            first_partial=first,
            second_partial=second,
            final_average=average,
            recovery_grade=None,
            academic_status=STATUS_RECOVERY_PENDING,
            official_grade=average,
            recovery_allowed=True,
        )

    if recovery >= PASSING:
        return CourseGradeResult(
            first_partial=first,
            second_partial=second,
            final_average=average,
            recovery_grade=recovery,
            academic_status=STATUS_APPROVED_RECOVERY,
            official_grade=PASSING,
            recovery_allowed=True,
        )

    return CourseGradeResult(
        first_partial=first,
        second_partial=second,
        final_average=average,
        recovery_grade=recovery,
        academic_status=STATUS_FAILED,
        official_grade=average,
        recovery_allowed=True,
    )
