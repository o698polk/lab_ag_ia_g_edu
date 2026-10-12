"""Generación de reportes para el agente IA (PDF, XLSX, JSON, MD)."""

import json
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.models import AIArtifact, AIConversation
from app.services.reports import (
    attendance_rows,
    courses_rows,
    enrollments_rows,
    filter_attendance,
    filter_courses,
    filter_enrollments,
    filter_grades,
    filter_students,
    filter_subjects,
    grades_rows,
    pdf_from_rows,
    students_rows,
    subjects_rows,
    workbook_from_rows,
)

class _ArgMap:
    """Adaptador dict → interfaz tipo request.args para reports.py."""

    def __init__(self, data):
        self._data = data or {}

    def get(self, key, default=None, type=None):
        if key not in self._data:
            return default
        v = self._data.get(key)
        if v is None or v == "":
            return default
        if type:
            try:
                return type(v)
            except (TypeError, ValueError):
                return default
        return v


REPORT_TYPES = {
    "grades": {
        "filter": filter_grades,
        "rows": grades_rows,
        "title": "Reporte de Notas",
        "perm": ("reports.export", "grades.view"),
        "widths": [85, 45, 95, 55, 30, 30, 30, 35, 45],
    },
    "attendance": {
        "filter": filter_attendance,
        "rows": attendance_rows,
        "title": "Reporte de Asistencia",
        "perm": ("reports.export", "attendance.view"),
        "widths": [120, 120, 70, 60, 120],
    },
    "enrollments": {
        "filter": filter_enrollments,
        "rows": enrollments_rows,
        "title": "Reporte de Matrículas",
        "perm": ("reports.export", "enrollments.view"),
        "widths": [35, 110, 120, 70, 55, 60],
    },
    "students": {
        "filter": filter_students,
        "rows": students_rows,
        "title": "Reporte de Estudiantes",
        "perm": ("reports.export", "students.view"),
        "widths": [55, 110, 120, 100, 60, 45],
    },
    # SPEC-031: materias/cursos del docente (scope vía filter_courses)
    "courses": {
        "filter": filter_courses,
        "rows": courses_rows,
        "title": "Reporte de Cursos y Materias",
        "perm": ("reports.export", "courses.view"),
        "widths": [55, 120, 100, 80, 35, 40, 40],
    },
    "subjects": {
        "filter": filter_subjects,
        "rows": subjects_rows,
        "title": "Reporte de Materias",
        "perm": ("reports.export", "subjects.view"),
        "widths": [55, 120, 40, 100, 40],
    },
}


def user_can_report(user, report_type: str) -> bool:
    cfg = REPORT_TYPES.get(report_type)
    if not cfg:
        return False
    if "ADMIN" in user.get_role_codes():
        return True
    perms = user.get_permissions()
    return any(p in perms for p in cfg["perm"])


def _artifact_dir() -> Path:
    path = Path(current_app.instance_path) / "ai_artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rows_to_md(title: str, headers, rows) -> str:
    lines = [f"# {title}", "", f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC", ""]
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c if c is not None else "") for c in row) + " |")
    return "\n".join(lines)


def generate_report_artifact(user, report_type: str, fmt: str, filters: dict, conversation_id=None):
    fmt = (fmt or "xlsx").lower()
    if fmt not in ("pdf", "xlsx", "json", "md"):
        raise ValueError("Formato no soportado. Use pdf, xlsx, json o md.")
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Tipo de reporte inválido: {report_type}")
    if not user_can_report(user, report_type):
        raise PermissionError("Sin permiso para generar este reporte")

    cfg = REPORT_TYPES[report_type]
    items = cfg["filter"](user, _ArgMap(filters or {}))
    headers, rows = cfg["rows"](items)
    title = cfg["title"]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = f"{report_type}_{ts}"

    artifact_dir = _artifact_dir()
    if fmt == "xlsx":
        buf = workbook_from_rows(title[:31], headers, rows)
        filename = f"{base}.xlsx"
        path = artifact_dir / filename
        path.write_bytes(buf.getvalue())
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fmt == "pdf":
        # SPEC-025: anchos del catálogo + texto Latin-1 seguro
        buf = pdf_from_rows(title, headers, rows, col_widths=cfg.get("widths"))
        filename = f"{base}.pdf"
        path = artifact_dir / filename
        path.write_bytes(buf.getvalue())
        mime = "application/pdf"
    elif fmt == "json":
        payload = {
            "title": title,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": filters or {},
            "headers": headers,
            "rows": [list(r) for r in rows],
            "count": len(rows),
        }
        filename = f"{base}.json"
        path = artifact_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        mime = "application/json"
    else:
        md = _rows_to_md(title, headers, rows)
        filename = f"{base}.md"
        path = artifact_dir / filename
        path.write_text(md, encoding="utf-8")
        mime = "text/markdown"

    conv_id = None
    if conversation_id and AIConversation.query.get(conversation_id):
        conv_id = conversation_id

    artifact = AIArtifact(
        conversation_id=conv_id,
        user_id=user.id,
        format=fmt,
        report_type=report_type,
        filename=filename,
        storage_path=str(path),
        filters=filters or {},
    )
    db.session.add(artifact)
    db.session.commit()
    return artifact, mime
