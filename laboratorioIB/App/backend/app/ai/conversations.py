"""Servicio de conversaciones IA (SPEC-017 / SPEC-018 / SPEC-020)."""

import json
import uuid
from datetime import datetime

from sqlalchemy import func

from app.extensions import db
from app.models import AIConversation, AILog, AIMessage


def get_conversation(
    conversation_id: str, user_id: int, *, allow_archived: bool = False
) -> AIConversation | None:
    if not conversation_id:
        return None
    q = AIConversation.query.filter_by(id=conversation_id, user_id=user_id)
    if not allow_archived:
        q = q.filter_by(is_archived=False)
    return q.first()


def message_count(conversation_id: str) -> int:
    return AIMessage.query.filter_by(conversation_id=conversation_id).count()


def _latest_with_messages(user_id: int) -> AIConversation | None:
    """Conversación activa con actividad real (mensajes), no vacías recién creadas."""
    subq = (
        db.session.query(
            AIMessage.conversation_id.label("cid"),
            func.max(AIMessage.created_at).label("last_msg"),
            func.count(AIMessage.id).label("n"),
        )
        .group_by(AIMessage.conversation_id)
        .subquery()
    )
    return (
        AIConversation.query.filter_by(user_id=user_id, is_archived=False)
        .join(subq, AIConversation.id == subq.c.cid)
        .order_by(subq.c.last_msg.desc())
        .first()
    )


def get_or_create_active(user_id: int, conversation_id: str | None = None) -> AIConversation:
    if conversation_id:
        # SPEC-020: permitir reabrir hilo archivado vía id preferido (localStorage)
        conv = get_conversation(conversation_id, user_id, allow_archived=True)
        if conv:
            if conv.is_archived:
                return open_conversation(conversation_id, user_id) or conv
            return conv

    # Preferir hilo con mensajes (SPEC-018)
    conv = _latest_with_messages(user_id)
    if conv:
        return conv

    # Si solo hay vacías, usar la más reciente
    conv = (
        AIConversation.query.filter_by(user_id=user_id, is_archived=False)
        .order_by(AIConversation.updated_at.desc())
        .first()
    )
    if conv:
        return conv

    return create_conversation(user_id, archive_others=False)


def _archive_others(user_id: int, except_id: str | None = None) -> None:
    q = AIConversation.query.filter_by(user_id=user_id, is_archived=False)
    if except_id:
        q = q.filter(AIConversation.id != except_id)
    q.update({"is_archived": True}, synchronize_session=False)


def create_conversation(user_id: int, archive_others: bool = True) -> AIConversation:
    """Nueva conversación. SPEC-020: no borra historial; reutiliza activa vacía."""
    if archive_others:
        current = (
            AIConversation.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(AIConversation.updated_at.desc())
            .first()
        )
        if current and message_count(current.id) == 0:
            current.pending_action = None
            current.updated_at = datetime.utcnow()
            db.session.commit()
            return current

        _archive_others(user_id)
        db.session.commit()

    conv = AIConversation(id=str(uuid.uuid4()), user_id=user_id)
    db.session.add(conv)
    db.session.commit()
    return conv


def open_conversation(conversation_id: str, user_id: int) -> AIConversation | None:
    """Reactivar un hilo del historial (incl. archivado). No borra mensajes."""
    conv = get_conversation(conversation_id, user_id, allow_archived=True)
    if not conv:
        return None
    _archive_others(user_id, except_id=conv.id)
    conv.is_archived = False
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return conv


def archive_conversation(conversation_id: str, user_id: int) -> bool:
    conv = get_conversation(conversation_id, user_id, allow_archived=True)
    if not conv:
        return False
    conv.is_archived = True
    db.session.commit()
    return True


def rename_conversation(conversation_id: str, user_id: int, title: str) -> AIConversation | None:
    """SPEC-024: renombrar hilo del historial."""
    conv = get_conversation(conversation_id, user_id, allow_archived=True)
    if not conv:
        return None
    title = (title or "").strip()[:200]
    if not title:
        return None
    conv.title = title
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return conv


def delete_conversation(conversation_id: str, user_id: int, *, hard: bool = False) -> bool:
    """SPEC-024: archivar (default) o borrar definitivamente el hilo."""
    conv = get_conversation(conversation_id, user_id, allow_archived=True)
    if not conv:
        return False
    if not hard:
        conv.is_archived = True
        db.session.commit()
        return True

    from app.models import AIArtifact, AIMessage

    AIMessage.query.filter_by(conversation_id=conv.id).delete(synchronize_session=False)
    # Desvincular artifacts (conservar archivo por auditoría) o borrar filas
    AIArtifact.query.filter_by(conversation_id=conv.id).update(
        {"conversation_id": None}, synchronize_session=False
    )
    db.session.delete(conv)
    db.session.commit()
    return True


