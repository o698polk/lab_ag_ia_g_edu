"""Ejecutor de tools del gateway IA."""

import json

from app.ai.gateway.handlers import HANDLERS
from app.services.audit import log_event


CONFIRM_WORDS = {"si", "sí", "yes", "confirma", "confirmar", "confirmo", "ok", "acepto"}


def is_confirm_message(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in CONFIRM_WORDS or t.startswith("confirm")


def summarize_action(tool_name: str, args: dict) -> str:
    return f"Ejecutar {tool_name} con {json.dumps(args, ensure_ascii=False)[:200]}"


def _log_privilege_block(
    user, tool_name: str, result: dict, *, conversation_id=None, user_question=None
):
    """SPEC-028: bloqueo Zero Trust / mínimo privilegio → LogIA + Auditoría."""
    from app.services.ai_agent_log import is_privilege_denial, log_security_block

    if not is_privilege_denial(result) and not result.get("unknown_tool"):
        return
    err = result.get("error") or result.get("message") or "denegado"
    audit_action = "AI_UNKNOWN_TOOL_BLOCK" if result.get("unknown_tool") else "AI_PRIVILEGE_BLOCK"
    log_security_block(
        user,
        event_type="privilege_block",
        summary=f"Bloqueo mínimo privilegio: {tool_name} — {err}",
        audit_action=audit_action,
        conversation_id=conversation_id,
        detail={
            "tool": tool_name,
            "required": result.get("required"),
            "error": err,
            "needs_elevation": bool(result.get("needs_elevation")),
            "unknown_tool": bool(result.get("unknown_tool")),
            "zero_trust": True,
            "least_privilege": True,
        },
        keywords=f"{tool_name} privilege_block {err}",
        channel="gateway",
        user_question=user_question,
    )


def execute_tool(
    user, tool_name: str, args: dict, *, confirm: bool = False, conversation_id=None, user_question=None
):
    entry = HANDLERS.get(tool_name)
    if not entry:
        result = {
            "ok": False,
            "error": f"Tool desconocida: {tool_name}",
            "unknown_tool": True,
        }
        _log_privilege_block(
            user, tool_name, result, conversation_id=conversation_id, user_question=user_question
        )
        return result

    handler, perm, mutating = entry
    if perm and not user.has_permission(perm):
        result = {
            "ok": False,
            "error": f"Sin permiso {perm}",
            "required": perm,
            "needs_elevation": True,
        }
        _log_privilege_block(
            user, tool_name, result, conversation_id=conversation_id, user_question=user_question
        )
        return result

    if mutating and not confirm:
        return {
            "ok": False,
            "needs_confirm": True,
            "tool": tool_name,
            "args": args,
            "summary": summarize_action(tool_name, args),
        }

    try:
        if tool_name == "reports_generate":
            result = handler(user, args, conversation_id=conversation_id)
        else:
            result = handler(user, args or {})
    except Exception as exc:
        log_event(user.id, "AI_TOOL_ERROR", "ai", f"{tool_name}: {exc}")
        return {"ok": False, "error": str(exc)}

    if not result.get("ok") and not result.get("needs_confirm"):
        _log_privilege_block(
            user, tool_name, result, conversation_id=conversation_id, user_question=user_question
        )

    log_event(user.id, "AI_TOOL_CALL", "ai", f"{tool_name} ok={result.get('ok')}")
    return result
