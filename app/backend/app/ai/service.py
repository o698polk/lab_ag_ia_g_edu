# Ref: BL-O6-005 | Skill: K-018 | Fase: F6
"""AI service — proposes tools only; never touches MySQL directly."""

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.deepseek import propose_from_message
from app.auth.deps import CurrentUser
from app.gateway.pep import ToolGateway
from app.models import AiConversation, AiMessage
from app.policy.pdp import AuthzRequest, PDP, Subject
from app.services.ai_settings_service import AiSettingsService


class AIService:
    """Mock NL → tool proposal. Execution always via Tool Gateway."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = ToolGateway(db)
        self.pdp = PDP()

    def chat(
        self,
        *,
        current: CurrentUser,
        message: str,
        conversation_id: Optional[int] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        # Authorize ai.use
        decision = self.pdp.evaluate(
            AuthzRequest(
                subject=Subject(
                    user_id=current.user.id,
                    roles=current.roles,
                    permissions=current.permissions,
                    status=current.user.status,
                ),
                action="ai.chat",
                resource={"type": "ai"},
                context={},
            )
        )
        if decision.decision != "ALLOW":
            return {
                "decision": "DENY",
                "reason_code": decision.reason_code,
                "reply": "No autorizado para usar el asistente IA.",
                "tool_result": None,
            }

        conv = self._get_or_create_conversation(current.user.id, conversation_id)
        user_msg = AiMessage(conversation_id=conv.id, role="user", content=message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        llm_reply = None
        proposal = self._propose_tool(message)
        if isinstance(proposal, dict) and proposal.get("_llm_reply"):
            llm_reply = proposal.pop("_llm_reply")
        if not proposal or not proposal.get("tool"):
            reply = self._redact_secrets(
                llm_reply
                or (
                    "Puedo ayudar con consultas de notas, asistencia, kardex o perfil. "
                    "No ejecuto SQL ni accedo a la base directamente."
                )
            )
            self._assistant_msg(conv.id, reply)
            return {
                "decision": "ALLOW",
                "reason_code": "NO_TOOL",
                "conversation_id": conv.id,
                "reply": reply,
                "proposal": None,
                "tool_result": None,
            }

        # Execute via Gateway (PEP) — CURRENT_USER binding + PDP
        gw = self.gateway.invoke(
            current=current,
            tool_name=proposal["tool"],
            parameters=proposal.get("parameters") or {},
            message_id=user_msg.id,
            ip=ip,
            user_agent=user_agent,
        )

        if gw.decision == "ALLOW":
            reply = self._format_tool_reply(gw.tool, gw.result)
        else:
            reply = (
                f"Solicitud denegada. Tool `{gw.tool}` → DENY "
                f"({gw.reason_code}). No se modificó ningún dato."
            )
        reply = self._redact_secrets(reply)

        self._assistant_msg(
            conv.id,
            reply + f" request_id={gw.request_id}",
        )
        return {
            "decision": gw.decision,
            "reason_code": gw.reason_code,
            "policy_id": gw.policy_id,
            "conversation_id": conv.id,
            "reply": reply,
            "proposal": proposal,
            "tool_result": gw.to_dict(),
        }

    def _format_tool_reply(self, tool: str, result: Any) -> str:
        if isinstance(result, dict) and result.get("error"):
            errors = {
                "STUDENT_PROFILE_REQUIRED": (
                    "Esta consulta aplica a un estudiante. "
                    "Inicie sesión como estudiante o indique el estudiante."
                ),
                "STUDENT_NOT_FOUND": "No encontré el perfil de estudiante.",
            }
            return errors.get(str(result["error"]), str(result["error"]))
        items = result if isinstance(result, list) else []
        if tool == "get_grades":
            if not items:
                return "No hay calificaciones registradas en el período activo."
            lines = ["Calificaciones del período activo:"]
            for row in items:
                name = (
                    row.get("subject_name")
                    or row.get("course_name")
                    or (f"Evaluación {row['evaluation_id']}" if row.get("evaluation_id") else "Evaluación")
                )
                score = row.get("official_grade")
                if score is None:
                    score = row.get("score")
                status = row.get("academic_status") or ""
                extra = f" ({status})" if status else ""
                lines.append(f"- {name}: {score}{extra}")
            return "\n".join(lines)
        if tool == "get_attendance":
            if not items:
                return "No hay registros de asistencia en el período activo."
            lines = ["Asistencia del período activo:"]
            for row in items:
                name = row.get("subject_name") or f"Sesión {row.get('session_id') or ''}"
                pct = row.get("attendance_pct")
                status = row.get("status") or ""
                if pct is not None:
                    lines.append(f"- {name}: {pct}%")
                else:
                    lines.append(f"- {name}: {status}".strip())
            return "\n".join(lines)
        if tool == "get_kardex":
            if not items:
                return "No hay registros en el kárdex."
            lines = ["Kárdex académico:"]
            for row in items:
                name = row.get("subject_name") or f"Asignatura {row.get('subject_id')}"
                grade = row.get("final_grade") or row.get("score") or "—"
                status = row.get("academic_status") or ""
                extra = f" ({status})" if status else ""
                lines.append(f"- {name}: {grade}{extra}")
            return "\n".join(lines)
        if tool == "get_student_profile" and isinstance(result, dict):
            code = result.get("student_code") or result.get("id")
            return f"Perfil de estudiante {code}. Estado: {result.get('status') or '—'}."
        if tool == "get_schedule":
            if not items:
                return "No hay horarios registrados."
            return f"Encontré {len(items)} franjas de horario."
        return f"Consulta `{tool}` completada."

    def _redact_secrets(self, text: str) -> str:
        cfg = AiSettingsService(self.db).runtime_config()
        if cfg and cfg.api_key and cfg.api_key in text:
            return text.replace(cfg.api_key, "[REDACTED]")
        return text

    def _propose_tool(self, message: str) -> Optional[dict[str, Any]]:
        cfg = AiSettingsService(self.db).runtime_config()
        if cfg is not None:
            try:
                parsed = propose_from_message(
                    api_key=cfg.api_key,
                    message=message,
                    model=cfg.model,
                    base_url=cfg.base_url,
                )
                if parsed.get("tool"):
                    out = {
                        "tool": parsed["tool"],
                        "parameters": parsed.get("parameters") or {},
                    }
                    if parsed.get("reply"):
                        out["_llm_reply"] = self._redact_secrets(str(parsed["reply"]))
                    return out
                if parsed.get("reply"):
                    return {"_llm_reply": self._redact_secrets(str(parsed["reply"]))}
            except Exception:
                pass
        text = message.lower()
        # Attack / grade mutation intent
        if re.search(r"(cambia|modifica|actualiza|pon|sube).*(nota|calific)", text) or (
            "nota" in text and ("100" in text or "cambiar" in text)
        ):
            return {
                "tool": "update_grade",
                "parameters": {
                    "evaluation_id": 1,
                    "student_id": "CURRENT_USER",
                    "score": 100,
                },
            }
        if re.search(r"(mis )?(calificaciones|notas|grades)", text):
            return {
                "tool": "get_grades",
                "parameters": {"student_id": "CURRENT_USER"},
            }
        if "asistencia" in text or "attendance" in text:
            return {
                "tool": "get_attendance",
                "parameters": {"student_id": "CURRENT_USER"},
            }
        if "kardex" in text:
            return {
                "tool": "get_kardex",
                "parameters": {"student_id": "CURRENT_USER"},
            }
        if "perfil" in text or "profile" in text:
            return {
                "tool": "get_student_profile",
                "parameters": {"student_id": "CURRENT_USER"},
            }
        if "reporte" in text or "report" in text:
            return {
                "tool": "generate_report",
                "parameters": {"report_type": "students", "format": "JSON"},
            }
        if "horario" in text or "schedule" in text:
            return {"tool": "get_schedule", "parameters": {}}
        return None

    def _get_or_create_conversation(
        self, user_id: int, conversation_id: Optional[int]
    ) -> AiConversation:
        if conversation_id:
            conv = self.db.get(AiConversation, conversation_id)
            if conv and conv.user_id == user_id:
                return conv
        conv = AiConversation(user_id=user_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def _assistant_msg(self, conversation_id: int, content: str) -> None:
        self.db.add(
            AiMessage(conversation_id=conversation_id, role="assistant", content=content)
        )
        self.db.commit()
