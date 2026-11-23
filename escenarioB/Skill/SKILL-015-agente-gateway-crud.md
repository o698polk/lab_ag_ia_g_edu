# SKILL-015 — Gateway CRUD del agente IA

**Spec:** SPEC-016  
**También aplica:** SPEC-002, SPEC-003, SPEC-005, SPEC-008, SPEC-013

## Rol del agente

Implementar un **Tool Gateway** para que el LLM invoque operaciones CRUD/IAM reales con los permisos del usuario, confirmación en mutaciones y auditoría; incluir gestión y solicitud de elevación de roles/privilegios.

## Procedimiento

1. Leer SPEC-016 completo.
2. Crear módulo `app/ai/gateway/`:
   - `registry.py` — catálogo de tools `{resource}.{action}` → handler + `permission` + `mutating`.
   - `executor.py` — `execute(user, name, args, confirm)` → check perm → confirm → llamar servicio → audit.
   - `orchestrator.py` — loop LLM↔tools (máx. N calls); construir schemas JSON para function-calling del proveedor activo (SPEC-013).
3. Registrar tools por recurso reutilizando handlers de `app/api/academic.py`, `users.py`, `system_api.py` (extraer a services si hace falta para no importar circular).
4. Ampliar `POST /ai/chat`:
   - Pasar historial de conversación (SPEC-017 si ya existe; si no, mínimo últimos turnos en memoria/AILog).
   - Devolver `pending_action`, `tool_calls`, `reply`.
5. IAM tools: `users.assign_roles`, `roles.set_permissions`, `privileges.request_elevation`, `privileges.resolve_elevation` (modelo `elevation_requests` si no existe).
6. Bloquear: SQL raw, lectura de passwords/keys, delete masivo, tools no registradas.
7. Fallback sin API key: solo texto contextual; **no** ejecutar mutaciones.
8. Tests manuales o script: STUDENT denegado en delete course; ADMIN confirm assign role; TEACHER upsert grade en curso propio.

## Restricciones

- Actuar siempre como el invocador (salvo elevación aprobada y auditada).
- Mutaciones requieren confirmación explícita.
- No exponer secretos en args/logs de tools.
- No implementar “modo dios” del modelo sin permiso humano.
