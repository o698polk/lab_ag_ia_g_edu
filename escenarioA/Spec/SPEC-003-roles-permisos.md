# SPEC-003 — Roles y Permisos Granulares

## Roles

| Código | Descripción |
| --- | --- |
| ADMIN | Control total |
| RECTOR | Supervisión, reportes, sin edición |
| COORDINATOR | Carreras, mallas, horarios, cursos |
| TEACHER | Notas, asistencia, cursos asignados (sin kárdex ni dashboard; SPEC-009 / SPEC-014) |
| STUDENT | Consulta propia (sin kárdex ni dashboard; SPEC-009 / SPEC-014) |
| SECRETARY | Matrículas, estudiantes, reportes admin |
| REVIEWER | Revisión solo lectura + observaciones |
| AUDITOR | Logs y auditoría |
| GUARDIAN | Consulta del estudiante a cargo |
| IT_SUPPORT | Configuración técnica, sin datos académicos sensibles |

## Módulos y acciones

- `users`: view, create, edit, delete, login-as
- `roles`: view, create, edit, delete
- `permissions`: view, create, edit, delete, assign
- `students`, `teachers`, `careers`, `subjects`, `terms`, `courses`, `schedules`, `enrollments`: view, create, edit
- `curriculum`, `assignments`: view, manage
- `grades`, `attendance`: view, manage
- `kardex`: view, export
- `dashboard`: view
- `reports`: view, export, schedule
- `notifications`: view, send
- `history`: view
- `ai`: use, configure, view_logs
- `audit`: view
