from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.ai.conversations import (
    archive_conversation,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_or_create_active,
    list_user_conversations,
    open_conversation,
    rename_conversation,
)
from app.ai.gateway import run_agent_chat
from app.extensions import db, limiter
from app.models import (
    AIArtifact,
    AIConfig,
    AIConversation,
    AILog,
    Attendance,
    AuditLog,
    Course,
    Enrollment,
    Grade,
    Notification,
    Permission,
    Role,
    Student,
    SystemConfig,
    Teacher,
    User,
)
from app.permissions.decorators import any_permission_required, get_current_user, permission_required
from app.services.audit import log_event
from app.services.crypto import encrypt_value

system_bp = Blueprint("system", __name__, url_prefix="/api/v1")


# ─── Dashboard ─────────────────────────────────────────────
@system_bp.get("/dashboard")
@jwt_required()
@permission_required("dashboard.view")
def dashboard():
    return jsonify(
        {
            "students": Student.query.count(),
            "teachers": Teacher.query.count(),
            "courses": Course.query.count(),
            "enrollments_active": Enrollment.query.filter_by(status="activa").count(),
            "users_active": User.query.filter_by(is_active=True).count(),
            "grades_pending": Grade.query.filter(Grade.final_grade.is_(None)).count(),
        }
    )


# ─── Roles & Permissions ───────────────────────────────────
@system_bp.get("/roles")
@jwt_required()
@permission_required("roles.view")
def list_roles():
    return jsonify([r.to_dict() for r in Role.query.all()])


@system_bp.get("/permissions")
@jwt_required()
@permission_required("permissions.view")
def list_permissions():
    return jsonify([p.to_dict() for p in Permission.query.order_by(Permission.module).all()])


@system_bp.put("/roles/<int:rid>/permissions")
@jwt_required()
@permission_required("permissions.assign")
def assign_permissions(rid):
    role = Role.query.get_or_404(rid)
    data = request.get_json(silent=True) or {}
    codes = data.get("permissions", [])
    perms = []
    for code in codes:
        if "." not in code:
            continue
        module, action = code.split(".", 1)
        p = Permission.query.filter_by(module=module, action=action).first()
        if p:
            perms.append(p)
    role.permissions = perms
    db.session.commit()
    log_event(get_current_user().id, "PERMISSIONS_ASSIGN", "permissions", f"role={role.code}")
    return jsonify(role.to_dict())


# ─── Notifications ─────────────────────────────────────────
@system_bp.get("/notifications")
@jwt_required()
@permission_required("notifications.view")
def list_notifications():
    user = get_current_user()
    roles = user.get_role_codes()
    items = (
        Notification.query.filter(
            db.or_(
                Notification.user_id == user.id,
                Notification.role_code.in_(roles),
                Notification.user_id.is_(None) & Notification.role_code.is_(None),
            )
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([n.to_dict() for n in items])


@system_bp.post("/notifications")
@jwt_required()
@permission_required("notifications.send")
def send_notification():
    data = request.get_json(silent=True) or {}
    n = Notification(
        user_id=data.get("user_id"),
        role_code=data.get("role_code"),
        title=data["title"],
        message=data["message"],
        created_by=get_current_user().id,
    )
    db.session.add(n)
    db.session.commit()
    return jsonify(n.to_dict()), 201


@system_bp.post("/notifications/<int:nid>/read")
@jwt_required()
@permission_required("notifications.view")
def mark_read(nid):
    n = Notification.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    return jsonify(n.to_dict())


# ─── Audit ─────────────────────────────────────────────────
@system_bp.get("/audit")
@jwt_required()
@permission_required("audit.view")
def list_audit():
    q = AuditLog.query.order_by(AuditLog.created_at.desc())
    module = request.args.get("module")
    action = request.args.get("action")
    user_id = request.args.get("user_id", type=int)
    if module:
        q = q.filter_by(module=module)
    if action:
        q = q.filter_by(action=action)
    if user_id:
        q = q.filter_by(user_id=user_id)
    return jsonify([a.to_dict() for a in q.limit(200).all()])


# ─── System Config ─────────────────────────────────────────
_BRAND_KEYS = (
    "system_name",
    "primary_color",
    "secondary_color",
    "accent_color",
    "default_theme",
)


def _config_map():
    return {c.key: c.value for c in SystemConfig.query.all()}


def _normalize_hex(value, fallback):
    if value is None:
        return fallback
    s = str(value).strip()
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        s = f"#{s}"
    if len(s) == 4 and s.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in s[1:]):
        s = f"#{s[1]*2}{s[2]*2}{s[3]*2}"
    if len(s) == 7 and s.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in s[1:]):
        return s.lower()
    return fallback


