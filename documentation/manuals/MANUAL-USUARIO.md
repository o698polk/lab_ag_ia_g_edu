# Manual de usuario — SIGA

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| Audiencia | Estudiante / Docente |

## Acceso

1. Abrir http://127.0.0.1:8000/ui/
2. Iniciar sesión (`admin` / `teacher1` / `student1` en el seed de laboratorio).
3. Usar la navegación: **Dashboard**, **Notas**, **Asistencia** (docente/admin), **Asistente IA**, **Avisos**.

La UI es un cliente Bootstrap; **no autoriza**. ALLOW/DENY lo decide el servidor (RBAC + ABAC + PDP/Gateway).

### Pantallas

| Módulo | Qué hace |
|---|---|
| Dashboard | Indicadores por rol (`GET /dashboard`) |
| Notas | Mis notas / kardex · listar curso · registrar nota (docente) |
| Asistencia | Crear sesión · marcar · % asistencia |
| Asistente IA | Chat mock; propuestas de tools pasan por Gateway |
| Avisos | Listar y marcar leídas |

Alternativa: API con cliente HTTP (`/docs`).

## Estudiante

| Acción | Cómo |
|---|---|
| Ver mis notas | `GET /api/v1/me/grades` |
| Ver mi kardex | `GET /api/v1/me/kardex` |
| Ver dashboard | `GET /api/v1/dashboard` |
| Notificaciones | `GET /api/v1/notifications` · marcar leída `PUT .../read` |
| Historial de actividad | `GET /api/v1/me/history` |
| Asistente IA (consulta) | `POST /api/v1/ai/chat` con mensajes como “Cuáles son mis calificaciones?” |

**No puede:** modificar notas, asistencia, matrículas ni ver datos de otros estudiantes.

Si la IA propone cambiar una nota, el sistema **deniega** la operación; su calificación no cambia.

## Docente

| Acción | Cómo |
|---|---|
| Dashboard | `GET /api/v1/dashboard` (vista TEACHER) |
| Crear evaluación | `POST /api/v1/evaluations` (solo cursos asignados) |
| Registrar nota | `PUT /api/v1/grades` |
| Asistencia | `POST /api/v1/attendance/sessions` · `PUT /api/v1/attendance/records` |
| Reportes | `POST /api/v1/reports` (HTML/CSV/JSON) |

Sin `teaching_assignment` en el curso/periodo, el sistema responde **DENY** (`CONTEXT_MISMATCH`).

## Cambiar contraseña

```http
POST /api/v1/auth/change-password
{ "current_password": "...", "new_password": "..." }
```

## Soporte

Problemas de acceso o permisos: contactar al administrador del laboratorio.
Documentación técnica: `documentation/D00-index.md`.
