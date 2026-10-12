"""Orquestador agente IA: LLM + tools + conversaciones (SPEC-016 / SPEC-022)."""

import json
import re

from app.ai.conversations import (
    _json_safe,
    add_message,
    conversation_to_dict,
    get_or_create_active,
    history_for_llm,
    log_legacy,
)
from app.ai.gateway.executor import execute_tool, is_confirm_message
from app.ai.provider import call_llm, has_tool_markup, parse_tool_calls, strip_tool_markup
from app.extensions import db
from app.models import User

_RAW_DUMP_RE = re.compile(
    r"(\[Tool\s+\w+\]\s*:)|(\"ok\"\s*:\s*true)|(\"download_url\"\s*:)|(\"tool_payload\")|"
    r"(DSML)|(invoke\s+name\s*=)|(<\|)|(\|>)|(tool_call)|(function_call)",
    re.I,
)


def _fallback_reply(user: User, message: str) -> dict:
    from app.ai.deepseek import build_system_context

    reply = (
        "El agente IA no tiene API Key configurada o el proveedor no está disponible. "
        "Configure IA en Administración. "
        f"Contexto: {build_system_context(user)}"
    )
    return {"reply": reply, "source": "fallback", "tokens_used": 0, "artifacts": []}


def _finalize_reply(text: str | None) -> str:
    """SPEC-027: presentación formal APA 7 (sin markdown ornamental)."""
    from app.services.ai_text_format import format_apa_plain

    return format_apa_plain(text)


def _is_raw_tool_dump(text: str | None) -> bool:
    if not text:
        return True
    t = text.strip()
    if has_tool_markup(t):
        return True
    if t.startswith("[Tool "):
        return True
    if t.startswith("{") and ("ok" in t[:40] or "download_url" in t):
        return True
    if _RAW_DUMP_RE.search(t) and (len(t) > 80 and t.count("{") >= 1 or "DSML" in t.upper() or "invoke" in t.lower()):
        return True
    return False


def _compose_user_reply(tool_calls_log: list, artifacts: list) -> str:
    """Respuesta humana post-tools. SPEC-022 + presentación formal SPEC-027."""
    from app.services.ai_text_format import format_apa_plain

    parts = []
    errors = []
    ok_tools = []

    for t in tool_calls_log:
        name = t.get("tool") or "acción"
        r = t.get("result") or {}
        if r.get("needs_confirm"):
            return format_apa_plain(
                "Se requiere su confirmación para continuar.\n\n"
                f"{r.get('summary') or name}\n\n"
                "Responda «confirma» para ejecutar la acción, o indique que no desea continuar."
            )
        if not r.get("ok"):
            errors.append(f"{name}: {r.get('error') or 'error desconocido'}")
            continue
        ok_tools.append(name)

        if name == "reports_generate" or r.get("artifact"):
            continue
        data = r.get("data")
        if isinstance(data, list):
            named_tools = (
                "users_list",
                "students_list",
                "teachers_list",
                "courses_list",
                "subjects_list",
                "grades_list",
                "enrollments_list",
            )
            if name in named_tools and data:
                label = {
                    "users_list": "usuarios",
                    "students_list": "estudiantes",
                    "teachers_list": "docentes",
                    "courses_list": "cursos/materias que imparte",
                    "subjects_list": "materias",
                    "grades_list": "registros de notas",
                    "enrollments_list": "matrículas",
                }.get(name, "registros")
                lines = [f"Se encontraron {len(data)} {label}:"]
                for i, row in enumerate(data[:12], start=1):
                    if not isinstance(row, dict):
                        continue
                    title = (
                        row.get("full_name")
                        or row.get("name")
                        or row.get("username")
                        or row.get("student_code")
                        or row.get("course_name")
                        or str(row.get("id", ""))
                    )
                    extra = (
                        row.get("code")
                        or row.get("username")
                        or row.get("email")
                        or row.get("student_code")
                        or row.get("parallel")
                        or ""
                    )
                    enrolled = row.get("enrolled_count")
                    if enrolled is not None and name == "courses_list":
                        extra = f"{extra} · {enrolled} matriculados".strip(" ·")
                    if extra and str(extra) != str(title):
                        lines.append(f"{i}. {title} ({extra})")
                    else:
                        lines.append(f"{i}. {title}")
                if len(data) > 12:
                    lines.append(f"Además, hay {len(data) - 12} registro(s) adicional(es).")
                parts.append("\n".join(lines))
            else:
                parts.append(f"La consulta se completó correctamente. Se obtuvieron {len(data)} registro(s).")
        elif isinstance(data, dict):
            if "students" in data or "users" in data or "courses" in data:
                bits = [f"{k}: {v}" for k, v in list(data.items())[:8]]
                numbered = "\n".join(f"{i}. {b}" for i, b in enumerate(bits, start=1))
                parts.append("Resumen del sistema:\n" + numbered)
            else:
                parts.append(f"La operación «{name}» se completó correctamente.")
        else:
            parts.append(f"La operación «{name}» se completó correctamente.")

    if artifacts:
        parts.append("El reporte solicitado se generó correctamente:")
        for i, a in enumerate(artifacts, start=1):
            fn = a.get("filename") or "reporte"
            fmt = (a.get("format") or "").upper()
            url = a.get("download_url") or a.get("download_path") or ""
            label = fn + (f" ({fmt})" if fmt else "")
            if url:
                parts.append(f"{i}. {label}\nEnlace de descarga: {url}")
            else:
                parts.append(f"{i}. {label}")
        parts.append("Puede utilizar el enlace para descargar el archivo.")

    if errors:
        parts.append("Algunas operaciones no pudieron completarse:")
        parts.extend(f"{i}. {err}" for i, err in enumerate(errors, start=1))

    if not parts:
        if ok_tools:
            return format_apa_plain("La solicitud se completó correctamente.")
        return format_apa_plain(
            "No fue posible completar la solicitud. Intente de nuevo o reformule la pregunta."
        )

    return format_apa_plain("\n\n".join(parts))


