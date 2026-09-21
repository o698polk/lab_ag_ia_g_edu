# API — Catálogo `/api/v1`

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| OpenAPI | http://127.0.0.1:8000/docs |

## Autenticación

Todas las rutas (salvo `health`, `ready`, `login`, `refresh`, `logout`) requieren:

```http
Authorization: Bearer <access_token>
```

El JWT **no** autoriza por sí solo: el servidor revalida usuario, roles y permisos (ADR-005).

## Health

| Método | Ruta | Auth |
|---|---|---|
| GET | `/health` | No |
| GET | `/ready` | No |

## Auth

| Método | Ruta | Permiso |
|---|---|---|
| POST | `/auth/login` | — |
| POST | `/auth/refresh` | — |
| POST | `/auth/logout` | — |
| GET | `/auth/me` | autenticado |
| POST | `/auth/change-password` | autenticado |

## IAM

| Método | Ruta | Permiso típico |
|---|---|---|
| GET/POST | `/users` | `users.view` / `users.create` |
| GET/PATCH/DELETE | `/users/{id}` | `users.*` |
| PUT | `/users/{id}/roles` | `users.update` |
| GET | `/roles`, `/permissions` | `roles.view`, `permissions.view` |
| PUT | `/roles/{code}/permissions` | `permissions.assign` |

## Catálogo académico

| Recurso | Rutas | Permisos |
|---|---|---|
| Careers | GET/POST `/careers` | `careers.*` |
| Subjects | GET/POST `/subjects` | `subjects.*` |
| Curricula | GET/POST `/curricula`, POST `.../subjects` | `curriculum.*` |
| Terms | GET/POST `/terms`, PATCH `.../status` | `terms.*` |
| Students | GET/POST `/students` | `students.*` |
| Teachers | GET/POST `/teachers` | `teachers.*` |

## Operaciones

| Recurso | Rutas | Notas |
|---|---|---|
| Courses | GET/POST `/courses` | |
| Teaching assignments | GET/POST `/teaching-assignments` | ABAC base |
| ABAC check | GET `/abac/teaching-assignment` | |
| Enrollments | GET/POST `/enrollments`, POST `.../cancel` | |
| Classrooms / Schedules | GET/POST | conflictos horario |

## Evaluación

| Recurso | Rutas | Notas |
|---|---|---|
| Evaluations | POST `/evaluations`, GET `/courses/{id}/evaluations` | docente asignado |
| Grades | PUT `/grades`, GET curso/estudiante/`me` | anti-IDOR |
| Attendance | POST sessions, PUT records, GET percent | |
| Kardex | PUT `/kardex`, GET `me` / estudiante | |

## Plataforma

| Recurso | Rutas |
|---|---|
| Dashboard | GET `/dashboard` |
| Reports | GET `/reports/catalog`, POST `/reports`, GET `/reports/logs` |
| Notifications | GET/POST `/notifications`, PUT `.../read` |
| User history | GET `/me/history`, GET `/users/{id}/history` |

## Zero Trust / IA

| Recurso | Rutas | Notas |
|---|---|---|
| AI chat | POST `/ai/chat` | propone tools → Gateway → PDP |
| Policies | GET `/policies` | `audit.view` |
| Tools | GET `/tools` | registry |
| Audit | GET `/audit/events` | ≠ historial usuario |
| Security | GET `/security/events` | LOGIN_FAILURE, TOOL_DENY, … |

## Códigos de denegación frecuentes

| `reason_code` | Significado |
|---|---|
| `PERMISSION_MISSING` | Falta permiso RBAC |
| `CONTEXT_MISMATCH` | Sin teaching_assignment / contexto |
| `RESOURCE_NOT_OWNED` | IDOR |
| `TERM_CLOSED` | Periodo cerrado |
| `TOOL_NOT_ALLOWED` | Tool sensible denegada (p.ej. STUDENT→update_grade) |
| `RATE_LIMITED` | Demasiados logins |
| `DEFAULT_DENY` | Sin regla ALLOW |
