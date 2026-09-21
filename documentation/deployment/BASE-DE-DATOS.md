# Base de datos

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| Ref | A02 ERD · Alembic · ADR-008 |

## Motor

| Entorno | Motor |
|---|---|
| Laboratorio local | MySQL 8+ (XAMPP) |
| Tests automatizados | SQLite `:memory:` (StaticPool) |

## Migraciones Alembic

Ubicación: `app/backend/alembic/versions/`

| Rev | Contenido |
|---|---|
| `0001_iam` | users, roles, permissions, sessions, refresh |
| `0002_academic` | careers, subjects, terms, students, teachers, … |
| `0003_operations` | courses, assignments, enrollments, schedules |
| `0004_evaluation` | attendance, evaluations, grades, kardex |
| `0005_platform` | reports, notifications, user_history |
| `0006_zero_trust` | audit/security events, tools, AI messages |

```powershell
cd app\backend
alembic upgrade head
alembic current
```

## Seed IAM

```powershell
python scripts\seed_iam.py
```

Usuarios demo (cambiar en producción; solo lab):

| Usuario | Rol | Password demo |
|---|---|---|
| `admin` | ADMINISTRATOR | `Admin123!` |
| `teacher1` | TEACHER | `Teacher123!` |
| `student1` | STUDENT | `Student123!` |

## Dominios de datos

```text
IAM → Académico → Operaciones → Evaluación → Plataforma → Zero Trust / IA
```

Separación conceptual:

| Tabla / concepto | Pregunta |
|---|---|
| `user_history_events` | ¿Qué hizo el usuario en la app? |
| `audit_events` | ¿Qué evidencia técnica de operación? |
| `security_events` | ¿Qué señal de seguridad (DENY, LOGIN_FAILURE, …)? |

ERD completo: `documentation/architecture/A02-erd.md`.

## Integridad

- PK/FK, unique compuestos (enrollment, assignment, grade)
- Soft delete en usuarios/estudiantes/docentes críticos
- Periodo `CLOSED` bloquea escrituras académicas normales
