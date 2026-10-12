def validate_grade_value(value):
    if value is None:
        return True, None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, "La nota debe ser numérica"
    if v < 1 or v > 10:
        return False, "La nota debe estar entre 1 y 10"
    return True, v


def apply_grade_rules(grade, partial1=None, partial2=None, supplementary=None):
    """Aplica reglas SPEC-004: promedio, supletorio si < 7.0."""
    if partial1 is not None:
        ok, v = validate_grade_value(partial1)
        if not ok:
            raise ValueError(v)
        grade.partial1 = v
    if partial2 is not None:
        ok, v = validate_grade_value(partial2)
        if not ok:
            raise ValueError(v)
        grade.partial2 = v

    avg = None
    if grade.partial1 is not None and grade.partial2 is not None:
        avg = (grade.partial1 + grade.partial2) / 2.0

    if supplementary is not None:
        if avg is None or avg >= 7.0:
            raise ValueError("Supletorio solo permitido si el promedio es menor a 7.0")
        ok, v = validate_grade_value(supplementary)
        if not ok:
            raise ValueError(v)
        grade.supplementary = v

    grade.compute()
    return grade
