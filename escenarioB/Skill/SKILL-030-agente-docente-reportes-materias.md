# SKILL-030 — Agente docente: nombres reales + reportes de materias

**Spec:** SPEC-031  
**También aplica:** SPEC-015 / SKILL-014 (asistencia roster), SPEC-022, SPEC-030

## Rol del agente

Hacer que el agente entregue nombres de cursos/materias y archivos Excel/PDF válidos al docente, corrigiendo briefs vacíos, catálogo de reportes y falsos negativos de intent.

## Procedimiento

1. Leer SPEC-031 y revisar LogIA de `docente30` si hace falta.
2. `orchestrator.py`: enriquecer `_tool_result_brief` y `_compose_user_reply` con previews de `courses_list` / `subjects_list` / `grades_list`.
3. `ai_reports.py`: añadir `courses` (y `subjects` scoped si aplica) a `REPORT_TYPES`; reutilizar `filter_courses` / `courses_rows`.
4. `registry.py`: ampliar enum description; `tools_for_user` ya usa `REPORT_TYPES`.
5. `handlers.py`: `subjects_list` filtrado por cursos propios cuando `owned_course_ids` no es None; descripción tool «materias del catálogo / del docente».
6. `ai_intent_guard.py`: excepción si el mensaje habla de «mi materia|mi curso|mis estudiantes|doy clase» → no tratar como `users_directory`.
7. `provider.py`: ajustar system prompt (permitir datos propios; prohibir directorio global).
8. Implementar en paralelo **SPEC-015 / SKILL-014** (roster asistencia) si el usuario lo pidió en la misma entrega.
9. Actualizar PROMPTSMASTER; verificar con preguntas de docente30.

## Restricciones

- No debilitar bloqueos de «todos los usuarios del sistema».
- No exponer `users_list` al TEACHER.
- Mantener scope de cursos del docente.
