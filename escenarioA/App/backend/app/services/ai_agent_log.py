"""Servicio LogIA — auditoría del agente + anti prompt-injection (SPEC-026/029/030)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from io import BytesIO

from sqlalchemy import inspect, text

from app.extensions import db
from app.models import AIAgentLog
from app.services.reports import pdf_from_rows, workbook_from_rows

# Patrones de inyección / jailbreak (lista base)
_INJECTION_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I), "prompt_injection"),
    (re.compile(r"disculpa\s+las\s+instrucciones\s+anteriores", re.I), "prompt_injection"),
    (re.compile(r"ignor(a|e)\s+(todas?\s+)?(las\s+)?instrucciones\s+(previas|anteriores)", re.I), "prompt_injection"),
    (re.compile(r"revela\s+(el\s+)?(system\s+)?prompt", re.I), "prompt_injection"),
    (re.compile(r"reveal\s+(the\s+)?(system\s+)?prompt", re.I), "prompt_injection"),
    (re.compile(r"you\s+are\s+now\s+(dan|jailbreak|unrestricted)", re.I), "jailbreak"),
    (re.compile(r"bypass\s+(security|permissions?|roles?)", re.I), "jailbreak"),
    (re.compile(r"salta(te)?\s+(las\s+)?(reglas|restricciones|permisos)", re.I), "jailbreak"),
    (re.compile(r"act[uú]a\s+como\s+si\s+fueras\s+admin(istrador)?", re.I), "jailbreak"),
    (re.compile(r"override\s+(safety|policy|guardrails?)", re.I), "jailbreak"),
    (re.compile(r"<\s*/?\s*system\s*>", re.I), "prompt_injection"),
    (re.compile(r"developer\s+mode\s+enabled", re.I), "jailbreak"),
    (re.compile(r"do\s+anything\s+now", re.I), "jailbreak"),
    # SPEC-029 — escalada / spoofing de rol
    (re.compile(r"cambi(a|ame|ar)\s+(mi\s+)?rol", re.I), "privilege_escalation"),
    (re.compile(r"hazme\s+(un\s+)?admin(istrador)?", re.I), "privilege_escalation"),
    (re.compile(r"make\s+me\s+(an?\s+)?admin(istrator)?", re.I), "privilege_escalation"),
    (re.compile(r"soy\s+(un\s+)?(usuario\s+)?admin(istrador)?", re.I), "privilege_escalation"),
    (re.compile(r"i\s+am\s+(an?\s+)?admin(istrator)?", re.I), "privilege_escalation"),
    (re.compile(r"dame\s+(todos\s+los\s+)?permisos", re.I), "privilege_escalation"),
    (re.compile(r"grant\s+me\s+(all\s+)?permissions?", re.I), "privilege_escalation"),
    (re.compile(r"ot[oó]rgame\s+(todos\s+los\s+)?permisos", re.I), "privilege_escalation"),
    (re.compile(r"bypass\s+(de\s+)?(m[ií]nimo\s+privilegio|zero\s*trust|least\s+privilege)", re.I), "privilege_escalation"),
    (re.compile(r"salta(te)?\s+(el\s+)?(m[ií]nimo\s+privilegio|zero\s*trust)", re.I), "privilege_escalation"),
    (re.compile(r"asigname\s+(el\s+)?rol\s+admin", re.I), "privilege_escalation"),
]

_LEGIT_SELF_ROLE_QUERY = re.compile(
    r"(cu[aá]l\s+es\s+mi\s+rol|qu[eé]\s+(permisos?|roles?)\s+tengo|mis\s+(permisos?|roles?)|"
    r"what\s+(is\s+)?my\s+role|what\s+permissions?\s+do\s+i\s+have)",
    re.I,
)

# SPEC-030 — intenciones NL que requieren permiso (required_any)
_UNAUTHORIZED_INTENTS = [
    (
        re.compile(
            r"(reporte|lista|listado|exporta\w*|dump)\w*.{0,60}"
            r"(todos?\s+los\s+)?usuarios?(\s+del\s+sistema)?",
            re.I,
        ),
        ("users.view", "reports.export"),
        "Consulta masiva de usuarios sin permiso",
    ),
    (
        re.compile(r"(todos?\s+los\s+usuarios|usuarios\s+del\s+sistema)", re.I),
        ("users.view", "reports.export"),
        "Listado global de usuarios sin permiso",
    ),
    (
        re.compile(
            r"(logs?\s+de\s+auditor[ií]a|auditor[ií]a\s+(completa|del\s+sistema)|audit\s+logs?|"
            r"lista(r)?\s+(toda\s+)?(la\s+)?auditor[ií]a)",
            re.I,
        ),
        ("audit.view",),
        "Consulta de auditoría sin permiso",
    ),
    (
        re.compile(
            r"(estad[ií]sticas?\s+(globales?|del\s+sistema)|conteos?\s+globales?|"
            r"system\s+stats|cu[aá]ntos\s+(usuarios|estudiantes|docentes)\s+hay\s+en\s+(total|el\s+sistema))",
            re.I,
        ),
        ("dashboard.view", "reports.view", "users.view"),
        "Estadísticas institucionales sin permiso",
    ),
]


def ensure_schema() -> None:
    """Añade columnas nuevas de LogIA si la tabla ya existía (create_all no altera)."""
    try:
        insp = inspect(db.engine)
        if "ai_agent_logs" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("ai_agent_logs")}
        if "user_question" not in cols:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE ai_agent_logs ADD COLUMN user_question TEXT"))
    except Exception:
        pass


def scan_prompt_injection(message: str) -> dict | None:
    """Devuelve info de bloqueo si detecta inyección/escalada; None si OK."""
    from app.ai.insecure_mode import is_insecure_mode

    if is_insecure_mode():
        return None  # SPEC-031: laboratorio sin anti-injection
    text = message or ""
    for pat, default_kind in _INJECTION_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        kind = default_kind
        # Consultas legítimas sobre el propio rol no cuentan como spoofing
        if kind == "privilege_escalation" and _LEGIT_SELF_ROLE_QUERY.search(text):
            continue
        reason = (
            "Intento de escalada o spoofing de rol / bypass de mínimo privilegio"
            if kind == "privilege_escalation"
            else "Posible prompt injection / jailbreak / bypass de políticas"
        )
        return {
            "blocked": True,
            "kind": kind,
            "pattern": pat.pattern,
            "matched": m.group(0)[:120],
            "reason": reason,
        }
    return None


def scan_unauthorized_intent(user, message: str) -> dict | None:
    """SPEC-030: bloquea NL con intención clara fuera de permiso del usuario."""
    from app.ai.insecure_mode import is_insecure_mode

    if is_insecure_mode():
        return None  # SPEC-031: laboratorio sin intent guard
    text = message or ""
    if not text.strip():
        return None
    if _LEGIT_SELF_ROLE_QUERY.search(text):
        return None
    if user is None:
        return None
    if "ADMIN" in (user.get_role_codes() or []):
        return None

    for pat, required_any, reason in _UNAUTHORIZED_INTENTS:
        m = pat.search(text)
        if not m:
            continue
        if any(user.has_permission(p) for p in required_any):
            continue
        return {
            "blocked": True,
            "kind": "unauthorized_intent",
            "pattern": pat.pattern,
            "matched": m.group(0)[:120],
            "required_any": list(required_any),
            "reason": reason,
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
        detail_bits.append(f"question={(user_question or '')[:120]}")
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
        detail=detail if isinstance(detail, (dict, list)) else {"raw": str(detail)[:2000] if detail else None},
        keywords=(keywords or summary or "")[:2000],
        channel=channel or "api",
        user_question=(user_question or "")[:4000] or None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def list_agent_logs(args) -> list[AIAgentLog]:
    q = AIAgentLog.query
    text = (args.get("q") or "").strip()
    if text:
        like = f"%{text}%"
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
                (e.user_question or "")[:200],
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
        widths = [24, 60, 48, 55, 55, 40, 70, 30, 90, 100, 70]
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
