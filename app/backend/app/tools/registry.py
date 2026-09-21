# Ref: BL-O6-003 | Skill: K-019 | Fase: F6
"""In-code Tool Registry metadata (seeded to DB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolMeta:
    tool_name: str
    description: str
    method: str
    endpoint: str
    parameters_schema: dict[str, Any]
    required_permissions: list[str]
    allowed_roles: list[str]
    resource_type: str
    risk_level: str  # LOW|MED|HIGH
    is_active: bool = True


TOOLS: dict[str, ToolMeta] = {
    "get_student_profile": ToolMeta(
        tool_name="get_student_profile",
        description="Consultar perfil de estudiante",
        method="GET",
        endpoint="/api/v1/students/{id}",
        parameters_schema={"student_id": "int|CURRENT_USER"},
        required_permissions=["students.view"],
        allowed_roles=["ADMINISTRATOR", "TEACHER", "STUDENT"],
        resource_type="student",
        risk_level="LOW",
    ),
    "get_grades": ToolMeta(
        tool_name="get_grades",
        description="Consultar calificaciones",
        method="GET",
        endpoint="/api/v1/grades",
        parameters_schema={"student_id": "int|CURRENT_USER"},
        required_permissions=["grades.view"],
        allowed_roles=["ADMINISTRATOR", "TEACHER", "STUDENT"],
        resource_type="grade",
        risk_level="LOW",
    ),
    "get_attendance": ToolMeta(
        tool_name="get_attendance",
        description="Consultar asistencia",
        method="GET",
        endpoint="/api/v1/attendance",
        parameters_schema={"student_id": "int|CURRENT_USER", "course_id": "int?"},
        required_permissions=["attendance.view"],
        allowed_roles=["ADMINISTRATOR", "TEACHER", "STUDENT"],
        resource_type="attendance",
        risk_level="LOW",
    ),
    "get_kardex": ToolMeta(
        tool_name="get_kardex",
        description="Consultar kardex",
        method="GET",
        endpoint="/api/v1/kardex",
        parameters_schema={"student_id": "int|CURRENT_USER"},
        required_permissions=["kardex.view"],
        allowed_roles=["ADMINISTRATOR", "STUDENT"],
        resource_type="kardex",
        risk_level="LOW",
    ),
    "get_schedule": ToolMeta(
        tool_name="get_schedule",
        description="Consultar horarios",
        method="GET",
        endpoint="/api/v1/schedules",
        parameters_schema={},
        required_permissions=["schedules.view"],
        allowed_roles=["ADMINISTRATOR", "TEACHER", "STUDENT"],
        resource_type="schedule",
        risk_level="LOW",
    ),
    "generate_report": ToolMeta(
        tool_name="generate_report",
        description="Generar reporte académico",
        method="POST",
        endpoint="/api/v1/reports",
        parameters_schema={"report_type": "str", "format": "str"},
        required_permissions=["reports.generate"],
        allowed_roles=["ADMINISTRATOR", "TEACHER"],
        resource_type="report",
        risk_level="MED",
    ),
    "update_grade": ToolMeta(
        tool_name="update_grade",
        description="Modificar calificación (sensible)",
        method="PUT",
        endpoint="/api/v1/grades",
        parameters_schema={
            "evaluation_id": "int",
            "student_id": "int",
            "score": "number",
        },
        required_permissions=["grades.update"],
        allowed_roles=["TEACHER", "ADMINISTRATOR"],
        resource_type="grade",
        risk_level="HIGH",
    ),
    "update_attendance": ToolMeta(
        tool_name="update_attendance",
        description="Modificar asistencia (sensible)",
        method="PUT",
        endpoint="/api/v1/attendance/records",
        parameters_schema={"session_id": "int", "student_id": "int", "status": "str"},
        required_permissions=["attendance.update"],
        allowed_roles=["TEACHER", "ADMINISTRATOR"],
        resource_type="attendance",
        risk_level="HIGH",
    ),
    "create_enrollment": ToolMeta(
        tool_name="create_enrollment",
        description="Crear matrícula (sensible)",
        method="POST",
        endpoint="/api/v1/enrollments",
        parameters_schema={"student_id": "int", "course_id": "int", "term_id": "int"},
        required_permissions=["enrollments.create"],
        allowed_roles=["ADMINISTRATOR"],
        resource_type="enrollment",
        risk_level="HIGH",
    ),
    "cancel_enrollment": ToolMeta(
        tool_name="cancel_enrollment",
        description="Cancelar matrícula (sensible)",
        method="POST",
        endpoint="/api/v1/enrollments/{id}/cancel",
        parameters_schema={"enrollment_id": "int"},
        required_permissions=["enrollments.cancel"],
        allowed_roles=["ADMINISTRATOR"],
        resource_type="enrollment",
        risk_level="HIGH",
    ),
}


def get_tool(name: str) -> Optional[ToolMeta]:
    return TOOLS.get(name)


def list_tools() -> list[ToolMeta]:
    return [t for t in TOOLS.values() if t.is_active]
