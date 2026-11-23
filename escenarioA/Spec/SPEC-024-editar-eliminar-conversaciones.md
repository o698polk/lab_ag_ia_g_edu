# SPEC-024 — Editar y eliminar conversaciones del chat IA

**Objetivo:** En el historial del asistente IA, el usuario puede **renombrar** y **eliminar** (o archivar de forma explícita) conversaciones guardadas.

**Skills:** SKILL-023  
**Relacionadas:** SPEC-020, SPEC-017

## Reglas

1. Renombrar: `PATCH /ai/conversations/<id>` con `{ "title": "..." }` (dueño; máx. 200 chars).
2. Eliminar: `DELETE /ai/conversations/<id>?hard=1` borra mensajes/artifacts del hilo (dueño). Sin `hard` o `hard=0` → archivar (comportamiento actual).
3. UI historial: botones Editar título y Eliminar por ítem; confirmar eliminación.
4. Si se elimina la conversación activa → crear/abrir otra vacía y refrescar UI.
5. No permitir operar conversaciones de otro usuario (salvo ADMIN auditoría futura).

## Criterios

- Renombrar se refleja en la lista.
- Eliminar quita el ítem del historial y limpia mensajes.
- Archivar (sin hard) sigue ocultando del “activo” pero puede listarse si se desea; hard = irreversible.