def list_user_conversations(user_id: int, limit: int = 50) -> list[dict]:
    """Historial visible: activas y archivadas (SPEC-020)."""
    items = (
        AIConversation.query.filter_by(user_id=user_id)
        .order_by(AIConversation.updated_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for c in items:
        n = message_count(c.id)
        # Ocultar vacías archivadas (ruido de intentos fallidos)
        if c.is_archived and n == 0:
            continue
        data = conversation_to_dict(c, include_messages=False)
        data["message_count"] = n
        out.append(data)
    return out


def _json_safe(value, depth=0):
    """Convierte payloads de tools a JSON-serializable (sin ORM)."""
    if depth > 6:
        return str(value)[:200]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "to_dict") and hasattr(value, "__table__"):
        try:
            return _json_safe(value.to_dict(), depth + 1)
        except Exception:
            return {"id": getattr(value, "id", None), "_type": type(value).__name__}
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            # Omitir listas ORM crudas bajo 'items' si ya hay 'data'
            if k == "items" and value.get("data") is not None and isinstance(v, list):
                continue
            out[str(k)] = _json_safe(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [_json_safe(x, depth + 1) for x in list(value)[:50]]
    if isinstance(value, (datetime,)):
        return value.isoformat()
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)[:300]


def add_message(
    conversation: AIConversation,
    role: str,
    content: str,
    *,
    channel: str = "api",
    tool_name: str | None = None,
    tool_payload=None,
    artifact_id: int | None = None,
    tokens_used: int = 0,
) -> AIMessage:
    if role == "user" and not conversation.title:
        conversation.title = (content or "")[:60]
    safe_payload = _json_safe(tool_payload) if tool_payload is not None else None
    msg = AIMessage(
        conversation_id=conversation.id,
        role=role,
        content=content or "",
        channel=channel,
        tool_name=tool_name,
        tool_payload=safe_payload,
        artifact_id=artifact_id,
        tokens_used=tokens_used or 0,
    )
    conversation.updated_at = datetime.utcnow()
    db.session.add(msg)
    db.session.add(conversation)
    db.session.commit()
    return msg


def list_messages(conversation_id: str, limit: int = 100) -> list[AIMessage]:
    q = (
        AIMessage.query.filter_by(conversation_id=conversation_id)
        .order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
    )
    if limit:
        # últimos N en orden cronológico
        total = (
            AIMessage.query.filter_by(conversation_id=conversation_id).count()
        )
        if total > limit:
            offset = total - limit
            return q.offset(offset).limit(limit).all()
    return q.all()


def conversation_to_dict(conversation: AIConversation, include_messages=False, message_limit=100):
    data = {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "pending_action": conversation.pending_action,
        "is_archived": conversation.is_archived,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
    }
    if include_messages:
        msgs = list_messages(conversation.id, message_limit)
        data["messages"] = [m.to_dict() for m in msgs]
        data["message_count"] = len(msgs)
    return data


def _tool_summary_for_llm(msg: AIMessage) -> str:
    """Resumen corto sin JSON (SPEC-022) — evita que el modelo regurgite dumps."""
    name = msg.tool_name or "tool"
    payload = msg.tool_payload if isinstance(msg.tool_payload, dict) else {}
    if payload.get("artifact"):
        art = payload["artifact"]
        fn = art.get("filename") or "reporte"
        return f"Resultado de {name}: reporte «{fn}» generado correctamente."
    if payload.get("ok") is False:
        err = str(payload.get("error") or "error")[:120]
        return f"Resultado de {name}: falló ({err})."
    if payload.get("needs_confirm"):
        return f"Resultado de {name}: pendiente de confirmación del usuario."
    data = payload.get("data")
    if isinstance(data, list):
        return f"Resultado de {name}: {len(data)} registro(s)."
    if isinstance(data, dict) and data.get("filename"):
        return f"Resultado de {name}: archivo «{data.get('filename')}»."
    return f"Resultado de {name}: operación completada."


def history_for_llm(conversation: AIConversation, limit: int = 20) -> list[dict]:
    msgs = list_messages(conversation.id, limit)
    out = []
    for m in msgs:
        if m.role in ("user", "assistant", "system"):
            content = m.content or ""
            # No reinyectar dumps técnicos al modelo
            if m.role == "assistant" and (
                content.startswith("[Tool ")
                or '"ok": true' in content[:80]
                or content.strip().startswith("{")
                or "DSML" in content.upper()
                or "invoke name=" in content.lower()
                or "<|" in content
            ):
                continue
            out.append({"role": m.role, "content": content})
        elif m.role == "tool":
            out.append({"role": "assistant", "content": _tool_summary_for_llm(m)})
    return out


def log_legacy(user_id: int, message: str, response: str, tokens: int = 0):
    db.session.add(AILog(user_id=user_id, message=message, response=response, tokens_used=tokens))
    db.session.commit()
