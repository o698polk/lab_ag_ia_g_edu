# SKILL-027 — Dual-log bloqueos seguridad (LogIA + Auditoría) + UI roja

**Spec:** SPEC-028  
**También aplica:** SPEC-026, SPEC-016

## Rol del agente

Registrar en **LogIA y Auditoría** todo bloqueo por prompt injection/jailbreak o por mínimo privilegio / Zero Trust, y resaltar esas filas en rojo en ambos módulos.

## Procedimiento

1. Leer SPEC-028.
2. En `ai_agent_log.py` añadir `log_security_block` (LogIA + `audit.log_event`).
3. Orquestador: usar dual-log en inyección.
4. Executor: dual-log en tool desconocida, sin permiso, y denegaciones de privilegio/scope del handler.
5. Frontend `app.js` + `app.css`: clase `row-security-block` (fondo/borde rojo) en LogIA y Auditoría.
6. Actualizar PROMPTSMASTER y nota breve en `politas_Agente_Ia.md`.
7. Validar con llamadas sintéticas a `log_security_block` / flujo executor.

## Restricciones

- No registrar confirmaciones normales ni tool_calls exitosos como bloqueos.
- No romper exports existentes.
