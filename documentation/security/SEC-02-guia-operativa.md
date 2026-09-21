# SEC-02 — Guía operativa de seguridad

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 (+K-007) |
| Complemento | [SEC-01 OWASP](./SEC-01-owasp-assessment.md) |

## Principios

1. **Never Trust, Always Verify** — JWT no es AuthZ absoluta.
2. **Deny by Default** — sin permiso/política explícita → DENY.
3. **IA no toca MySQL** — solo propone tools; Gateway/PDP ejecutan o deniegan.
4. **Solo localhost** en este laboratorio.

## Roles y permisos

| Rol | Uso típico |
|---|---|
| ADMINISTRATOR | IAM, catálogo, reportes, auditoría |
| TEACHER | Cursos asignados, notas, asistencia |
| STUDENT | Consulta propia, kardex, IA de consulta |

ABAC docente: requiere `teaching_assignment` + periodo ACTIVE para calificar/asistencia.

## Incidentes conocidos del laboratorio (demostración)

| Escenario | Resultado esperado |
|---|---|
| Estudiante: “Cambia mi nota a 100” vía `/ai/chat` | DENY + `security_events` + nota intacta |
| Estudiante lee `/students/{otro}/grades` | `RESOURCE_NOT_OWNED` |
| Docente califica curso sin assignment | `CONTEXT_MISMATCH` |
| Login fallido | `LOGIN_FAILURE` |

## Operación diaria

1. Rotar `JWT_SECRET` si se filtra el `.env` local.
2. No compartir passwords demo fuera del lab.
3. Revisar `/api/v1/security/events` y `/api/v1/audit/events` tras pruebas de ataque.
4. Mantener `APP_HOST=127.0.0.1`.

## Residuales aceptados (ADR-013)

- Rate limit in-memory.
- Cobertura de ramas global &lt; 70% (ruta crítica OK).
- CSRF N/A (Bearer sin cookies de sesión).
