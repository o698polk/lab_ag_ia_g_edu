# SPEC-020 — Historial de conversaciones IA (no perder al crear nueva)

**Objetivo:** Al pulsar **Nueva conversación**, el chat actual queda en **historial** (no se borra). El usuario puede **reabrir** cualquier conversación anterior. Archivar = guardar en historial, no hard-delete.

**Skills relacionadas:** SKILL-019  
**Specs relacionadas:** SPEC-017, SPEC-018

---

## 1. Problema

| Hoy | Efecto |
| --- | --- |
| `POST /ai/conversations` archiva la anterior | Correcto en BD, pero… |
| `GET /ai/conversations` solo lista `is_archived=False` | La anterior **desaparece** de la UI |
| `get_conversation` exige `is_archived=False` | No se puede reabrir |
| UI solo tiene botón “Nueva” | El usuario percibe que “se borró” el chat |

---

## 2. Reglas

1. **Nunca** borrar mensajes ni conversaciones al crear una nueva (salvo DELETE explícito / archivado voluntario).
2. Al crear nueva:
   - Si la activa actual **no tiene mensajes**, reutilizarla (no crear huérfanas vacías).
   - Si tiene mensajes: marcarla `is_archived=True` y crear hilo vacío nuevo.
3. **Listado** de historial: últimas N conversaciones del usuario (activas **y** archivadas), con `title`, `message_count`, `updated_at`, `is_archived`.
4. **Abrir** conversación por id: pertenece al usuario → cargar mensajes; si estaba archivada, **reactivarla** (desarchivar) y archivar las demás activas.
5. UI módulo Asistente IA: panel lateral **Historial** + botón Nueva; clic en un ítem carga ese hilo (panel + flotante sync).

---

## 3. API

| Método | Ruta | Comportamiento |
| --- | --- | --- |
| GET | `/ai/conversations` | Historial (incl. archivadas), `?limit=50` |
| POST | `/ai/conversations` | Nueva (reusa vacía o archiva+crea) |
| POST | `/ai/conversations/<id>/open` | Reactivar / seleccionar hilo |
| GET | `/ai/conversations/<id>` | Detalle + mensajes (también archivada del dueño) |
| DELETE | `/ai/conversations/<id>` | Archivar (ocultar del “activo”; sigue en historial hasta purge futuro) |

---

## 4. Criterios de aceptación

1. Chat con mensajes → Nueva → chat vacío; la anterior aparece en Historial con su título.
2. Clic en historial → se restauran los mensajes (panel y flotante).
3. Recargar F5 con `conversation_id` en localStorage (aunque archivada) → abre ese hilo o el activo con mensajes.
4. Nueva sobre chat vacío → no duplica conversaciones vacías.
5. Validación automatizada: crear → archivar anterior → list incluye ambas → open restaura mensajes.

---

## 5. Modelos sugeridos

Composer / Claude — leer SPEC-020 + SKILL-019 antes de editar.
