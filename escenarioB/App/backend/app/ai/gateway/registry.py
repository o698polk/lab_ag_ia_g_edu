"""Definiciones OpenAI-style de tools para el agente IA."""

from __future__ import annotations

import copy

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "system_stats",
            "description": "Estadísticas globales del sistema (conteos).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "careers_list",
            "description": "Lista carreras.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "is_active": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "careers_get",
            "description": "Obtiene una carrera por id.",
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "careers_create",
            "description": "Crea una carrera (requiere confirmación).",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "duration_semesters": {"type": "integer"},
                },
                "required": ["code", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "subjects_list",
            "description": "Lista materias del alcance del usuario (docente: solo las que imparte).",
            "parameters": {
                "type": "object",
                "properties": {"career_id": {"type": "integer"}, "page": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terms_list",
            "description": "Lista periodos académicos visibles.",
            "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "courses_list",
            "description": "Lista cursos/paralelos del usuario (docente: materias que imparte).",
            "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "students_list",
            "description": "Lista estudiantes visibles.",
            "parameters": {
                "type": "object",
                "properties": {"career_id": {"type": "integer"}, "page": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "teachers_list",
            "description": "Lista docentes.",
            "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enrollments_list",
            "description": "Lista matrículas.",
            "parameters": {
                "type": "object",
                "properties": {"course_id": {"type": "integer"}, "page": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enrollments_create",
            "description": "Matricula un estudiante en un curso (requiere confirmación).",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "course_id": {"type": "integer"},
                    "status": {"type": "string"},
                },
                "required": ["student_id", "course_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grades_list",
            "description": "Lista notas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "student_id": {"type": "integer"},
                    "page": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grades_upsert",
            "description": "Crea o actualiza nota (requiere confirmación).",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "course_id": {"type": "integer"},
                    "partial1": {"type": "number"},
                    "partial2": {"type": "number"},
                    "supplementary": {"type": "number"},
                },
                "required": ["student_id", "course_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "attendance_list",
            "description": "Lista registros de asistencia.",
            "parameters": {
                "type": "object",
                "properties": {"course_id": {"type": "integer"}, "page": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "attendance_upsert",
            "description": "Registra asistencia de un estudiante (requiere confirmación).",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "course_id": {"type": "integer"},
                    "session_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "status": {"type": "string", "enum": ["presente", "ausente", "tardanza", "justificada"]},
                    "notes": {"type": "string"},
                },
                "required": ["student_id", "course_id", "session_date", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "users_list",
            "description": "Lista usuarios (sin passwords).",
            "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roles_list",
            "description": "Lista roles del sistema.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "users_assign_roles",
            "description": "Asigna roles a un usuario (requiere confirmación).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"},
                    "role_codes": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["user_id", "role_codes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "privileges_request_elevation",
            "description": "Solicita elevación de permisos a administradores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permissions": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["permissions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reports_list_types",
            "description": "Lista tipos de reportes disponibles para el usuario.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reports_generate",
            "description": (
                "Genera reporte descargable (pdf, xlsx, json, md). "
                "Para materias/cursos del docente use report_type=courses; "
                "para alumnos de sus cursos use students; notas=grades."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": [
                            "grades",
                            "attendance",
                            "enrollments",
                            "students",
                            "courses",
                            "subjects",
                        ],
                    },
                    "format": {"type": "string", "enum": ["pdf", "xlsx", "json", "md"]},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "term_id": {"type": "integer"},
                            "career_id": {"type": "integer"},
                            "course_id": {"type": "integer"},
                            "status": {"type": "string"},
                        },
                    },
                },
                "required": ["report_type", "format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audit_logs_list",
            "description": "Lista auditoría reciente.",
            "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}},
        },
    },
]


def _can_system_stats(user) -> bool:
    if "ADMIN" in (user.get_role_codes() or []):
        return True
    return any(
        user.has_permission(p)
        for p in ("dashboard.view", "reports.view", "users.view")
    )


def tools_for_user(user) -> list:
    """
    SPEC-030: solo schemas de tools permitidas para el rol/permisos del usuario.
    """
    from app.ai.gateway.handlers import HANDLERS
    from app.services.ai_reports import REPORT_TYPES, user_can_report

    allowed_report_types = [code for code in REPORT_TYPES if user_can_report(user, code)]
    out = []
    for schema in TOOL_SCHEMAS:
        name = schema.get("function", {}).get("name")
        if not name:
            continue
        entry = HANDLERS.get(name)
        if not entry:
            continue
        _handler, perm, _mutating = entry

        if name == "system_stats":
            if not _can_system_stats(user):
                continue
            out.append(schema)
            continue

        if name in ("reports_generate", "reports_list_types"):
            if not allowed_report_types:
                continue
            if name == "reports_generate":
                cloned = copy.deepcopy(schema)
                cloned["function"]["parameters"]["properties"]["report_type"]["enum"] = (
                    allowed_report_types
                )
                out.append(cloned)
            else:
                out.append(schema)
            continue

        if perm and not user.has_permission(perm) and "ADMIN" not in (user.get_role_codes() or []):
            continue
        out.append(schema)
    return out