@system_bp.get("/config/brand")
@limiter.exempt
def get_brand_config():
    """Colores/nombre públicos para login y arranque (sin secretos)."""
    items = _config_map()
    return jsonify(
        {
            "system_name": items.get("system_name") or "Sistema de Gestión Académica",
            "primary_color": _normalize_hex(items.get("primary_color"), "#0d6efd"),
            "secondary_color": _normalize_hex(items.get("secondary_color"), "#198754"),
            "accent_color": _normalize_hex(items.get("accent_color"), "#0dcaf0"),
            "default_theme": items.get("default_theme") if items.get("default_theme") in ("light", "dark") else "light",
        }
    )


@system_bp.get("/config")
@jwt_required()
def get_config():
    items = _config_map()
    # Normalizar colores para inputs type=color
    for key, fallback in (
        ("primary_color", "#0d6efd"),
        ("secondary_color", "#198754"),
        ("accent_color", "#0dcaf0"),
    ):
        if key in items:
            items[key] = _normalize_hex(items[key], fallback)
    return jsonify(items)


@system_bp.put("/config")
@jwt_required()
@permission_required("ai.configure")
def update_config():
    data = request.get_json(silent=True) or {}
    allowed = set(_BRAND_KEYS)
    cleaned = {}
    for key, value in data.items():
        if key not in allowed:
            continue
        if key in ("primary_color", "secondary_color", "accent_color"):
            defaults = {
                "primary_color": "#0d6efd",
                "secondary_color": "#198754",
                "accent_color": "#0dcaf0",
            }
            value = _normalize_hex(value, defaults[key])
        elif key == "default_theme":
            value = value if value in ("light", "dark") else "light"
        else:
            value = (str(value) if value is not None else "").strip()
            if not value and key == "system_name":
                continue
        cleaned[key] = value
        row = SystemConfig.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
        else:
            db.session.add(SystemConfig(key=key, value=str(value), description=key))
    if not cleaned:
        return jsonify({"error": "No hay campos válidos para actualizar"}), 400
    db.session.commit()
    log_event(get_current_user().id, "CONFIG_UPDATE", "system", str(list(cleaned.keys())))
    items = _config_map()
    for key, fallback in (
        ("primary_color", "#0d6efd"),
        ("secondary_color", "#198754"),
        ("accent_color", "#0dcaf0"),
    ):
        if key in items:
            items[key] = _normalize_hex(items[key], fallback)
    return jsonify({"message": "Configuración actualizada", "config": items})


# ─── AI ────────────────────────────────────────────────────
@system_bp.get("/ai/config")
@jwt_required()
@permission_required("ai.configure")
def get_ai_config():
    cfg = AIConfig.query.first()
    return jsonify(cfg.to_dict() if cfg else {})


@system_bp.put("/ai/config")
@jwt_required()
@permission_required("ai.configure")
def update_ai_config():
    data = request.get_json(silent=True) or {}
    cfg = AIConfig.query.first()
    if not cfg:
        cfg = AIConfig()
        db.session.add(cfg)
    if data.get("api_key"):
        cfg.api_key_encrypted = encrypt_value(data["api_key"])
    if "model" in data:
        cfg.model = data["model"]
    if "temperature" in data:
        cfg.temperature = float(data["temperature"])
    if "system_prompt" in data:
        cfg.system_prompt = data["system_prompt"]
    if "is_enabled" in data:
        cfg.is_enabled = bool(data["is_enabled"])
    db.session.commit()
    log_event(get_current_user().id, "AI_CONFIG_UPDATE", "ai", "")
    return jsonify(cfg.to_dict())


