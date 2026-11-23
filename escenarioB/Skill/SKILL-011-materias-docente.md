# SKILL-011 — Docente en listado de Materias

**Spec:** SPEC-012  
**También aplica:** SPEC-009

## Rol del agente

Exponer en API y UI el nombre del/los docentes asignados a cada materia visible según el perfil del usuario (prioridad: estudiante).

## Procedimiento

1. Leer SPEC-012.
2. En `list_subjects` (`academic.py`):
   - Mantener filtro `owned_course_ids` / periodos.
   - Consultar cursos del ámbito + `assignments` + `teacher.user`.
   - Añadir `teachers: string[]` y `teachers_label` a cada `to_dict()`.
3. En `Pages.subjects` (`app.js`):
   - Columna **Docente(s)** con `teachers_label`.
   - Incluir nombres en `data-search`.
   - Ocultar Acciones si no hay permiso de edición.
4. Verificar con `est0001`: `GET /subjects` → `teachers` no vacío en materias con curso.

## Restricciones

- No inventar docentes: solo desde `assignments`.
- No filtrar materias solo en frontend.
- No requerir permiso `assignments.view` para ver el nombre (va embebido en subjects).
