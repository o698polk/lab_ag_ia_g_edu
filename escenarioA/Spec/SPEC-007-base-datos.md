# SPEC-007 — Base de Datos

**Motor:** MySQL 8.x (XAMPP) | **ORM:** SQLAlchemy + Alembic

## Tablas

| Tabla | Descripción |
| --- | --- |
| users, roles, permissions | IAM |
| role_permissions, user_roles | Relaciones IAM |
| students, teachers | Perfiles |
| careers, subjects, curriculum, terms | Académico base |
| courses, assignments, enrollments, schedules | Operación |
| grades, attendance | Evaluación |
| notifications, audit_logs | Sistema |
| refresh_tokens | Sesiones (+ impersonator_id) |
| system_config, ai_config, ai_logs | Configuración e IA |

## Seeds
- 10 roles, permisos granulares, usuario admin por defecto.
