# SKILL-019 — Historial conversaciones IA (no borrar al crear nueva)

**Spec:** SPEC-020  
**También aplica:** SPEC-017, SPEC-018

## Rol del agente

Corregir la percepción de “borrado” al crear nueva conversación: archivar en historial, listar, reabrir.

## Procedimiento

1. Leer SPEC-020.
2. `conversations.py`:
   - `get_conversation(..., allow_archived=True)` para dueño.
   - `list_user_conversations` con message_count, incl. archivadas.
   - `create_conversation`: reutilizar activa vacía; si no, archivar otras y crear.
   - `open_conversation`: desarchivar id, archivar resto.
3. `system_api.py`: ajustar list/get; añadir `POST .../open`.
4. `ai-chat.js` + `Pages.ai`: UI historial, `openConversation`, refrescar lista tras nueva/open.
5. CSS mínimo para lista historial.
6. Validar con script: nueva no hard-delete; list + open restauran.

## Restricciones

- No hard-delete de mensajes.
- No romper sync panel/flotante ni localStorage `ai_conversation_id`.
- Mantener permisos `ai.use`.
