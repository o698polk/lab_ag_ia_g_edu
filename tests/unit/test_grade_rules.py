# Ref: RF-GRD | Skill: K-006 | Fase: calificaciones
"""Pure academic grade-rule tests."""

from decimal import Decimal

import pytest

from app.services.grade_rules import (
    STATUS_APPROVED,
    STATUS_APPROVED_RECOVERY,
    STATUS_FAILED,
    STATUS_RECOVERY_PENDING,
    RecoveryNotAllowedError,
    resolve_course_grade,
)


@pytest.mark.unit
def test_direct_pass_keeps_recovery_null():
    result = resolve_course_grade("8.50", "9.00", None)
    assert result.final_average == Decimal("8.75")
    assert result.academic_status == STATUS_APPROVED
    assert result.recovery_grade is None
    assert result.official_grade == Decimal("8.75")
    assert result.recovery_allowed is False


@pytest.mark.unit
def test_integer_and_decimal_partials():
    result = resolve_course_grade(10, "7.25", None)
    assert result.final_average == Decimal("8.63")
    assert result.academic_status == STATUS_APPROVED


@pytest.mark.unit
def test_average_below_seven_is_pending_without_recovery():
    result = resolve_course_grade("6.00", "6.50", None)
    assert result.final_average == Decimal("6.25")
    assert result.academic_status == STATUS_RECOVERY_PENDING
    assert result.recovery_allowed is True
    assert result.recovery_grade is None


@pytest.mark.unit
def test_recovery_pass_caps_official_grade_at_seven():
    result = resolve_course_grade("6.00", "6.50", "7.50")
    assert result.final_average == Decimal("6.25")
    assert result.recovery_grade == Decimal("7.50")
    assert result.academic_status == STATUS_APPROVED_RECOVERY
    assert result.official_grade == Decimal("7.00")


@pytest.mark.unit
def test_recovery_fail_is_reprobado():
    result = resolve_course_grade("5.50", "6.00", "6.25")
    assert result.final_average == Decimal("5.75")
    assert result.academic_status == STATUS_FAILED
    assert result.official_grade == Decimal("5.75")


@pytest.mark.unit
def test_cannot_register_recovery_when_already_passing():
    with pytest.raises(RecoveryNotAllowedError):
        resolve_course_grade("8.00", "8.00", "9.00")


@pytest.mark.unit
def test_recovery_below_seven_cannot_approve():
    result = resolve_course_grade("5.00", "5.00", "6.99")
    assert result.academic_status == STATUS_FAILED
    assert result.academic_status != STATUS_APPROVED_RECOVERY
