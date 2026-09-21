# Ref: BL-O6-005 | Skill: K-018 | Fase: F6
"""AI service — proposes tools only; never touches MySQL directly."""

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.gateway.pep import ToolGateway
from app.models import AiConversation, AiMessage
from app.policy.pdp import AuthzRequest, PDP, Subject


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

        proposal = self._propose_tool(message)
        if proposal is None:
            reply = (
                "Puedo ayudar con consultas de notas, asistencia, kardex o perfil. "
                "No ejecuto SQL ni accedo a la base directamente."
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
            reply = f"Tool `{gw.tool}` ejecutada (ALLOW / {gw.reason_code})."
        else:
            reply = (
                f"Solicitud denegada. Tool `{gw.tool}` → DENY "
                f"({gw.reason_code}). No se modificó ningún dato."
            )

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

    def _propose_tool(self, message: str) -> Optional[dict[str, Any]]:
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
