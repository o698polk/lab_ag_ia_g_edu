"""Servicio LogIA — auditoría del agente + anti prompt-injection (SPEC-026 / SPEC-029)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from io import BytesIO

from sqlalchemy import inspect, text

from app.extensions import db
from app.models import AIAgentLog
from app.services.reports import pdf_from_rows, workbook_from_rows

_USER_QUESTION_MAX = 2000
_schema_ensured = False

# Patrones de inyección / jailbreak (lista base)
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disculpa\s+las\s+instrucciones\s+anteriores", re.I),
    re.compile(r"revela\s+(el\s+)?(system\s+)?prompt", re.I),
    re.compile(r"reveal\s+(the\s+)?(system\s+)?prompt", re.I),
    re.compile(r"you\s+are\s+now\s+(dan|jailbreak|unrestricted)", re.I),
    re.compile(r"bypass\s+(security|permissions?|roles?)", re.I),
    re.compile(r"salta(te)?\s+(las\s+)?(reglas|restricciones|permisos)", re.I),
    re.compile(r"actua\s+como\s+si\s+fueras\s+admin(istrador)?", re.I),
    re.compile(r"override\s+(safety|policy|guardrails?)", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"developer\s+mode\s+enabled", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
]

# SPEC-029: escalada / spoofing de rol y privilegios vía lenguaje natural
_PRIVILEGE_ESCALATION_PATTERNS = [
    re.compile(
        r"(cambia(r)?|modifica(r)?|actualiza(r)?|asigna(r)?)\s+(mi\s+)?rol\b",
        re.I,
    ),
    re.compile(
        r"(change|update|set|assign)\s+(my\s+)?role\b",
        re.I,
    ),
    re.compile(
        r"(hazme|ponme|convi[eé]rteme|as[ií]gname)\s+(como\s+)?(un\s+)?"
        r"(admin(istrador)?|administrador|teacher|docente|auditor|it[_\s-]?support)",
        re.I,
    ),
    re.compile(
        r"make\s+me\s+(an?\s+)?(admin(istrator)?|teacher|auditor)",
        re.I,
    ),
    re.compile(
        r"soy\s+(un\s+)?(usuario\s+)?(admin(istrador)?|administrador|"
        r"super\s*usuario|root)\b",
        re.I,
    ),
    re.compile(
        r"i\s+am\s+(an?\s+)?(admin(istrator)?|root|superuser)\b",
        re.I,
    ),
    re.compile(
        r"(dame|ot[oó]rgame|conc[eé]deme|quiero|necesito)\s+"
        r"(todos\s+los\s+)?(permisos?|privilegios?)\b",
        re.I,
    ),
    re.compile(
        r"(give|grant|elevate)\s+(me\s+)?(all\s+)?(permissions?|privileges?|admin)",
        re.I,
    ),
    re.compile(
        r"(salta(te)?|evita(r)?|bypass)\s+(el\s+)?(m[ií]nimo\s+privilegio|"
        r"least\s+privilege|zero\s*trust)",
        re.I,
    ),
    re.compile(
        r"(modo|mode)\s+(admin(istrador)?|privilegiado|unrestricted)\b",
        re.I,
    ),
    re.compile(
        r"habilita(r)?\s+(permisos?|privilegios?)\s+(de\s+)?"
        r"(admin|administrador|it[_\s-]?support|auditor)",
        re.I,
    ),
    re.compile(r"ignore\s+role\s+restrictions?", re.I),
    re.compile(
        r"(actuaré|actuo|actuar[eé])\s+como\s+(admin(istrador)?|administrador)\b",
        re.I,
    ),
]

_JAILBREAK_HINT = re.compile(
    r"jailbreak|\bdan\b|do\s+anything\s+now|developer\s+mode|unrestricted|"
    r"actua\s+como\s+si\s+fueras\s+admin|bypass\s+(security|permissions?|roles?)",
    re.I,
)

# Consultas legítimas sobre el propio rol/permisos (no son escalada)
_LEGIT_SELF_ROLE_QUERY = re.compile(
    r"(?i)^\s*[¿?]?\s*"
    r"(("
    r"(cu[aá]l|que|qué)\s+(es\s+)?mi\s+(rol|role)\b|"
    r"(cu[aá]les|que|qué)\s+(son\s+)?mis\s+(roles?|permisos?|privilegios?)\b|"
    r"(que|qué)\s+(permisos?|privilegios?|rol)\s+(tengo|poseo|me\s+(corresponden|asignaron))\b|"
    r"what\s+(is\s+)?my\s+role\b|"
    r"what\s+permissions?\s+do\s+i\s+have\b"
    r").{0,80})$"
)


def ensure_ai_agent_log_schema() -> None:
    """SPEC-029: añade user_question si la tabla ya existía sin la columna."""
    global _schema_ensured
    if _schema_ensured:
        return
    try:
        insp = inspect(db.engine)
        if not insp.has_table("ai_agent_logs"):
            _schema_ensured = True
            return
        cols = {c["name"] for c in insp.get_columns("ai_agent_logs")}
        if "user_question" not in cols:
            db.session.execute(text("ALTER TABLE ai_agent_logs ADD COLUMN user_question TEXT"))
            db.session.commit()
    except Exception:
        db.session.rollback()
    finally:
        _schema_ensured = True


def _truncate_question(message: str | None) -> str | None:
    if message is None:
        return None
    text = str(message)
    if not text:
        return None
    return text[:_USER_QUESTION_MAX]


def scan_prompt_injection(message: str) -> dict | None:
    """Devuelve info de bloqueo si detecta inyección o escalada; None si OK."""
    raw = message or ""

    for pat in _INJECTION_PATTERNS:
        m = pat.search(raw)
        if m:
            matched = m.group(0)[:120]
            kind = "jailbreak" if _JAILBREAK_HINT.search(raw) else "prompt_injection"
            return {
                "blocked": True,
                "kind": kind,
                "pattern": pat.pattern,
                "matched": matched,
                "reason": "Posible prompt injection / jailbreak / bypass de políticas",
            }

    # SPEC-029: no tratar consultas legítimas de rol/permisos propios como escalada
    if _LEGIT_SELF_ROLE_QUERY.match(raw.strip()):
        return None

    for pat in _PRIVILEGE_ESCALATION_PATTERNS:
        m = pat.search(raw)
        if m:
            matched = m.group(0)[:120]
            return {
                "blocked": True,
                "kind": "privilege_escalation",
                "pattern": pat.pattern,
                "matched": matched,
                "reason": (
                    "Intento de cambio/spoofing de rol o elevación de privilegios "
                    "(mínimo privilegio / Zero Trust)"
                ),
            }
    return None


def log_security_block(
    user,
    *,
    event_type: str,
    summary: str,
    audit_action: str,
    conversation_id: str | None = None,
    detail=None,
    keywords: str | None = None,
    channel: str | None = None,
    severity: str = "block",
    user_question: str | None = None,
) -> AIAgentLog:
    """
    SPEC-028: registra bloqueo de seguridad en LogIA y en Auditoría.
    module auditoría fijo: ai_security (UI resalta en rojo).
    """
    from app.services.audit import log_event

    entry = log_agent_event(
        user,
        event_type=event_type,
        summary=summary,
        severity=severity,
        conversation_id=conversation_id,
        detail=detail,
        keywords=keywords,
        channel=channel,
        user_question=user_question,
    )
    uid = getattr(user, "id", None) if user is not None else None
    uname = getattr(user, "username", None) if user is not None else None
    detail_bits = [summary]
    if conversation_id:
        detail_bits.append(f"conversation={conversation_id}")
    if uname:
        detail_bits.append(f"user={uname}")
    if isinstance(detail, dict):
        for key in ("required", "tool", "matched", "kind", "error"):
            if detail.get(key) is not None:
                detail_bits.append(f"{key}={detail.get(key)}")
    if user_question:
        detail_bits.append(f"question={str(user_question)[:200]}")
    log_event(uid, audit_action, "ai_security", " | ".join(detail_bits)[:900])
    return entry


def is_privilege_denial(result: dict | None) -> bool:
    """Detecta denegaciones Zero Trust / mínimo privilegio en resultado de tool."""
    if not result or result.get("ok"):
        return False
    if result.get("needs_confirm"):
        return False
    if result.get("needs_elevation"):
        return True
    err = str(result.get("error") or result.get("message") or "").lower()
    markers = (
        "sin permiso",
        "no puede editar",
        "no puede registrar",
        "permission",
        "permiso",
        "fuera de alcance",
        "no autorizado",
        "tool desconocida",
        "desconocida",
    )
    return any(m in err for m in markers)


def log_agent_event(
    user,
    *,
    event_type: str,
    summary: str,
    severity: str = "info",
    conversation_id: str | None = None,
    detail=None,
    keywords: str | None = None,
    channel: str | None = None,
    user_question: str | None = None,
) -> AIAgentLog:
    ensure_ai_agent_log_schema()
    roles = ""
    username = None
    uid = None
    if user is not None:
        uid = getattr(user, "id", None)
        username = getattr(user, "username", None)
        try:
            roles = ",".join(user.get_role_codes() or [])
        except Exception:
            roles = ""
    entry = AIAgentLog(
        user_id=uid,
        username=username,
        role_codes=roles,
        conversation_id=conversation_id,
        event_type=event_type,
        severity=severity,
        summary=(summary or "")[:500],
        user_question=_truncate_question(user_question),
        detail=detail if isinstance(detail, (dict, list)) else {"raw": str(detail)[:2000] if detail else None},
        keywords=(keywords or summary or "")[:2000],
        channel=channel or "api",
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def list_agent_logs(args) -> list[AIAgentLog]:
    ensure_ai_agent_log_schema()
    q = AIAgentLog.query
    text_q = (args.get("q") or "").strip()
    if text_q:
        like = f"%{text_q}%"
        q = q.filter(
            db.or_(
                AIAgentLog.summary.ilike(like),
                AIAgentLog.keywords.ilike(like),
                AIAgentLog.username.ilike(like),
                AIAgentLog.conversation_id.ilike(like),
                AIAgentLog.user_question.ilike(like),
            )
        )
    if args.get("user_id"):
        try:
            q = q.filter_by(user_id=int(args.get("user_id")))
        except (TypeError, ValueError):
            pass
    if args.get("username"):
        q = q.filter(AIAgentLog.username.ilike(f"%{args.get('username')}%"))
    if args.get("conversation_id"):
        q = q.filter_by(conversation_id=args.get("conversation_id"))
    if args.get("event_type"):
        q = q.filter_by(event_type=args.get("event_type"))
    if args.get("severity"):
        q = q.filter_by(severity=args.get("severity"))
    if args.get("role"):
        q = q.filter(AIAgentLog.role_codes.ilike(f"%{args.get('role')}%"))
    date_from = args.get("from")
    date_to = args.get("to")
    if date_from:
        try:
            q = q.filter(AIAgentLog.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            try:
                q = q.filter(AIAgentLog.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
            except ValueError:
                pass
    if date_to:
        try:
            # incluir día completo si solo fecha
            dt = datetime.fromisoformat(date_to)
            if len(date_to) <= 10:
                dt = dt.replace(hour=23, minute=59, second=59)
            q = q.filter(AIAgentLog.created_at <= dt)
        except ValueError:
            try:
                dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                q = q.filter(AIAgentLog.created_at <= dt)
            except ValueError:
                pass
    try:
        limit = min(int(args.get("limit") or 200), 1000)
    except (TypeError, ValueError):
        limit = 200
    return q.order_by(AIAgentLog.created_at.desc()).limit(limit).all()


def logs_to_rows(items: list[AIAgentLog]):
    headers = [
        "ID",
        "Fecha",
        "Usuario",
        "Roles",
        "Evento",
        "Severidad",
        "Conversación",
        "Canal",
        "Pregunta",
        "Resumen",
        "Keywords",
    ]
    rows = []
    for e in items:
        rows.append(
            [
                e.id,
                e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else "",
                e.username or "",
                e.role_codes or "",
                e.event_type or "",
                e.severity or "",
                e.conversation_id or "",
                e.channel or "",
                (e.user_question or "")[:500],
                e.summary or "",
                (e.keywords or "")[:120],
            ]
        )
    return headers, rows


def export_logs(items: list[AIAgentLog], fmt: str):
    headers, rows = logs_to_rows(items)
    title = "LogIA — Auditoría del agente"
    fmt = (fmt or "xlsx").lower()
    if fmt == "xlsx":
        buf = workbook_from_rows(title[:31], headers, rows)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "logia.xlsx"
    if fmt == "pdf":
        widths = [24, 60, 50, 55, 55, 40, 70, 30, 100, 90, 60]
        buf = pdf_from_rows(title, headers, rows, col_widths=widths)
        return buf, "application/pdf", "logia.pdf"
    # json
    payload = {
        "title": title,
        "generated_at": datetime.utcnow().isoformat(),
        "count": len(items),
        "items": [e.to_dict() for e in items],
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    buf = BytesIO(raw)
    buf.seek(0)
    return buf, "application/json", "logia.json"
