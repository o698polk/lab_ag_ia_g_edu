# SKILL-029 — Agente: bloqueo por rol y permisos

**Spec:** SPEC-030  
**También aplica:** SPEC-003, SPEC-016, SPEC-028, SPEC-029, SKILL-027, SKILL-028

## Rol del agente

Asegurar que el agente IA solo ofrezca y ejecute lo que el rol del usuario permite: filtrar tools, bloquear intents NL no autorizados, acotar reportes por scope y registrar bloqueos en LogIA.

## Procedimiento

1. Leer SPEC-030 y la matriz en `permisos_role.md` / seed.
2. Crear `App/backend/app/services/ai_intent_guard.py` con `scan_unauthorized_intent(user, message)`.
3. En `registry.py` (o módulo de política): `tools_for_user(user)` filtrando `TOOL_SCHEMAS` según `HANDLERS` + reglas de `system_stats` / reportes.
4. `provider.py` `call_llm`: usar `tools_for_user(user)` en lugar del catálogo completo; enriquecer system prompt con roles del usuario y regla de mínimo privilegio.
5. `orchestrator.py`: tras `scan_prompt_injection`, invocar `scan_unauthorized_intent`; si bloquea → respuesta de política + `log_security_block` (`privilege_block`) + `user_question`.
6. `reports.py` `filter_students`: aplicar scope `owned_course_ids` como `students_list`.
7. `handlers.py`: endurecer `system_stats` con los mismos permisos; `reports_list_types` alineado a `user_can_report` (sin exigir solo `reports.view` si el dominio permite generar).
8. Actualizar PROMPTSMASTER, `permisos_role.md` (sección agente) y `politas_Agente_Ia.md`.
9. Validar casos TEACHER / STUDENT del criterio de aceptación SPEC-030.

## Restricciones

- No debilitar anti-injection SPEC-029.
- No romper confirmación de mutaciones.
- Docente debe seguir pudiendo notas/asistencia/estudiantes de **sus** cursos.
- ADMIN conserva bypass.
