# SPEC-028 — Bloqueos de seguridad resaltados en LogIA y Auditoría

**Objetivo:** Cuando el agente detecte y **bloquee** un intento de *prompt injection* / *jailbreak*, o un intento que viole **Zero Trust / mínimo privilegio** (tool sin permiso, tool desconocida, fuera de scope), el evento debe quedar registrado **tanto en LogIA como en Auditoría**, y en ambos módulos la fila debe resaltarse en **rojo**.

**Skills relacionadas:** SKILL-027  
**Specs relacionadas:** SPEC-026, SPEC-016, politicas del agente (`politas_Agente_Ia.md`)

---

## 1. Eventos a registrar (dual)

| Caso | LogIA `event_type` | LogIA `severity` | Auditoría `action` | Auditoría `module` |
| --- | --- | --- | --- | --- |
| Prompt injection / jailbreak bloqueado | `prompt_injection` (+ `policy_block`) | `block` | `AI_PROMPT_INJECTION_BLOCK` | `ai_security` |
| Sin permiso IAM en tool | `privilege_block` | `block` | `AI_PRIVILEGE_BLOCK` | `ai_security` |
| Fuera de scope / visibilidad | `privilege_block` | `block` | `AI_PRIVILEGE_BLOCK` | `ai_security` |
| Tool desconocida | `privilege_block` | `block` | `AI_UNKNOWN_TOOL_BLOCK` | `ai_security` |
| Reporte denegado por permiso | `privilege_block` | `block` | `AI_PRIVILEGE_BLOCK` | `ai_security` |

---

## 2. Requisitos técnicos

1. Función central `log_security_block(...)` que escriba LogIA + `AuditLog` en una sola llamada de política.
2. Orquestador: en bloqueo por `scan_prompt_injection`, invocar dual-log (además de o reemplazando los dos `log_agent_event` actuales, manteniendo tipos).
3. Executor: al denegar por permiso, tool desconocida, o resultado de handler con denegación de privilegio/scope → dual-log.
4. Frontend LogIA: filas con `severity=block` o `event_type` ∈ {`prompt_injection`,`policy_block`,`privilege_block`} → clase CSS roja.
5. Frontend Auditoría: filas con `module=ai_security` o acciones `AI_*_BLOCK` → clase CSS roja + badge.
6. Filtros: incluir `privilege_block` en select de eventos LogIA; módulo `ai_security` aparece en filtro de auditoría.

---

## 3. Criterios de aceptación

1. Mensaje tipo “ignore previous instructions…” → LogIA rojo + Auditoría `AI_PROMPT_INJECTION_BLOCK` en rojo.
2. Usuario STUDENT pide tool `users_list` (sin permiso) vía agente → LogIA `privilege_block` + Auditoría `AI_PRIVILEGE_BLOCK` en rojo.
3. Exports de LogIA/Audit siguen incluyendo estos registros.
4. SPEC/SKILL + PROMPTSMASTER actualizados.

---

## 4. Modelos sugeridos

Composer — leer SPEC-028 + SKILL-027.
