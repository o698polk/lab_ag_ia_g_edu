# Ref: BL-O6-005 | Skill: K-018 | Fase: F6
"""AI service — proposes tools only; never touches MySQL directly."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.deepseek import propose_from_message
from app.auth.deps import CurrentUser
from app.gateway.pep import ToolGateway
from app.models import AiConversation, AiMessage
from app.policy.pdp import AuthzRequest, PDP, Subject
from app.services.ai_settings_service import AiSettingsService

_OPEN_PREFIX = "[Políticas desactivadas] "
_REQUEST_ID_TAIL = re.compile(r"\s*request_id=[0-9a-fA-F-]{8,}\s*")


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
        case_id: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        guard = AiSettingsService(self.db).guard_status(current.user.id)
        enforced = bool(guard["policies_enforced"])
        scenario = "B" if enforced else "A"
        if enforced:
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
                    "policies_enforced": True,
                    "scenario": "B",
                }

        conv = self._get_or_create_conversation(current.user.id, conversation_id)
        user_msg = AiMessage(conversation_id=conv.id, role="user", content=message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        llm_reply = None
        proposal = self._propose_tool(message, current, case_id=case_id)
        if isinstance(proposal, dict) and proposal.get("_llm_reply"):
            llm_reply = proposal.pop("_llm_reply")
        if not proposal or not proposal.get("tool"):
            if not enforced:
                fallback = (
                    "Escenario A (políticas desactivadas): puedo ejecutar actualizaciones "
                    "y SQL de laboratorio (SELECT/INSERT/UPDATE/DELETE). "
                    "Indique el cambio o el SQL a ejecutar."
                )
            else:
                fallback = (
                    "Puedo ayudar con consultas de notas, asistencia, kardex o perfil. "
                    "Con políticas activas no ejecuto SQL ni accedo a la base directamente."
                )
            reply = self._redact_secrets(llm_reply or fallback)
            reply = self._clean_visible_text(reply)
            self._assistant_msg(conv.id, reply)
            return {
                "decision": "ALLOW",
                "reason_code": "NO_TOOL",
                "conversation_id": conv.id,
                "reply": reply,
                "proposal": None,
                "tool_result": None,
                "policies_enforced": enforced,
                "scenario": scenario,
                "case_id": case_id,
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
            if not enforced:
                reply = (
                    "Escenario A: políticas desactivadas. La herramienta se ejecutó "
                    "sin PDP ni control de mínimo privilegio. " + reply
                )
        else:
            reply = self._deny_reply(gw, current, enforced=enforced)
        reply = self._clean_visible_text(self._redact_secrets(reply))

        self._assistant_msg(conv.id, reply)
        return {
            "decision": gw.decision,
            "reason_code": gw.reason_code,
            "policy_id": gw.policy_id,
            "conversation_id": conv.id,
            "reply": reply,
            "proposal": proposal,
            "tool_result": gw.to_dict(),
            "policies_enforced": enforced,
            "scenario": scenario,
            "case_id": proposal.get("_case_id") or case_id,
        }

    def _deny_reply(self, gw: Any, current: CurrentUser, *, enforced: bool) -> str:
        role = (current.roles or ["usuario"])[0]
        tool = gw.tool
        reason = gw.reason_code
        if reason == "RESOURCE_NOT_OWNED":
            detail = "No puedes consultar ni modificar datos de otro estudiante."
        elif reason == "TOOL_NOT_ALLOWED":
            detail = f"El rol {role} no puede ejecutar `{tool}`."
        elif reason == "ROLE_NOT_ALLOWED":
            detail = f"La herramienta `{tool}` no pertenece al rol {role}."
        elif reason == "PERMISSION_MISSING":
            detail = f"Tu cuenta no tiene el permiso necesario para `{tool}`."
        else:
            detail = f"Solicitud denegada ({reason})."
        if enforced:
            return f"Escenario B: {detail} No se modificó ningún dato."
        return detail

    def _format_tool_reply(self, tool: str, result: Any) -> str:
        if isinstance(result, dict) and result.get("error"):
            errors = {
                "STUDENT_PROFILE_REQUIRED": (
                    "Esta consulta aplica a un estudiante. "
                    "Inicie sesión como estudiante o indique el estudiante."
                ),
                "STUDENT_NOT_FOUND": "No encontré el perfil de estudiante.",
                "EVALUATION_NOT_FOUND": "No encontré la evaluación indicada.",
            }
            return errors.get(str(result["error"]), str(result["error"]))
        items = result if isinstance(result, list) else []
        if tool == "get_grades":
            if not items:
                return "No hay calificaciones registradas en el período activo."
            lines = ["Calificaciones por materia (parciales):"]
            for row in items:
                name = row.get("subject_name") or row.get("course_name") or "Materia"
                p1 = row.get("first_partial")
                p2 = row.get("second_partial")
                final = row.get("official_grade")
                if final is None:
                    final = row.get("final_average")
                if final is None:
                    final = row.get("score")
                sup = row.get("recovery_grade")
                status = row.get("academic_status") or ""
                bits = [
                    f"1.er parcial={p1 if p1 is not None else '—'}",
                    f"2.º parcial={p2 if p2 is not None else '—'}",
                    f"nota final={final if final is not None else '—'}",
                    f"supletorio={sup if sup is not None else '—'}",
                ]
                extra = f" ({status})" if status else ""
                lines.append(f"- {name}: " + " · ".join(bits) + extra)
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
        if tool == "update_grade" and isinstance(result, dict):
            return (
                f"Nota actualizada a {result.get('score')} "
                f"(evaluación {result.get('evaluation_id')}, estudiante {result.get('student_id')})."
            )
        if tool == "execute_sql" and isinstance(result, dict):
            if result.get("error"):
                return f"SQL no aplicado: {result.get('error')}."
            if "rows" in result:
                rows = result.get("rows") or []
                preview = rows[:10]
                lines = [f"SQL ejecutado · {result.get('row_count', 0)} fila(s):"]
                for row in preview:
                    lines.append(f"- {row}")
                return "\n".join(lines)
            return (
                f"SQL ejecutado · {result.get('row_count', 0)} fila(s) afectadas "
                f"({result.get('status') or 'OK'})."
            )
        if tool == "get_dashboard" and isinstance(result, dict):
            view = result.get("view") or result.get("role") or ""
            indicators = result.get("indicators") or {}
            bits = [f"{k}={v}" for k, v in list(indicators.items())[:8]]
            return f"Dashboard {view}: " + (", ".join(bits) if bits else "sin indicadores.")
        if tool == "generate_report" and isinstance(result, dict):
            return self._format_report_reply(result)
        if tool.startswith("list_") or tool in {
            "get_user",
            "create_user",
            "update_user",
            "create_subject",
            "create_career",
            "create_course",
            "create_student",
            "create_teacher",
            "create_notification",
        }:
            if isinstance(result, dict):
                label = result.get("name") or result.get("code") or result.get("username") or result.get("id")
                return f"Operación `{tool}` completada: {label}."
            if not items:
                return f"No hay registros para `{tool}` con esos filtros."
            lines = [f"{len(items)} registro(s):"]
            for row in items[:20]:
                if not isinstance(row, dict):
                    lines.append(f"- {row}")
                    continue
                label = (
                    row.get("name")
                    or row.get("code")
                    or row.get("username")
                    or row.get("student_code")
                    or row.get("teacher_code")
                    or row.get("title")
                    or row.get("id")
                )
                extra = row.get("status") or row.get("email") or ""
                lines.append(f"- {label}" + (f" ({extra})" if extra else ""))
            return "\n".join(lines)
        return f"Consulta `{tool}` completada."

    def _format_report_reply(self, result: dict[str, Any]) -> str:
        from app.services.platform_service import REPORT_TYPES

        rtype = str(result.get("report_type") or "reporte")
        title = REPORT_TYPES.get(rtype, rtype.replace("_", " ").title())
        fmt = str(result.get("format") or "JSON")
        rows = self._report_rows(result)
        count = result.get("row_count")
        if count is None:
            count = len(rows)
        term = ""
        if rows and isinstance(rows[0], dict):
            term = str(rows[0].get("term_name") or rows[0].get("term_code") or "")
        head = f"{title} ({fmt})"
        if term:
            head += f" · periodo {term}"
        head += f" · {count} registro(s)."
        if not rows:
            return head + " No hay datos en el periodo autorizado."
        lines = [head]
        preview = rows[:20]
        for row in preview:
            if isinstance(row, dict):
                lines.append("- " + self._report_row_label(row))
            else:
                lines.append(f"- {row}")
        leftover = int(count) - len(preview)
        if leftover > 0:
            lines.append(f"... y {leftover} registro(s) más.")
        return "\n".join(lines)

    @staticmethod
    def _report_rows(result: dict[str, Any]) -> list[Any]:
        content = result.get("content")
        if isinstance(content, list):
            return content
        if not isinstance(content, str) or not content.strip():
            return []
        fmt = str(result.get("format") or "").upper()
        if fmt == "JSON" or content.lstrip().startswith("["):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                return []
            return parsed if isinstance(parsed, list) else []
        if fmt == "CSV":
            lines = [ln for ln in content.splitlines() if ln.strip()]
            return lines[1:21]
        return []

    @staticmethod
    def _report_row_label(row: dict[str, Any]) -> str:
        bits: list[str] = []
        who = row.get("student_code") or row.get("teacher_code") or row.get("code") or row.get("name")
        if who:
            bits.append(str(who))
        elif row.get("student_id"):
            bits.append(f"estudiante {row['student_id']}")
        elif row.get("teacher_id"):
            bits.append(f"docente {row['teacher_id']}")
        subject = row.get("subject_name") or row.get("course_name")
        if subject:
            bits.append(str(subject))
        elif row.get("course_id"):
            bits.append(f"curso {row['course_id']}")
        if row.get("term_name"):
            bits.append(str(row["term_name"]))
        grade = row.get("final_grade")
        if grade is None:
            grade = row.get("score")
        if grade is None:
            grade = row.get("average")
        if grade not in (None, ""):
            bits.append(f"nota {grade}")
        status = row.get("academic_status") or row.get("status")
        if status:
            bits.append(str(status))
        return " · ".join(bits) if bits else str(row.get("id") or "fila")

    @staticmethod
    def _clean_visible_text(text: str) -> str:
        out = str(text or "")
        if out.startswith(_OPEN_PREFIX):
            out = out[len(_OPEN_PREFIX) :]
        return _REQUEST_ID_TAIL.sub(" ", out).strip()

    def _redact_secrets(self, text: str) -> str:
        cfg = AiSettingsService(self.db).runtime_config()
        if cfg and cfg.api_key and cfg.api_key in text:
            return text.replace(cfg.api_key, "[REDACTED]")
        return text

    def _propose_tool(
        self,
        message: str,
        current: CurrentUser | None = None,
        case_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        from app.eval.cases import get_case, match_case

        roles = current.roles if current else []
        case = None
        if case_id:
            found = get_case(case_id)
            if found and (not roles or found["role"] in roles):
                case = found
        if case is None:
            case = match_case(message, roles)
        if case:
            return {
                "tool": case["expected_tool"],
                "parameters": dict(case.get("parameters") or {}),
                "_case_id": case["case_id"],
            }
        sql_proposal = self._sql_proposal(message)
        if sql_proposal:
            return sql_proposal
        mutation = self._mutation_proposal(message)
        if mutation:
            return mutation
        keywords = self._keyword_proposal(message, current)
        if keywords:
            return keywords
        cfg = AiSettingsService(self.db).runtime_config()
        if cfg is None:
            return None
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
            return None
        return None

    def _keyword_proposal(
        self, message: str, current: CurrentUser | None = None
    ) -> Optional[dict[str, Any]]:
        text = message.lower()
        other = self._other_student_id(text)
        roles = current.roles if current else []
        own_scope = other or ("CURRENT_USER" if "STUDENT" in roles else None)
        if re.search(r"(mis )?(calificaciones|notas|grades)", text):
            params = {"student_id": own_scope} if own_scope else {}
            return {"tool": "get_grades", "parameters": params}
        if "asistencia" in text or "attendance" in text:
            params = {"student_id": own_scope} if own_scope else {}
            return {"tool": "get_attendance", "parameters": params}
        if "kardex" in text or "kárdex" in text:
            return {
                "tool": "get_kardex",
                "parameters": {"student_id": other or "CURRENT_USER"},
            }
        if "perfil" in text or "profile" in text:
            return {
                "tool": "get_student_profile",
                "parameters": {"student_id": other or "CURRENT_USER"},
            }
        if "reporte" in text or "report" in text:
            if "STUDENT" in roles and re.search(r"(mis |mi )(nota|calific)", text):
                return {
                    "tool": "get_grades",
                    "parameters": {"student_id": "CURRENT_USER"},
                }
            return {
                "tool": "generate_report",
                "parameters": {
                    "report_type": self._report_type_from_text(text),
                    "format": "JSON",
                },
            }
        if "horario" in text or "schedule" in text:
            if re.search(r"(elimina|borra|quita)", text):
                found = re.search(r"horario\s+(\d+)", text)
                return {
                    "tool": "delete_schedule",
                    "parameters": {"schedule_id": int(found.group(1)) if found else 1},
                }
            if re.search(r"(crea|nuevo|registra)", text):
                return {"tool": "create_schedule", "parameters": {}}
            return {"tool": "get_schedule", "parameters": {}}
        if "matrícula" in text or "matricula" in text or "enrollment" in text:
            if re.search(r"(lista|consulta|muestra|ver)", text):
                return {"tool": "list_enrollments", "parameters": self._filter_params(text)}
            if "cancel" in text or "anula" in text or "quita" in text:
                return {"tool": "cancel_enrollment", "parameters": {"enrollment_id": 1}}
            return {
                "tool": "create_enrollment",
                "parameters": {"student_id": other or 2, "course_id": 1, "term_id": 1},
            }
        module = self._module_keyword(text)
        if module:
            return module
        return None

    @staticmethod
    def _filter_params(text: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if re.search(r"activ[oa]s", text):
            params["status"] = "ACTIVE"
        elif re.search(r"inactiv|cerrad|closed", text):
            params["status"] = "CLOSED"
        found = re.search(r"(?:filtra|busca|c[oó]digo|codigo)\s+([a-zA-Z0-9_\-]+)", text)
        if found:
            params["q"] = found.group(1)
        return params

    def _module_keyword(self, text: str) -> Optional[dict[str, Any]]:
        write = bool(re.search(r"\b(crea|crear|registra|nuevo|agrega|alta)\b", text))
        update = bool(re.search(r"\b(actualiza|modifica|cambia|edita|altera)\b", text))
        delete = bool(re.search(r"\b(elimina|borra|quita)\b", text))
        operate = bool(
            re.search(
                r"\b(lista|listar|consulta|consultar|muestra|mostrar|filtra|busca|"
                r"crea|crear|registra|nuevo|agrega|alta|actualiza|modifica|cambia|"
                r"edita|altera|elimina|borra|quita|dashboard|tablero)\b",
                text,
            )
        )
        if not operate:
            return None
        filters = self._filter_params(text)
        pairs = [
            (("usuarios?", "users?"), "list_users", "create_user", "update_user"),
            (("roles?", "rol(?:es)?"), "list_roles", "create_role", None),
            (("permisos?", "permissions?"), "list_permissions", None, None),
            (("carreras?", "careers?"), "list_careers", "create_career", "set_career_status"),
            (("asignaturas?", "materias?", "subjects?"), "list_subjects", "create_subject", "set_subject_status"),
            (("mallas?", "curricul\\w*"), "list_curricula", "create_curriculum", None),
            (("periodos?", "t[eé]rminos?", "terms?"), "list_terms", "create_term", "set_term_status"),
            (("estudiantes?", "students?"), "list_students", "create_student", "set_student_status"),
            (("docentes?", "teachers?", "profesores?"), "list_teachers", "create_teacher", "set_teacher_status"),
            (("cursos?", "paralelos?", "courses?"), "list_courses", "create_course", "update_course"),
            (("asignaciones?", "assignments?"), "list_assignments", "create_assignment", None),
            (("aulas?", "classrooms?", "salones?"), "list_classrooms", "create_classroom", None),
            (("avisos?", "notificaciones?"), "list_notifications", "create_notification", None),
            (("dashboard", "resumen", "tablero"), "get_dashboard", None, None),
            (("auditor[ií]a", "audit"), "list_audit", None, None),
        ]
        for keys, listed, created, updated in pairs:
            if not any(re.search(rf"\b{key}\b", text) for key in keys):
                continue
            if write and created:
                params = dict(filters)
                token = re.search(r"(?:asignatura|materia|carrera|usuario|rol)\s+([A-Za-z0-9_\-]+)", text)
                if created == "create_subject" and token:
                    params["code"] = token.group(1).upper()
                    params["name"] = token.group(1).upper()
                if created == "create_career" and token:
                    params["code"] = token.group(1).upper()
                    params["name"] = token.group(1).upper()
                if created == "create_user" and token:
                    params["username"] = token.group(1).lower()
                return {"tool": created, "parameters": params}
            if delete and listed == "list_users":
                found = re.search(r"usuario\s+(\d+)", text)
                return {"tool": "delete_user", "parameters": {"user_id": int(found.group(1)) if found else 1}}
            if update and updated:
                return {"tool": updated, "parameters": dict(filters)}
            if listed == "get_dashboard":
                return {"tool": listed, "parameters": {}}
            return {"tool": listed, "parameters": dict(filters)}
        return None

    @staticmethod
    def _report_type_from_text(text: str) -> str:
        if re.search(r"\b(docentes?|teachers?|profesores?)\b", text):
            return "teachers"
        if re.search(r"\b(estudiantes?|students?)\b", text) and not re.search(
            r"acad[eé]mic", text
        ):
            return "students"
        if re.search(r"\b(asistencias?|attendance)\b", text):
            return "attendance"
        if re.search(r"\b(promedios?|averages?)\b", text):
            return "averages"
        if re.search(r"\b(kardex|kárdex)\b", text):
            return "kardex"
        if re.search(r"\b(carreras?|careers?)\b", text):
            return "career"
        if re.search(r"\b(matr[ií]culas?|enrollments?)\b", text):
            return "enrollments"
        if re.search(r"\b(calific|notas?|grades?)\b", text):
            return "grades"
        if re.search(r"acad[eé]mic|periodo|autorizad", text):
            return "term_academic"
        return "students"

    @staticmethod
    def _other_student_id(text: str) -> int | None:
        found = re.search(r"estudiante\s+(\d+)", text)
        if found:
            return int(found.group(1))
        return None

    @staticmethod
    def _sql_proposal(message: str) -> Optional[dict[str, Any]]:
        text = (message or "").strip()
        if not text:
            return None
        fenced = re.search(r"```(?:sql)?\s*([\s\S]+?)```", text, re.IGNORECASE)
        if fenced:
            sql = fenced.group(1).strip()
            if sql:
                return {"tool": "execute_sql", "parameters": {"sql": sql}}
        tagged = re.search(
            r"(?:ejecuta(?:r)?|corre|run)\s+(?:este\s+)?sql\s*[:\-]?\s*([\s\S]+)$",
            text,
            re.IGNORECASE,
        )
        if tagged:
            sql = tagged.group(1).strip().strip("`")
            if sql:
                return {"tool": "execute_sql", "parameters": {"sql": sql}}
        compact = re.sub(r"\s+", " ", text).strip()
        if re.match(
            r"^(select|insert|update|delete|with)\b",
            compact,
            re.IGNORECASE,
        ):
            return {"tool": "execute_sql", "parameters": {"sql": compact}}
        if re.search(
            r"\b(sql|base de datos|mysql|query)\b",
            text,
            re.IGNORECASE,
        ) and re.search(
            r"\b(select|insert|update|delete|ejecuta|correr|consulta)\b",
            text,
            re.IGNORECASE,
        ):
            found = re.search(
                r"((?:select|insert|update|delete|with)\b[\s\S]+)$",
                text,
                re.IGNORECASE,
            )
            if found:
                return {
                    "tool": "execute_sql",
                    "parameters": {"sql": found.group(1).strip()},
                }
        return None

    def _mutation_proposal(self, message: str) -> Optional[dict[str, Any]]:
        text = message.lower()
        if not (
            re.search(r"(cambia|modifica|actualiza|pon|sube).*(nota|calific)", text)
            or ("nota" in text and ("100" in text or "cambiar" in text))
        ):
            return None
        student_id: Any = "CURRENT_USER"
        found = re.search(r"estudiante\s+(\d+)", text)
        if found:
            student_id = int(found.group(1))
        # Lab-sensitive write still uses evaluation_id for PDP battery compatibility;
        # academic UI/tools only expose subject partials (0–10).
        evaluation_id = 1
        found_ev = re.search(r"evaluaci[oó]n\s+(\d+)", text)
        if found_ev:
            evaluation_id = int(found_ev.group(1))
        score = 10
        found_score = re.search(r"\ba\s+(\d{1,3}(?:\.\d+)?)\b", text)
        if found_score:
            value = float(found_score.group(1))
            if 0 <= value <= 100:
                score = value if value <= 10 else round(value / 10, 2)
        return {
            "tool": "update_grade",
            "parameters": {
                "evaluation_id": evaluation_id,
                "student_id": student_id,
                "score": score,
            },
        }

    def list_conversations(self, user_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = list(
            self.db.scalars(
                select(AiConversation)
                .where(AiConversation.user_id == user_id)
                .order_by(AiConversation.id.desc())
                .limit(limit)
            )
        )
        items: list[dict[str, Any]] = []
        for conv in rows:
            msgs = list(
                self.db.scalars(
                    select(AiMessage)
                    .where(AiMessage.conversation_id == conv.id)
                    .order_by(AiMessage.id.asc())
                )
            )
            preview = ""
            for msg in msgs:
                if msg.role == "user" and msg.content:
                    preview = msg.content[:160]
                    break
            items.append(
                {
                    "id": conv.id,
                    "started_at": conv.started_at,
                    "preview": preview,
                    "message_count": len(msgs),
                }
            )
        return items

    def get_conversation(self, user_id: int, conversation_id: int) -> Optional[dict[str, Any]]:
        conv = self.db.get(AiConversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            return None
        msgs = list(
            self.db.scalars(
                select(AiMessage)
                .where(AiMessage.conversation_id == conv.id)
                .order_by(AiMessage.id.asc())
            )
        )
        return {
            "id": conv.id,
            "started_at": conv.started_at,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": self._clean_visible_text(msg.content),
                    "created_at": msg.created_at,
                }
                for msg in msgs
            ],
        }

    def start_conversation(self, user_id: int) -> dict[str, Any]:
        conv = AiConversation(user_id=user_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return {
            "id": conv.id,
            "started_at": conv.started_at,
            "preview": "",
            "message_count": 0,
        }

    def _get_or_create_conversation(
        self, user_id: int, conversation_id: Optional[int]
    ) -> AiConversation:
        if conversation_id:
            conv = self.db.get(AiConversation, conversation_id)
            if conv and conv.user_id == user_id:
                return conv
        latest = self.db.scalar(
            select(AiConversation)
            .where(AiConversation.user_id == user_id)
            .order_by(AiConversation.id.desc())
        )
        if latest:
            return latest
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
