# SKILL-028 — LogIA pregunta + bloqueo escalada de rol

**Spec:** SPEC-029  
**También aplica:** SPEC-026, SPEC-028

## Rol del agente

Implementar `user_question` en LogIA y ampliar `scan_prompt_injection` con patrones de escalada/spoofing de rol.

## Procedimiento

1. Leer SPEC-029.
2. Añadir columna `user_question` al modelo `AIAgentLog` + `ensure_schema` (ALTER si falta).
3. Extender `log_agent_event` / `log_security_block` con `user_question`.
4. Orquestador: pasar `message` como `user_question` en todos los logs del turno.
5. Ampliar `_INJECTION_PATTERNS` + `kind=privilege_escalation`.
6. Frontend LogIA: columna Pregunta; exports y búsqueda.
7. Actualizar `politas_Agente_Ia.md` y `permisos_role.md`.

## Restricciones

- No bloquear consultas legítimas de rol/permisos propios.
- Mantener excepción de confirmación (`pending_action`).
