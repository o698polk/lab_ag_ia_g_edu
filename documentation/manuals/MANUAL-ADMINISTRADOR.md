# Manual de administrador — SIGA

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| Audiencia | ADMINISTRATOR / operador del laboratorio |

## Puesta en marcha

Seguir [`../deployment/INSTALACION.md`](../deployment/INSTALACION.md) y [`../deployment/CONFIGURACION.md`](../deployment/CONFIGURACION.md).

Usuarios seed (solo lab): `admin` / `teacher1` / `student1` — ver `scripts/seed_iam.py`.

## Operaciones IAM

1. Crear usuarios: `POST /api/v1/users` con `role_codes`.
2. Asignar roles: `PUT /api/v1/users/{id}/roles`.
3. Ajustar permisos de rol: `PUT /api/v1/roles/{code}/permissions`.
4. Bloquear cuenta: `PATCH /api/v1/users/{id}/status` → `BLOCKED`.
5. Soft delete: `DELETE /api/v1/users/{id}`.

Campos extra (`is_superuser`, etc.) son **rechazados** (`extra=forbid`).

## Ciclo académico típico

```text
Carrera → Asignaturas → Periodo ACTIVE
  → Cursos → Teaching assignment → Matrícula
  → Evaluaciones / Notas / Asistencia → Kardex
  → Reportes / Dashboard
```

Cerrar periodo (`CLOSED`) bloquea escrituras académicas normales.

## Zero Trust / auditoría

| Endpoint | Uso |
|---|---|
| `GET /policies` | Inventario PAP |
| `GET /tools` | Tool Registry |
| `GET /audit/events` | Auditoría técnica |
| `GET /security/events` | Señales de seguridad |
| `GET /users/{id}/history` | Historial de usuario (≠ audit) |

Tras pruebas de ataque, verificar eventos `TOOL_DENY`, `LOGIN_FAILURE`, `IDOR_ATTEMPT`.

## IA

- Proveedor por defecto: `mock` (sin llamar a internet).
- La IA **nunca** escribe SQL ni abre MySQL.
- Tools sensibles (`update_grade`, …) pasan por Gateway + PDP.

## Checklist diario del lab

- [ ] MySQL/XAMPP o tests SQLite OK
- [ ] `JWT_SECRET` personalizado
- [ ] Health `ok` en 127.0.0.1
- [ ] Sin exposición a red pública
- [ ] Revisar security events si hubo demos de ataque

## Referencias

- API: [`../api/API.md`](../api/API.md)
- Seguridad: [`../security/SEC-01-owasp-assessment.md`](../security/SEC-01-owasp-assessment.md)
- Arquitectura: [`../architecture/A00-index.md`](../architecture/A00-index.md)
