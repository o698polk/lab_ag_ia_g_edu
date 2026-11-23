# SKILL-021 — Respuestas fluidas del agente (sin dump de tools)

**Spec:** SPEC-022  
**También aplica:** SPEC-016, SPEC-017, SPEC-021

## Rol del agente

Eliminar respuestas con JSON/`[Tool …]` y entregar texto claro post-tool, estilo ChatGPT.

## Procedimiento

1. Leer SPEC-022.
2. `conversations.history_for_llm`: resumir tools sin JSON.
3. `orchestrator.py`:
   - `_compose_user_reply(tool_calls_log, artifacts)`
   - `_is_raw_tool_dump(text)` sanitizer
   - Tras tools: preferir composición; LLM2 solo con resúmenes; si dump → reemplazar.
   - Guardar assistant con `artifact_id` si hay reporte.
4. `ai-chat.js`: no renderizar burbujas que sean dump técnico.
5. Validar script: reply limpia + download_url presente.

## Restricciones

- No romper confirmación de mutaciones.
- No exponer secrets ni payloads completos en UI.