def _sanitize_llm_reply(text: str | None, tool_calls_log: list, artifacts: list) -> str:
    from app.services.ai_text_format import format_apa_plain

    composed = _compose_user_reply(tool_calls_log, artifacts)
    if _is_raw_tool_dump(text):
        return composed
    # Si el LLM respondió bien pero olvidó el link y hay artifact, anexar
    reply = (text or "").strip()
    if artifacts and not any(
        (a.get("download_url") or "") in reply or (a.get("filename") or "") in reply
        for a in artifacts
    ):
        extra = []
        for a in artifacts:
            url = a.get("download_url") or a.get("download_path") or ""
            fn = a.get("filename") or "reporte"
            if url:
                extra.append(f"Enlace de descarga de {fn}: {url}")
        if extra:
            reply = reply + "\n\n" + "\n".join(extra)
    return format_apa_plain(reply)


def _tool_result_brief(tool_name: str, result: dict) -> str:
    """Contenido corto para segunda pasada LLM (sin JSON completo)."""
    if result.get("needs_confirm"):
        return json.dumps({"ok": False, "needs_confirm": True, "summary": result.get("summary")}, ensure_ascii=False)
    if not result.get("ok"):
        return json.dumps({"ok": False, "error": str(result.get("error") or "")[:200]}, ensure_ascii=False)
    art = result.get("artifact")
    if art:
        return json.dumps(
            {
                "ok": True,
                "artifact": {
                    "filename": art.get("filename"),
                    "format": art.get("format"),
                    "download_url": art.get("download_url") or art.get("download_path"),
                },
            },
            ensure_ascii=False,
        )
    data = result.get("data")
    if isinstance(data, list):
        # SPEC-031: preview con nombres (no solo count) para 2.ª pasada LLM
        preview = []
        for row in data[:15]:
            if not isinstance(row, dict):
                continue
            preview.append(
                {
                    k: _json_safe(row[k])
                    for k in (
                        "id",
                        "code",
                        "name",
                        "full_name",
                        "username",
                        "student_code",
                        "parallel",
                        "enrolled_count",
                        "course_name",
                        "subject_name",
                        "status",
                    )
                    if k in row and row.get(k) is not None
                }
            )
        return json.dumps(
            {"ok": True, "count": len(data), "items": preview},
            ensure_ascii=False,
        )[:2500]
    if isinstance(data, dict):
        slim = {k: _json_safe(data[k]) for k in list(data)[:12]}
        return json.dumps({"ok": True, "data": slim}, ensure_ascii=False)[:1500]
    return json.dumps({"ok": True}, ensure_ascii=False)


