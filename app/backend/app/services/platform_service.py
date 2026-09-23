# Ref: BL-O5-* | Skill: K-023/K-021/K-016 | Fase: F6
"""Dashboard, reports, notifications, user history (≠ technical audit)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AttendanceRecord,
    AttendanceSession,
    Career,
    Course,
    Enrollment,
    Grade,
    KardexEntry,
    Notification,
    Report,
    ReportLog,
    Student,
    Teacher,
    TeachingAssignment,
    User,
    UserHistoryEvent,
)
from app.services.role_service import AuthorizationError


REPORT_TYPES = {
    "students": "Reporte de estudiantes",
    "teachers": "Reporte de docentes",
    "enrollments": "Reporte de matrícula",
    "attendance": "Reporte de asistencia",
    "grades": "Reporte de calificaciones",
    "averages": "Reporte de promedios",
    "failure": "Reporte de reprobación",
    "kardex": "Reporte de Kardex",
    "teacher_load": "Reporte de carga docente",
    "term_academic": "Reporte académico por periodo",
    "career": "Reporte por carrera",
}

VALID_FORMATS = {"HTML", "CSV", "JSON", "PDF"}
VALID_NTF_TYPES = {"INFO", "WARNING", "SUCCESS", "ALERT", "SECURITY", "ACADEMIC"}


def _pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def _render_pdf(rows: list[dict], title: str) -> str:
    """Minimal PDF 1.4 (no extra deps) for lab export."""
    lines = [title, ""]
    if not rows:
        lines.append("Sin datos")
    else:
        headers = list(rows[0].keys())
        lines.append(" | ".join(str(h) for h in headers))
        for row in rows[:80]:
            lines.append(" | ".join(str(row.get(h, ""))[:40] for h in headers))
    cmds = ["BT", "/F1 9 Tf"]
    y = 800
    for line in lines:
        cmds.append(f"1 0 0 1 36 {y} Tm ({_pdf_escape(line[:120])}) Tj")
        y -= 12
        if y < 40:
            break
    cmds.append("ET")
    stream = "\n".join(cmds).encode("latin-1", "replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        b"4 0 obj << /Length "
        + str(len(stream)).encode()
        + b" >> stream\n"
        + stream
        + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return out.decode("latin-1")


class PlatformService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_report_catalog(self) -> None:
        for code, name in REPORT_TYPES.items():
            if not self.db.scalar(select(Report).where(Report.code == code)):
                self.db.add(Report(code=code, name=name, description=name, is_active=True))
        self.db.commit()

    def list_report_catalog(self) -> list[Report]:
        self.ensure_report_catalog()
        return list(
            self.db.scalars(select(Report).where(Report.is_active.is_(True)).order_by(Report.code))
        )

    # --- User history (≠ audit_events) ---
    def record_history(
        self,
        *,
        user_id: int,
        action: str,
        summary: str,
        module: str = "platform",
        metadata: Optional[dict] = None,
    ) -> UserHistoryEvent:
        event = UserHistoryEvent(
            user_id=user_id,
            action=action,
            module=module,
            summary=summary,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_history(self, user_id: int, *, limit: int = 50) -> Sequence[UserHistoryEvent]:
        return list(
            self.db.scalars(
                select(UserHistoryEvent)
                .where(UserHistoryEvent.user_id == user_id)
                .order_by(UserHistoryEvent.id.desc())
                .limit(limit)
            )
        )

    # --- Notifications ---
    def create_notification(
        self,
        *,
        user_id: int,
        type_: str,
        title: str,
        body: Optional[str] = None,
    ) -> Notification:
        if type_ not in VALID_NTF_TYPES:
            raise ValueError("INVALID_NOTIFICATION_TYPE")
        user = self.db.get(User, user_id)
        if user is None:
            raise LookupError("USER_NOT_FOUND")
        ntf = Notification(user_id=user_id, type=type_, title=title, body=body)
        self.db.add(ntf)
        self.db.commit()
        self.db.refresh(ntf)
        return ntf

    def list_notifications(self, user_id: int, *, unread_only: bool = False) -> Sequence[Notification]:
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.read_flag.is_(False))
        return list(self.db.scalars(q.order_by(Notification.id.desc())))

    def mark_read(self, *, notification_id: int, user_id: int) -> Notification:
        ntf = self.db.get(Notification, notification_id)
        if ntf is None:
            raise LookupError("NOTIFICATION_NOT_FOUND")
        if ntf.user_id != user_id:
            raise AuthorizationError("RESOURCE_NOT_OWNED")
        ntf.read_flag = True
        self.db.commit()
        self.db.refresh(ntf)
        return ntf

    # --- Dashboard ---
    def dashboard_for(self, *, user: User, roles: list[str]) -> dict[str, Any]:
        if "ADMINISTRATOR" in roles:
            view = "ADMINISTRATOR"
            indicators = {
                "students": self._count(Student, Student.deleted_at.is_(None)),
                "teachers": self._count(Teacher, Teacher.deleted_at.is_(None)),
                "courses": self._count(Course),
                "enrollments": self._count(Enrollment, Enrollment.status == "ACTIVE"),
                "users": self._count(User, User.deleted_at.is_(None)),
                "grades": self._count(Grade),
                "attendance_sessions": self._count(AttendanceSession),
                "careers": self._count(Career),
                "unread_notifications": self._count(
                    Notification,
                    Notification.user_id == user.id,
                    Notification.read_flag.is_(False),
                ),
            }
        elif "TEACHER" in roles:
            view = "TEACHER"
            teacher = self.db.scalar(select(Teacher).where(Teacher.user_id == user.id))
            assigned = 0
            students = 0
            if teacher:
                assigned = self._count(
                    TeachingAssignment,
                    TeachingAssignment.teacher_id == teacher.id,
                    TeachingAssignment.status == "ACTIVE",
                )
                course_ids = list(
                    self.db.scalars(
                        select(TeachingAssignment.course_id).where(
                            TeachingAssignment.teacher_id == teacher.id,
                            TeachingAssignment.status == "ACTIVE",
                        )
                    )
                )
                if course_ids:
                    students = self._count(
                        Enrollment,
                        Enrollment.course_id.in_(course_ids),
                        Enrollment.status == "ACTIVE",
                    )
            indicators = {
                "assigned_courses": assigned,
                "students": students,
                "grades_recorded": self._count(Grade),
                "unread_notifications": self._count(
                    Notification,
                    Notification.user_id == user.id,
                    Notification.read_flag.is_(False),
                ),
            }
        else:
            view = "STUDENT"
            student = self.db.scalar(select(Student).where(Student.user_id == user.id))
            my_courses = 0
            my_grades = 0
            my_kardex = 0
            if student:
                my_courses = self._count(
                    Enrollment,
                    Enrollment.student_id == student.id,
                    Enrollment.status == "ACTIVE",
                )
                my_grades = self._count(Grade, Grade.student_id == student.id)
                my_kardex = self._count(KardexEntry, KardexEntry.student_id == student.id)
            indicators = {
                "my_courses": my_courses,
                "my_grades": my_grades,
                "my_kardex": my_kardex,
                "unread_notifications": self._count(
                    Notification,
                    Notification.user_id == user.id,
                    Notification.read_flag.is_(False),
                ),
            }

        self.record_history(
            user_id=user.id,
            action="dashboard.view",
            summary=f"Dashboard {view}",
            module="dashboard",
        )
        return {"role_view": view, "indicators": indicators}

    def _count(self, model, *filters) -> int:
        q = select(func.count()).select_from(model)
        for f in filters:
            q = q.where(f)
        return int(self.db.scalar(q) or 0)

    # --- Reports ---
    def generate_report(
        self,
        *,
        user: User,
        report_type: str,
        format_: str,
        parameters: Optional[dict] = None,
    ) -> dict[str, Any]:
        self.ensure_report_catalog()
        report_type = report_type.lower().strip()
        format_ = format_.upper().strip()
        if report_type not in REPORT_TYPES:
            raise ValueError("INVALID_REPORT_TYPE")
        if format_ not in VALID_FORMATS:
            raise ValueError("INVALID_FORMAT")

        rows = self._collect_rows(report_type, parameters or {})
        content = self._render(rows, format_, report_type)
        report = self.db.scalar(select(Report).where(Report.code == report_type))
        log = ReportLog(
            user_id=user.id,
            report_id=report.id if report else None,
            report_type=report_type,
            format=format_,
            parameters=json.dumps(parameters or {}),
            result_status="SUCCESS",
            row_count=len(rows),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        self.record_history(
            user_id=user.id,
            action="reports.generate",
            summary=f"Generated {report_type} as {format_}",
            module="reports",
            metadata={"log_id": log.id, "rows": len(rows)},
        )
        return {
            "log_id": log.id,
            "report_type": report_type,
            "format": format_,
            "result_status": log.result_status,
            "row_count": log.row_count,
            "content": content,
        }

    def list_report_logs(self, *, user_id: Optional[int] = None) -> Sequence[ReportLog]:
        q = select(ReportLog).order_by(ReportLog.id.desc()).limit(100)
        if user_id is not None:
            q = q.where(ReportLog.user_id == user_id)
        return list(self.db.scalars(q))

    def _collect_rows(self, report_type: str, params: dict) -> list[dict[str, Any]]:
        if report_type == "students":
            return [
                {
                    "id": s.id,
                    "student_code": s.student_code,
                    "user_id": s.user_id,
                    "status": s.status,
                }
                for s in self.db.scalars(
                    select(Student).where(Student.deleted_at.is_(None))
                )
            ]
        if report_type == "teachers":
            return [
                {
                    "id": t.id,
                    "teacher_code": t.teacher_code,
                    "user_id": t.user_id,
                    "status": t.status,
                }
                for t in self.db.scalars(
                    select(Teacher).where(Teacher.deleted_at.is_(None))
                )
            ]
        if report_type == "enrollments":
            return [
                {
                    "id": e.id,
                    "student_id": e.student_id,
                    "course_id": e.course_id,
                    "term_id": e.term_id,
                    "status": e.status,
                }
                for e in self.db.scalars(select(Enrollment))
            ]
        if report_type == "attendance":
            return [
                {
                    "session_id": r.session_id,
                    "student_id": r.student_id,
                    "status": r.status,
                }
                for r in self.db.scalars(select(AttendanceRecord))
            ]
        if report_type == "grades":
            return [
                {
                    "id": g.id,
                    "evaluation_id": g.evaluation_id,
                    "student_id": g.student_id,
                    "score": str(g.score),
                }
                for g in self.db.scalars(select(Grade))
            ]
        if report_type == "averages":
            rows = self.db.execute(
                select(Grade.student_id, func.avg(Grade.score)).group_by(Grade.student_id)
            ).all()
            return [
                {"student_id": sid, "average": str(round(float(avg), 2)) if avg is not None else "0"}
                for sid, avg in rows
            ]
        if report_type == "failure":
            return [
                {
                    "id": k.id,
                    "student_id": k.student_id,
                    "subject_id": k.subject_id,
                    "final_grade": str(k.final_grade) if k.final_grade is not None else None,
                    "academic_status": k.academic_status,
                }
                for k in self.db.scalars(
                    select(KardexEntry).where(KardexEntry.academic_status == "FAILED")
                )
            ]
        if report_type == "kardex":
            q = select(KardexEntry)
            if "student_id" in params:
                q = q.where(KardexEntry.student_id == int(params["student_id"]))
            return [
                {
                    "id": k.id,
                    "student_id": k.student_id,
                    "term_id": k.term_id,
                    "subject_id": k.subject_id,
                    "final_grade": str(k.final_grade) if k.final_grade is not None else None,
                    "academic_status": k.academic_status,
                }
                for k in self.db.scalars(q)
            ]
        if report_type == "teacher_load":
            rows = self.db.execute(
                select(TeachingAssignment.teacher_id, func.count())
                .where(TeachingAssignment.status == "ACTIVE")
                .group_by(TeachingAssignment.teacher_id)
            ).all()
            return [{"teacher_id": tid, "active_courses": cnt} for tid, cnt in rows]
        if report_type == "term_academic":
            term_id = params.get("term_id")
            q = select(Enrollment)
            if term_id is not None:
                q = q.where(Enrollment.term_id == int(term_id))
            return [
                {
                    "id": e.id,
                    "student_id": e.student_id,
                    "course_id": e.course_id,
                    "term_id": e.term_id,
                    "status": e.status,
                }
                for e in self.db.scalars(q)
            ]
        if report_type == "career":
            return [
                {
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                    "status": c.status,
                    "students": self._count(
                        Student,
                        Student.career_id == c.id,
                        Student.deleted_at.is_(None),
                    ),
                }
                for c in self.db.scalars(select(Career))
            ]
        return []

    def _render(self, rows: list[dict], format_: str, report_type: str) -> str:
        if format_ == "JSON":
            return json.dumps(rows, ensure_ascii=False, indent=2)
        if format_ == "CSV":
            if not rows:
                return ""
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
            return buf.getvalue()
        if format_ == "PDF":
            return _render_pdf(rows, REPORT_TYPES.get(report_type, report_type))
        # HTML
        title = REPORT_TYPES.get(report_type, report_type)
        if not rows:
            return f"<html><body><h1>{title}</h1><p>Sin datos</p></body></html>"
        headers = list(rows[0].keys())
        th = "".join(f"<th>{h}</th>" for h in headers)
        trs = []
        for row in rows:
            tds = "".join(f"<td>{row.get(h, '')}</td>" for h in headers)
            trs.append(f"<tr>{tds}</tr>")
        return (
            f"<html><body><h1>{title}</h1>"
            f"<table border='1'><thead><tr>{th}</tr></thead>"
            f"<tbody>{''.join(trs)}</tbody></table></body></html>"
        )
