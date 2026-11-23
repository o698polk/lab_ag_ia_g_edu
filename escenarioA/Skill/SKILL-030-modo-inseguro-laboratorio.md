# SKILL-030 — Modo laboratorio inseguro del Agente IA

**Spec:** SPEC-031  
**También aplica:** SPEC-016, SPEC-026, SPEC-028, SPEC-029, SPEC-030

## Rol del agente

Implementar `AI_INSECURE_MODE` que, solo cuando está activo, bypasea controles del agente para pruebas de prompt injection. Default = seguro.

## Procedimiento

1. Crear `app/ai/insecure_mode.py` con `is_insecure_mode()`.
2. Orquestador: saltar scanners si inseguro.
3. Provider/registry: tools completas + system prompt débil.
4. Executor: sin IAM / confirm / privilege_block.
5. Handlers + `user_can_report` + scope: omitir checks si inseguro.
6. Rate limit `/ai/chat` + endpoint `/ai/security-mode` + banner UI.
7. Documentar en `.env.example`, `guia_ejecute.md`, `politas_Agente_Ia.md`.

## Restricciones

- No desactivar JWT de login.
- No dejar el modo inseguro como default.
- No borrar el código de seguridad; solo bypassear con el flag.
