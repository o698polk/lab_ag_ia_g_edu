# SKILL-029 — Tools filtradas + intent NL + system_stats / reportes

**Spec:** SPEC-030  
**También aplica:** SPEC-016, SPEC-009, SPEC-029

## Rol del agente

Aplicar mínimo privilegio antes del LLM (`tools_for_user`, `scan_unauthorized_intent`) y endurecer `system_stats` + scope de reportes de estudiantes.

## Procedimiento

1. Leer SPEC-030.
2. En `registry.py`: `tools_for_user(user)`.
3. En `provider.py`: usar `tools_for_user` al armar `tools`.
4. En `ai_agent_log.py`: `scan_unauthorized_intent`.
5. Orquestador: invocar intent guard tras injection (con misma excepción de confirmación).
6. `handlers.system_stats` + `HANDLERS`: exigir visión institucional.
7. `reports.filter_students`: aplicar `owned_course_ids`.
8. Actualizar `politas_Agente_Ia.md` y `permisos_role.md`.

## Restricciones

- No eliminar el chequeo IAM del executor.
- No romper confirmación de mutaciones.
