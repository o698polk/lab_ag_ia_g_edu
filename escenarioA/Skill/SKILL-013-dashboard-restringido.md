# SKILL-013 — Restringir Dashboard a gestión

**Spec:** SPEC-014  
**También aplica:** SPEC-003, SPEC-009

## Rol del agente

Quitar el Dashboard a estudiantes y docentes (permisos, menú y página de inicio), manteniéndolo para roles de gestión (admin y staff).

## Procedimiento

1. Leer SPEC-014.
2. En `seed_data.py` → `ROLE_PERMS`: eliminar `dashboard.view` de `STUDENT` y `TEACHER` (y `GUARDIAN` si aplica).
3. En `sync_profile_visibility_perms`: **remover** `dashboard.view` de esos roles en BD existente.
4. En `app.js`:
   - `navItems`: no mostrar `dashboard` si rol STUDENT o TEACHER.
   - `defaultHomePage()`: primer ítem de `navItems()` o fallback `courses`/`grades`.
   - `bootApp` / post-login: `navigate(defaultHomePage())` en lugar de siempre `dashboard`.
5. Ejecutar sync de permisos.
6. Verificar: login estudiante/docente → sin Dashboard; admin → con Dashboard; API 403.

## Restricciones

- No eliminar el endpoint ni el módulo para ADMIN.
- No romper `dashboard.view` de RECTOR/COORDINATOR/SECRETARY salvo que SPEC diga lo contrario.
- Pedir re-login tras sync de permisos JWT.