@system_bp.post("/ai/chat")
@jwt_required()
@permission_required("ai.use")
@limiter.limit("20 per minute")
def ai_chat():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Mensaje requerido"}), 400
    try:
        result = run_agent_chat(
            user,
            message,
            conversation_id=data.get("conversation_id"),
            channel=data.get("channel") or "api",
            confirm=bool(data.get("confirm")),
            context=data.get("context") or "",
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Error del asistente: {exc}"}), 500
    if result.get("error"):
        return jsonify(result), result.get("status", 400)
    log_event(user.id, "AI_CHAT", "ai", message[:200])
    return jsonify(result)


@system_bp.get("/ai/conversations")
@jwt_required()
@permission_required("ai.use")
def list_conversations():
    """SPEC-020: historial (activas + archivadas con mensajes)."""
    user = get_current_user()
    try:
        limit = min(int(request.args.get("limit") or 50), 100)
    except (TypeError, ValueError):
        limit = 50
    return jsonify(list_user_conversations(user.id, limit=limit))


@system_bp.get("/ai/conversations/active")
@jwt_required()
@permission_required("ai.use")
def active_conversation():
    user = get_current_user()
    preferred = request.args.get("conversation_id") or None
    conv = get_or_create_active(user.id, preferred)
    return jsonify(conv.to_dict(include_messages=True, message_limit=200))


@system_bp.get("/ai/conversations/<conversation_id>")
@jwt_required()
@permission_required("ai.use")
def get_conversation_detail(conversation_id):
    user = get_current_user()
    conv = get_conversation(conversation_id, user.id, allow_archived=True)
    if not conv and "ADMIN" not in user.get_role_codes():
        return jsonify({"error": "Conversación no encontrada"}), 404
    if not conv:
        conv = AIConversation.query.get(conversation_id)
        if not conv:
            return jsonify({"error": "Conversación no encontrada"}), 404
    return jsonify(conv.to_dict(include_messages=True, message_limit=200))


@system_bp.post("/ai/conversations")
@jwt_required()
@permission_required("ai.use")
def new_conversation():
    """Nueva conversación: la anterior queda en historial (no se borra)."""
    user = get_current_user()
    conv = create_conversation(user.id)
    return jsonify(conv.to_dict()), 201


@system_bp.post("/ai/conversations/<conversation_id>/open")
@jwt_required()
@permission_required("ai.use")
def open_conversation_route(conversation_id):
    """SPEC-020: reabrir un hilo del historial."""
    user = get_current_user()
    conv = open_conversation(conversation_id, user.id)
    if not conv:
        return jsonify({"error": "Conversación no encontrada"}), 404
    return jsonify(conv.to_dict(include_messages=True, message_limit=200))


@system_bp.patch("/ai/conversations/<conversation_id>")
@jwt_required()
@permission_required("ai.use")
def rename_conversation_route(conversation_id):
    """SPEC-024: renombrar conversación."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Título requerido"}), 400
    conv = rename_conversation(conversation_id, user.id, title)
    if not conv:
        return jsonify({"error": "Conversación no encontrada"}), 404
    return jsonify(conv.to_dict())


@system_bp.delete("/ai/conversations/<conversation_id>")
@jwt_required()
@permission_required("ai.use")
def archive_conversation_route(conversation_id):
    """SPEC-024: ?hard=1 elimina; por defecto archiva."""
    user = get_current_user()
    hard = str(request.args.get("hard") or "").lower() in ("1", "true", "yes")
    if hard:
        if not delete_conversation(conversation_id, user.id, hard=True):
            return jsonify({"error": "Conversación no encontrada"}), 404
        return jsonify({"message": "Conversación eliminada", "hard": True})
    if not archive_conversation(conversation_id, user.id):
        return jsonify({"error": "Conversación no encontrada"}), 404
    return jsonify({"message": "Conversación archivada", "hard": False})


@system_bp.get("/ai/artifacts/<int:artifact_id>/download")
def download_artifact(artifact_id):
    """SPEC-021: descarga directa por URL firmada o por JWT."""
    from app.services.artifact_links import verify_artifact_download_sig

    art = AIArtifact.query.get_or_404(artifact_id)
    if art.expires_at and art.expires_at < datetime.utcnow():
        return jsonify({"error": "El enlace de descarga ha expirado"}), 410

    token_ok = verify_artifact_download_sig(
        art, request.args.get("expires"), request.args.get("sig")
    )
    jwt_ok = False
    if not token_ok:
        try:
            verify_jwt_in_request(optional=True)
            user = get_current_user()
            if user:
                roles = user.get_role_codes()
                if art.user_id == user.id or "ADMIN" in roles:
                    if "ADMIN" in roles or user.has_permission("ai.use"):
                        jwt_ok = True
        except Exception:
            jwt_ok = False

    if not token_ok and not jwt_ok:
        return jsonify({"error": "Acceso denegado. Use JWT o enlace firmado."}), 401

    path = Path(art.storage_path)
    if not path.is_file():
        return jsonify({"error": "Archivo no disponible"}), 404
    mime = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "md": "text/markdown",
    }.get(art.format, "application/octet-stream")
    return send_file(path, mimetype=mime, as_attachment=True, download_name=art.filename)


@system_bp.get("/ai/logs")
@jwt_required()
@permission_required("ai.view_logs")
def ai_logs():
    return jsonify([l.to_dict() for l in AILog.query.order_by(AILog.created_at.desc()).limit(100).all()])


@system_bp.get("/ai/agent-logs")
@jwt_required()
@permission_required("ai.view_logs")
def agent_logs_list():
    """SPEC-026: LogIA — listado filtrable."""
    from app.services.ai_agent_log import list_agent_logs

    items = list_agent_logs(request.args)
    return jsonify([e.to_dict() for e in items])


@system_bp.get("/ai/agent-logs/export.<fmt>")
@jwt_required()
@permission_required("ai.view_logs")
def agent_logs_export(fmt):
    """SPEC-026: export LogIA xlsx | pdf | json."""
    from app.services.ai_agent_log import export_logs, list_agent_logs

    fmt = (fmt or "").lower()
    if fmt not in ("xlsx", "pdf", "json"):
        return jsonify({"error": "Formato inválido"}), 400
    items = list_agent_logs(request.args)
    buf, mime, filename = export_logs(items, fmt)
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=filename)


# ─── Kardex ────────────────────────────────────────────────
def _kardex_forbidden_for_profile(user):
    """SPEC-009: estudiantes y docentes no usan módulo kárdex."""
    roles = set(user.get_role_codes())
    if roles & {"ADMIN", "RECTOR", "SECRETARY", "COORDINATOR"}:
        return False
    return bool(roles & {"STUDENT", "TEACHER"})


@system_bp.get("/kardex/<int:student_id>")
@jwt_required()
@permission_required("kardex.view")
def kardex(student_id):
    from app.models import Course
    from app.services.visibility import visible_term_ids

    user = get_current_user()
    if _kardex_forbidden_for_profile(user):
        return jsonify({"error": "El módulo kárdex no está disponible para su rol"}), 403
    student = Student.query.get_or_404(student_id)
    q = Grade.query.filter_by(student_id=student_id).join(Course)
    term_ids = visible_term_ids(user)
    if term_ids is not None:
        q = q.filter(Course.term_id.in_(term_ids or [-1]))
    grades = q.all()
    return jsonify({"student": student.to_dict(), "grades": [g.to_dict() for g in grades]})


@system_bp.get("/kardex/<int:student_id>/pdf")
@jwt_required()
@permission_required("kardex.export")
def kardex_pdf(student_id):
    user = get_current_user()
    if _kardex_forbidden_for_profile(user):
        return jsonify({"error": "El módulo kárdex no está disponible para su rol"}), 403
    student = Student.query.get_or_404(student_id)
    grades = Grade.query.filter_by(student_id=student_id).all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Kardex Académico")
    y = 750
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Kárdex Académico")
    y -= 25
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Estudiante: {student.user.full_name} ({student.student_code})")
    y -= 20
    pdf.drawString(50, y, f"Carrera: {student.career.name if student.career else 'N/A'}")
    y -= 30
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Materia")
    pdf.drawString(280, y, "P1")
    pdf.drawString(320, y, "P2")
    pdf.drawString(360, y, "Sup")
    pdf.drawString(400, y, "Final")
    pdf.drawString(460, y, "Estado")
    y -= 15
    pdf.setFont("Helvetica", 9)
    for g in grades:
        if y < 50:
            pdf.showPage()
            y = 750
        name = (g.course.name if g.course else "")[:35]
        pdf.drawString(50, y, name)
        pdf.drawString(280, y, str(g.partial1 or "-"))
        pdf.drawString(320, y, str(g.partial2 or "-"))
        pdf.drawString(360, y, str(g.supplementary or "-"))
        pdf.drawString(400, y, str(g.final_grade or "-"))
        pdf.drawString(460, y, g.status or "")
        y -= 14
    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"kardex_{student.student_code}.pdf",
    )


# ─── Reports (SPEC-019: catálogo universal) ────────────────
def _send_xlsx(buf, filename):
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


def _send_pdf(buf, filename):
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)


def _user_can_report(user, perms: tuple) -> bool:
    if "ADMIN" in user.get_role_codes():
        return True
    have = user.get_permissions()
    return any(p in have for p in perms)


@system_bp.get("/reports/<report_type>.xlsx")
@jwt_required()
def report_xlsx(report_type):
    from app.services import reports as R

    cfg = R.REPORT_CATALOG.get(report_type)
    if not cfg:
        return jsonify({"error": "Tipo de reporte no disponible"}), 404
    user = get_current_user()
    if not _user_can_report(user, cfg["perms"]):
        return jsonify({"error": "Acceso denegado", "required": list(cfg["perms"])}), 403
    try:
        cfg, headers, rows = R.build_report(report_type, user, request.args)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return _send_xlsx(R.workbook_from_rows(cfg["title"][:31], headers, rows), f"{cfg['filename']}.xlsx")


@system_bp.get("/reports/<report_type>.pdf")
@jwt_required()
def report_pdf(report_type):
    from app.services import reports as R

    cfg = R.REPORT_CATALOG.get(report_type)
    if not cfg:
        return jsonify({"error": "Tipo de reporte no disponible"}), 404
    user = get_current_user()
    if not _user_can_report(user, cfg["perms"]):
        return jsonify({"error": "Acceso denegado", "required": list(cfg["perms"])}), 403
    try:
        cfg, headers, rows = R.build_report(report_type, user, request.args)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return _send_pdf(
        R.pdf_from_rows(f"Reporte de {cfg['title']}", headers, rows, cfg.get("widths")),
        f"{cfg['filename']}.pdf",
    )


@system_bp.get("/reports/catalog")
@jwt_required()
@permission_required("reports.view")
def report_catalog():
    from app.services import reports as R

    user = get_current_user()
    items = []
    for code, cfg in R.REPORT_CATALOG.items():
        if _user_can_report(user, cfg["perms"]):
            items.append({"type": code, "title": cfg["title"], "formats": ["xlsx", "pdf"]})
    return jsonify(items)


@system_bp.get("/reports/summary")
@jwt_required()
@permission_required("reports.view")
def report_summary():
    return jsonify(
        {
            "students": Student.query.count(),
            "teachers": Teacher.query.count(),
            "courses": Course.query.count(),
            "enrollments": Enrollment.query.count(),
            "grades": Grade.query.count(),
            "attendance": Attendance.query.count(),
            "users_active": User.query.filter_by(is_active=True).count(),
        }
    )
