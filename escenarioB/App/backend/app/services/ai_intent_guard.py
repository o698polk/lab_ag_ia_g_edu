"""SPEC-030: detección de solicitudes NL no autorizadas según permisos del rol."""

from __future__ import annotations

import re


def _has_any(user, perms: tuple[str, ...]) -> bool:
    if "ADMIN" in (user.get_role_codes() or []):
        return True
    return any(user.has_permission(p) for p in perms)


def _is_course_scoped(user) -> bool:
    """True si el usuario está limitado a cursos propios (TEACHER/STUDENT tipicos)."""
    from app.services.visibility import owned_course_ids

    return owned_course_ids(user) is not None


# (nombre, patrones, permisos_any, solo_si_scoped_y_pide_institucional)
_INTENT_RULES: list[tuple[str, list[re.Pattern], tuple[str, ...]]] = [
    (
        "users_directory",
        [
            re.compile(
                r"(reporte|listado|lista|exporta\w*|descarga\w*|excel|xlsx|pdf).{0,60}"
                r"(todos\s+los\s+)?usuarios",
                re.I,
            ),
            re.compile(
                r"(todos\s+los\s+)?usuarios\s+(del\s+)?(sistema|plataforma|instituci[oó]n)",
                re.I,
            ),
            re.compile(
                r"(list|export|report|download).{0,40}(all\s+)?users",
                re.I,
            ),
            re.compile(r"\busuarios\s+registrados\b", re.I),
        ],
        ("users.view", "reports.export"),
    ),
    (
        "roles_catalog",
        [
            re.compile(
                r"(lista|listado|muestra|muéstrame|muestrame|dame|ver).{0,40}\broles?\b",
                re.I,
            ),
            re.compile(r"(todos\s+los\s+)?roles\s+(del\s+)?sistema", re.I),
        ],
        ("roles.view",),
    ),
    (
        "audit_logs",
        [
            re.compile(
                r"(auditor[ií]a|audit\s*logs?|logs?\s+de\s+auditor[ií]a)",
                re.I,
            ),
        ],
        ("audit.view",),
    ),
    (
        "teachers_directory",
        [
            re.compile(
                r"(reporte|listado|lista|exporta\w*).{0,50}"
                r"(todos\s+los\s+)?(docentes|profesores|teachers)",
                re.I,
            ),
            re.compile(
                r"(todos\s+los\s+)?(docentes|profesores)\s+(del\s+)?"
                r"(sistema|instituci[oó]n)",
                re.I,
            ),
        ],
        ("teachers.view", "reports.export"),
    ),
    (
        "institution_students_export",
        [
            re.compile(
                r"(reporte|listado|lista|exporta\w*|excel|xlsx).{0,50}"
                r"(todos\s+los\s+)?estudiantes\s+(del\s+)?"
                r"(sistema|instituci[oó]n|colegio|universidad)",
                re.I,
            ),
            re.compile(
                r"(todos\s+los\s+estudiantes)\s+(del\s+)?"
                r"(sistema|instituci[oó]n)",
                re.I,
            ),
        ],
        ("reports.export", "students.view"),
    ),
]


# SPEC-031: pedidos del propio ámbito docente (no directorio institucional)
_OWN_SCOPE_HINT = re.compile(
    r"\b("
    r"mi\s+materia|mis\s+materias|mi\s+curso|mis\s+cursos|"
    r"mis\s+estudiantes|estudiantes\s+de\s+mi|"
    r"doy\s+clase|que\s+dicto|en\s+mi\s+materia|de\s+mi\s+materia|"
    r"en\s+mi\s+curso|de\s+mi\s+curso"
    r")\b",
    re.I,
)


def scan_unauthorized_intent(user, message: str) -> dict | None:
    """
    Si el mensaje pide datos/acciones fuera de permiso, retorna info de bloqueo.
    None = continuar (el executor/IAM siguen aplicando).
    """
    raw = (message or "").strip()
    if not raw:
        return None

    own_scope = bool(_OWN_SCOPE_HINT.search(raw))

    for intent, patterns, perms in _INTENT_RULES:
        matched = None
        for pat in patterns:
            m = pat.search(raw)
            if m:
                matched = m.group(0)[:120]
                break
        if not matched:
            continue

        # «usuarios/estudiantes de mi materia» ≠ directorio del sistema
        if intent in ("users_directory", "institution_students_export") and own_scope:
            continue

        # Estudiantes institucionales: si solo tiene students.view y está scoped,
        # bloquear pedidos "del sistema"; permitir "mis estudiantes" (no matchea estos patrones).
        if intent == "institution_students_export":
            if _has_any(user, ("reports.export",)) or (
                user.has_permission("students.view") and not _is_course_scoped(user)
            ):
                continue
            return {
                "blocked": True,
                "kind": "unauthorized_intent",
                "intent": intent,
                "required": list(perms),
                "matched": matched,
                "reason": (
                    "Solicitud de directorio institucional de estudiantes sin permiso "
                    "de exportación / alcance suficiente (mínimo privilegio)"
                ),
            }

        if _has_any(user, perms):
            continue

        return {
            "blocked": True,
            "kind": "unauthorized_intent",
            "intent": intent,
            "required": list(perms),
            "matched": matched,
            "reason": (
                "Solicitud fuera de los permisos del rol actual "
                f"(se requiere alguno de: {', '.join(perms)})"
            ),
        }

    return None
