# SPEC-014 — Dashboard restringido (no estudiante / no docente)

**Objetivo:** El módulo **Dashboard** (métricas institucionales agregadas) es información sensible de gestión. Los roles **STUDENT** y **TEACHER** no deben verlo ni en menú ni por API.

**Skills relacionadas:** SKILL-013  
**Specs relacionadas:** SPEC-003, SPEC-009

---

## 1. Problema

Hoy `dashboard.view` está en `ROLE_PERMS` de STUDENT y TEACHER. Tras el login, `bootApp` navega siempre a `dashboard`, exponiendo conteos globales (estudiantes, docentes, cursos, etc.).

---

## 2. Reglas de acceso

| Rol | `dashboard.view` | Menú Dashboard | `GET /dashboard` |
| --- | --- | --- | --- |
| ADMIN, RECTOR, COORDINATOR, SECRETARY, REVIEWER, AUDITOR, IT_SUPPORT | Sí (según matriz) | Sí | 200 |
| **TEACHER** | **No** | **Oculto** | **403** |
| **STUDENT** | **No** | **Oculto** | **403** |
| GUARDIAN | No (recomendado) | Oculto | 403 |

---

## 3. Comportamiento de arranque

Tras login / `bootApp`:

1. Construir `navItems()` filtrado por permisos (y exclusiones de rol).
2. Si el usuario **no** tiene `dashboard.view` (o es STUDENT/TEACHER):
   - Navegar al **primer ítem** disponible del menú (ej. Cursos, Notas).
3. No llamar a `/api/v1/dashboard` si no hay permiso.

Defensa en profundidad:

- Quitar permiso en seeds + `sync_profile_visibility_perms`.
- Frontend: ocultar Dashboard si rol es STUDENT o TEACHER aunque quede permiso residual en JWT viejo.
- Backend: ya exige `dashboard.view` → tras sync + re-login → 403.

---

## 4. Criterios de aceptación

1. `est0001` no ve “Dashboard” en el sidebar; entra a otra página (ej. Cursos/Notas).
2. `docente01` igual.
3. `GET /api/v1/dashboard` con token estudiante/docente → 403.
4. `admin` sigue viendo Dashboard con métricas.
5. Re-login necesario para refrescar JWT tras sincronizar permisos.

---

## 5. Modelos de IA sugeridos

Composer, Claude Sonnet — leer SPEC-014 + SKILL-013 antes de editar.
