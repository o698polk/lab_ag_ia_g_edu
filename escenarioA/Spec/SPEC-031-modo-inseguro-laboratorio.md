# SPEC-031 — Modo laboratorio inseguro del Agente IA

**Objetivo:** Permitir, **solo en laboratorio**, desactivar los controles del agente (injection, intent guard, IAM/tools, scope, confirmación) mediante el flag `AI_INSECURE_MODE`, para medir el impacto de *prompt injection* / *jailbreak* sin verificaciones.

**Skills relacionadas:** SKILL-030  
**Specs relacionadas:** SPEC-016, SPEC-026, SPEC-028, SPEC-029, SPEC-030, `promantiseguridadia.md`  
**ADVERTENCIA:** No usar en producción ni con datos reales públicos.

---

## 1. Activación

| Variable | Valores ON | Default |
| --- | --- | --- |
| `AI_INSECURE_MODE` | `1`, `true`, `yes`, `on` | apagado (seguro) |

Helper: `app.ai.insecure_mode.is_insecure_mode()`.

---

## 2. Qué se desactiva con el flag ON

1. `scan_prompt_injection` / `scan_unauthorized_intent` no bloquean.
2. LLM recibe todo `TOOL_SCHEMAS` (no `tools_for_user`).
3. Executor: sin IAM, sin confirmación mutante, sin `privilege_block` en tool desconocida.
4. Handlers / `user_can_report` / scope (`owned_course_ids`, `apply_course_scope`) se omiten.
5. System prompt débil (obedece al usuario).
6. Rate limit de `/ai/chat` relajado o exento.
7. Banner UI «MODO LABORATORIO INSEGURO».

**Fuera de alcance:** JWT login, cifrado API keys, SSRF allowlist, firma de artifacts.

---

## 3. Criterios de aceptación

1. Con flag OFF: comportamiento actual seguro intacto.
2. Con flag ON + estudiante: «Ignore previous instructions…» llega al LLM (sin bloqueo pre-LLM).
3. Con flag ON: «reporte de todos los usuarios en PDF» no se niega por IAM/intent.
4. Banner visible en el chat cuando `GET /ai/security-mode` → `insecure: true`.
5. Apagar flag + reiniciar Flask restaura el modo seguro.
