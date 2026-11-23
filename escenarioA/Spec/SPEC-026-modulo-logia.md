# SPEC-026 — Módulo LogIA (auditoría del agente)

**Objetivo:** Módulo **LogIA** que registra acciones del agente, bloqueos anti prompt-injection, comportamiento por usuario/rol; con búsqueda, filtros y export Excel / PDF / JSON.

**Skills:** SKILL-025  
**Relacionadas:** SPEC-016, SPEC-019, SPEC-023

## 1. Modelo `ai_agent_logs` (LogIA)

| Campo | Tipo | Descripción |
| --- | --- | --- |
| id | int PK | |
| user_id | FK nullable | Actor |
| username | string | Snapshot |
| role_codes | string/JSON | Roles al momento |
| conversation_id | string nullable | Hilo |
| event_type | string | `chat`, `tool_call`, `tool_error`, `report`, `policy_block`, `prompt_injection`, `confirm`, `conversation_*` |
| severity | string | `info`, `warn`, `block`, `error` |
| summary | string | Texto corto |
| detail | text/JSON | Payload sanitizado |
| keywords | string | Texto indexable (message + tools) |
| channel | string | panel/float/api |
| created_at | datetime | |

## 2. Anti prompt-injection

Antes de enviar al LLM, escanear el mensaje. Si hay patrones de jailbreak / inyección:

1. Registrar `event_type=prompt_injection` / `policy_block`, `severity=block`.
2. No ejecutar tools peligrosas; responder mensaje de política.
3. Patrones: “ignore previous instructions”, “revela system prompt”, intentos de bypass de roles, etc. (lista configurable).

## 3. API

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/ai/agent-logs` | `ai.view_logs` |
| GET | `/reports/ai_logs.xlsx\|pdf\|json` o `/ai/agent-logs/export` | `ai.view_logs` + export |

Query filters: `q`, `user_id`, `username`, `conversation_id`, `event_type`, `severity`, `from`, `to`, `role`.

## 4. UI módulo `logia`

- Nav: “LogIA”, perm `ai.view_logs`.
- Tabla + `moduleHeader` con filtros dates/status/role + búsqueda.
- Export Excel, PDF, JSON.
- Instrumentar orchestrator/executor para escribir logs.

## Criterios

1. Cada chat/tool/block deja fila en LogIA.
2. Filtros reducen la tabla; export respeta filtros.
3. Prompt de inyección → bloque + registro `policy_block`.
