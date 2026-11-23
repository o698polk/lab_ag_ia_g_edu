# SPEC-018 — Fix persistencia y sync del chat IA

**Objetivo:** Corregir fallos de usabilidad donde el historial del agente **parece no guardarse** entre chat flotante, panel fijo y recargas, y asegurar que el agente **ejecute** las acciones solicitadas (CRUD/tools/reportes) bajo permisos + confirmación.

**Skills relacionadas:** SKILL-017  
**Specs relacionadas:** SPEC-016, SPEC-017

---

## 1. Causas raíz confirmadas

| # | Bug | Efecto |
| --- | --- | --- |
| 1 | `Pages.ai()` llama `renderAll()` **antes** de insertar el HTML de `#aiMessages` | El panel fijo queda vacío aunque BD tenga mensajes |
| 2 | `get_or_create_active` elige la conversación no archivada con `updated_at` más reciente, aunque esté **vacía** (ej. tras “Nueva conversación” o race) | El historial con mensajes queda “huérfano”; el usuario ve chat vacío |
| 3 | `POST /ai/conversations` no archiva la conversación anterior | Varias activas compiten; la vacía gana |
| 4 | Frontend no recuerda `conversation_id` entre recargas de forma explícita | Depende solo del “active” defectuoso |

---

## 2. Reglas de corrección

### 2.1 Persistencia (backend)

1. **Conversación activa** = no archivada del usuario, preferencia:
   - `conversation_id` explícito del cliente (si pertenece al usuario),
   - else la no archivada con **más mensajes** / último mensaje más reciente,
   - else crear una nueva.
2. Al crear **nueva** conversación: **archivar** las demás no archivadas del mismo usuario (una sola activa).
3. `to_dict(include_messages=True)` debe cargar mensajes con query ordenada (no colección stale).
4. Cada turno de `POST /ai/chat` sigue persistiendo `user` + `assistant` (+ `tool` si aplica) en BD.

### 2.2 Sync UI (frontend)

1. Tras `navigate('ai')` e `innerHTML`, **entonces** `loadActive` + `renderAll`.
2. Flotante y panel comparten `AIChatStore` y el mismo `conversation_id`.
3. Guardar `conversation_id` en `localStorage` (`ai_conversation_id`) y enviarlo en cada chat / active preferido.
4. Tras enviar mensaje: recargar historial desde API (fuente de verdad) y pintar ambos contenedores.

### 2.3 Acciones del agente

1. Tools de lectura se ejecutan sin confirmación.
2. Mutaciones (`enrollments_create`, `grades_upsert`, `users_assign_roles`, …) requieren confirmación; al responder `confirma` se ejecutan de verdad.
3. `reports_generate` (pdf/xlsx/json/md) se ejecuta y deja `artifact` descargable.
4. Sin permiso → mensaje claro; opcional `privileges_request_elevation`.

---

## 3. Criterios de aceptación

1. Escribir en flotante → abrir Asistente IA → **mismo historial**.
2. Recargar F5 → historial intacto.
3. “Nueva conversación” empieza vacío; la anterior queda archivada (no pisa el historial al volver a active de la nueva).
4. Admin: “¿cuántos estudiantes?” → respuesta con dato real vía tool.
5. Admin: “exporta estudiantes en json” → artifact + download 200.
6. Admin: acción mutante → pide confirmación → tras `confirma` el cambio existe en BD.

---

## 4. Modelos sugeridos

Composer / Claude Sonnet — leer SPEC-018 + SKILL-017 antes de editar.
