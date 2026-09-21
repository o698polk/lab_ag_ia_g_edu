# Evidencia F6-O3 — Operación académica

| Campo | Valor |
|---|---|
| Fase | F6 / Oleada O3 |
| Skills | K-014, K-017, K-013, K-016, K-006 |
| Fecha | 2026-09-20 |

## Entregado

- Modelos: courses, teaching_assignments, enrollments, classrooms, schedules
- Alembic `0003_operations`
- APIs + ABAC check `/abac/teaching-assignment`
- Conflictos horario: TEACHER_BUSY / CLASSROOM_BUSY
- Periodo CLOSED bloquea altas
- Tests: **19 passed** (suite O1+O2+O3)

## Próximo

O4 — Asistencia, evaluaciones, calificaciones (ABAC docente asignado), kardex