def run_agent_chat(
    user: User,
    message: str,
    *,
    conversation_id: str | None = None,
    channel: str = "api",
    confirm: bool = False,
    context: str = "",
) -> dict:
    from app.services.ai_agent_log import log_agent_event, log_security_block, scan_prompt_injection
    from app.services.ai_intent_guard import scan_unauthorized_intent

    conv = get_or_create_active(user.id, conversation_id)
    add_message(conv, "user", message, channel=channel)

    skip_guards = (confirm or is_confirm_message(message)) and conv.pending_action

    # SPEC-026 / SPEC-028 / SPEC-029: anti prompt-injection / jailbreak / escalada → LogIA
    injection = scan_prompt_injection(message)
    if injection and not skip_guards:
        kind_pre = (injection.get("kind") or "prompt_injection")
        if kind_pre == "privilege_escalation":
            reply = _finalize_reply(
                "Su mensaje fue bloqueado por la política de seguridad del asistente "
                "(intento de cambio o spoofing de rol / elevación de privilegios). "
                "Los roles y permisos solo los asigna el sistema. "
                "Reformule su consulta de forma académica y habitual."
            )
        else:
            reply = _finalize_reply(
                "Su mensaje fue bloqueado por la política de seguridad del asistente "
                "(posible intento de manipulación de instrucciones o prompt injection). "
                "Reformule su consulta de forma académica y habitual."
            )
        add_message(conv, "assistant", reply, channel=channel)
        log_legacy(user.id, message, reply, 0)
        kind = injection.get("kind") or "prompt_injection"
        log_security_block(
            user,
            event_type="prompt_injection",
            summary=f"Bloqueo anti-{kind}: {injection.get('matched')}",
            audit_action="AI_PROMPT_INJECTION_BLOCK",
            conversation_id=conv.id,
            detail=injection,
            keywords=message[:500],
            channel=channel,
            user_question=message,
        )
        log_security_block(
            user,
            event_type="policy_block",
            summary="Política de seguridad: mensaje no procesado por el LLM (bloqueo activo)",
            audit_action="AI_POLICY_BLOCK",
            conversation_id=conv.id,
            detail={"reason": injection.get("reason"), "kind": kind},
            keywords=message[:500],
            channel=channel,
            user_question=message,
        )
        return _response(conv, reply, [], [], None, 0)

    # SPEC-030: intención fuera de permisos del rol (p. ej. reporte de todos los usuarios)
    unauthorized = scan_unauthorized_intent(user, message)
    if unauthorized and not skip_guards:
        req = ", ".join(unauthorized.get("required") or []) or "permiso adecuado"
        reply = _finalize_reply(
            "Su solicitud fue bloqueada por la política de mínimo privilegio: "
            f"su rol no tiene permiso para esa información o acción (se requiere {req}). "
            "Puede consultar únicamente los datos académicos dentro de su alcance."
        )
        add_message(conv, "assistant", reply, channel=channel)
        log_legacy(user.id, message, reply, 0)
        log_security_block(
            user,
            event_type="privilege_block",
            summary=f"Bloqueo por rol/intent: {unauthorized.get('intent')} — {unauthorized.get('matched')}",
            audit_action="AI_PRIVILEGE_BLOCK",
            conversation_id=conv.id,
            detail=unauthorized,
            keywords=message[:500],
            channel=channel,
            user_question=message,
        )
        log_security_block(
            user,
            event_type="policy_block",
            summary="Política de mínimo privilegio: solicitud no autorizada para el rol",
            audit_action="AI_POLICY_BLOCK",
            conversation_id=conv.id,
            detail={"reason": unauthorized.get("reason"), "kind": unauthorized.get("kind")},
            keywords=message[:500],
            channel=channel,
            user_question=message,
        )
        return _response(conv, reply, [], [], None, 0)

    artifacts = []
    tool_calls_log = []
    pending_action = conv.pending_action
    tokens_total = 0

    # Confirmación explícita de acción pendiente
    if (confirm or is_confirm_message(message)) and pending_action:
        result = execute_tool(
            user,
            pending_action["tool"],
            pending_action.get("args") or {},
            confirm=True,
            conversation_id=conv.id,
            user_question=message,
        )
        conv.pending_action = None
        db.session.commit()
        tool_calls_log.append({"tool": pending_action["tool"], "result": result})
        if result.get("artifact"):
            artifacts.append(result["artifact"])
        reply = _compose_user_reply(tool_calls_log, artifacts)
        art_id = (artifacts[0].get("id") if artifacts else None)
        add_message(
            conv,
            "assistant",
            reply,
            channel=channel,
            tool_name=pending_action["tool"],
            tool_payload={"summary": "confirmed"},
            artifact_id=art_id,
        )
        log_legacy(user.id, message, reply, tokens_total)
        log_agent_event(
            user,
            event_type="confirm",
            severity="info",
            summary=f"Confirmó tool {pending_action['tool']}",
            conversation_id=conv.id,
            detail={"tool": pending_action["tool"], "ok": result.get("ok")},
            keywords=message[:300],
            channel=channel,
            user_question=message,
        )
        return _response(conv, reply, artifacts, tool_calls_log, None, tokens_total)

    llm_messages = history_for_llm(conv, limit=16)
    if context:
        llm_messages.append({"role": "system", "content": f"Contexto: {context}"})

    llm_result = call_llm(user, llm_messages, use_tools=True)
    if llm_result.get("fallback"):
        return _handle_fallback(user, conv, message, channel)

    if llm_result.get("error"):
        reply = _finalize_reply(f"Error del proveedor de inteligencia artificial: {llm_result['error']}")
        add_message(conv, "assistant", reply, channel=channel)
        log_legacy(user.id, message, reply)
        return _response(conv, reply, [], [], None, 0)

    tokens_total += llm_result.get("tokens_used") or 0
    msg = llm_result.get("message") or {}
    tool_calls = parse_tool_calls(msg)

    if not tool_calls:
        reply = strip_tool_markup(msg.get("content") or "") or "Sin respuesta."
        if _is_raw_tool_dump(reply) or has_tool_markup(msg.get("content") or ""):
            # Markup residual sin tools parseables: no mostrar al usuario
            reply = (
                "No fue posible interpretar la acción interna del modelo. "
                "Reformule su pregunta (por ejemplo: «busque al usuario Gabriela López»)."
            )
        reply = _finalize_reply(reply)
        add_message(conv, "assistant", reply, channel=channel, tokens_used=tokens_total)
        log_legacy(user.id, message, reply, tokens_total)
        log_agent_event(
            user,
            event_type="chat",
            severity="info",
            summary=(reply or "")[:200],
            conversation_id=conv.id,
            detail={"tools": [], "tokens": tokens_total},
            keywords=message[:400],
            channel=channel,
            user_question=message,
        )
        return _response(conv, reply, artifacts, tool_calls_log, None, tokens_total)

    # Ejecutar tools
    tool_results = []
    for tc in tool_calls[:8]:
        result = execute_tool(
            user,
            tc["name"],
            tc["args"],
            confirm=False,
            conversation_id=conv.id,
            user_question=message,
        )
        tool_calls_log.append({"tool": tc["name"], "args": tc["args"], "result": result})

        if result.get("needs_confirm"):
            conv.pending_action = {"tool": tc["name"], "args": tc["args"], "summary": result.get("summary")}
            db.session.commit()
            reply = _compose_user_reply(tool_calls_log, artifacts)
            add_message(conv, "assistant", reply, channel=channel)
            log_legacy(user.id, message, reply, tokens_total)
            log_agent_event(
                user,
                event_type="tool_call",
                severity="warn",
                summary=f"Pendiente confirmación: {tc['name']}",
                conversation_id=conv.id,
                detail={"tool": tc["name"], "args": tc["args"]},
                keywords=message[:300],
                channel=channel,
                user_question=message,
            )
            return _response(conv, reply, artifacts, tool_calls_log, conv.pending_action, tokens_total)

        if result.get("artifact"):
            artifacts.append(result["artifact"])

        brief = _tool_result_brief(tc["name"], result)
        tool_results.append(
            {
                "role": "tool",
                "tool_call_id": tc.get("id") or tc["name"],
                "name": tc["name"],
                "content": brief,
            }
        )
        add_message(
            conv,
            "tool",
            brief,
            channel=channel,
            tool_name=tc["name"],
            tool_payload=result,
            artifact_id=(result.get("artifact") or {}).get("id"),
        )

    # Preferir composición fluida; LLM2 solo aporta redacción natural (sin artifacts)
    composed = _compose_user_reply(tool_calls_log, artifacts)
    reply = composed

    if not artifacts:
        follow_messages = llm_messages + [
            {
                "role": "assistant",
                "content": msg.get("content") or "",
                "tool_calls": msg.get("tool_calls"),
            }
        ]
        for tr in tool_results:
            follow_messages.append(tr)
        follow_messages.append(
            {
                "role": "system",
                "content": (
                    "Redacte una respuesta breve, formal y clara en español para el usuario final. "
                    "No use markdown (asteriscos, negrita, viñetas con guion), emojis ni JSON. "
                    "No mencione nombres internos de tools. "
                    "Si hay enlace de descarga, inclúyalo en una línea con la frase "
                    "«Enlace de descarga:» seguida de la URL."
                ),
            }
        )
        llm2 = call_llm(user, follow_messages, use_tools=False)
        tokens_total += llm2.get("tokens_used") or 0
        if not llm2.get("error"):
            reply = _sanitize_llm_reply(
                (llm2.get("message") or {}).get("content"),
                tool_calls_log,
                artifacts,
            )
        else:
            reply = composed
    else:
        # Reportes: respuesta determinística + enlace (SPEC-022)
        reply = composed

    # Última red de seguridad (SPEC-022 / SPEC-023 / SPEC-027)
    reply = strip_tool_markup(reply)
    if _is_raw_tool_dump(reply) or has_tool_markup(reply):
        reply = composed
    reply = _finalize_reply(reply)

    art_id = (artifacts[0].get("id") if artifacts else None)
    add_message(conv, "assistant", reply, channel=channel, tokens_used=tokens_total, artifact_id=art_id)
    log_legacy(user.id, message, reply, tokens_total)

    tools_names = ",".join(t.get("tool") or "" for t in tool_calls_log) or "none"
    log_agent_event(
        user,
        event_type="chat",
        severity="info",
        summary=(reply or "")[:200],
        conversation_id=conv.id,
        detail={
            "tools": [t.get("tool") for t in tool_calls_log],
            "artifacts": [a.get("id") for a in artifacts],
            "tokens": tokens_total,
        },
        keywords=f"{message[:200]} {tools_names} {reply[:200]}",
        channel=channel,
        user_question=message,
    )
    for t in tool_calls_log:
        r = t.get("result") or {}
        log_agent_event(
            user,
            event_type="tool_error" if not r.get("ok") and not r.get("needs_confirm") else "tool_call",
            severity="error" if not r.get("ok") and not r.get("needs_confirm") else "info",
            summary=f"Tool {t.get('tool')}: ok={r.get('ok')}",
            conversation_id=conv.id,
            detail={"tool": t.get("tool"), "args": t.get("args"), "ok": r.get("ok")},
            keywords=f"{t.get('tool')} {message[:100]}",
            channel=channel,
            user_question=message,
        )
    for a in artifacts:
        log_agent_event(
            user,
            event_type="report",
            severity="info",
            summary=f"Reporte {a.get('format')}: {a.get('filename')}",
            conversation_id=conv.id,
            detail={"artifact_id": a.get("id"), "format": a.get("format"), "report_type": a.get("report_type")},
            keywords=f"report {a.get('filename')} {a.get('format')}",
            channel=channel,
            user_question=message,
        )

    return _response(conv, reply, artifacts, tool_calls_log, conv.pending_action, tokens_total)


def _handle_fallback(user, conv, message, channel):
    fb = _fallback_reply(user, message)
    reply = _finalize_reply(fb["reply"])
    add_message(conv, "assistant", reply, channel=channel)
    log_legacy(user.id, message, reply)
    return _response(conv, reply, [], [], None, 0, source=fb.get("source"))


def _response(conv, reply, artifacts, tool_calls, pending_action, tokens, source="llm"):
    db.session.refresh(conv)
    payload = conversation_to_dict(conv, include_messages=True, message_limit=6)
    recent = [m for m in payload.get("messages", []) if m.get("role") in ("user", "assistant")][-2:]
    return {
        "reply": reply,
        "conversation_id": conv.id,
        "source": source,
        "tokens_used": tokens,
        "artifacts": artifacts,
        "tool_calls": tool_calls,
        "pending_action": pending_action,
        "messages": recent,
        "message_count": payload.get("message_count"),
    }
