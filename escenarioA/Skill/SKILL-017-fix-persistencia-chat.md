# SKILL-017 — Fix persistencia chat IA + validación de tools

**Spec:** SPEC-018  
**También aplica:** SPEC-016, SPEC-017

## Rol del agente

Reparar guardado/sync del historial IA y verificar que el gateway ejecute consultas, mutaciones (con confirmación) y reportes.

## Procedimiento

1. Leer SPEC-018.
2. Backend `conversations.py`:
   - Preferir conversación con mensajes al resolver active.
   - Al `create_conversation`, archivar las otras del usuario.
   - Cargar mensajes con query explícita en `to_dict`.
3. Frontend:
   - No renderizar `#aiMessages` antes de que exista en DOM.
   - Tras `navigate('ai')`, `loadActive` + `renderAll`.
   - Persistir `conversation_id` en localStorage y enviarlo siempre.
4. Validar con test client:
   - float → active → panel mismo id y N mensajes crecientes.
   - report generate → download.
   - mutación + confirma → efecto en BD.
5. Actualizar PROMPTSMASTER si aplica.

## Restricciones

- No borrar historial existente al “arreglar”; archivar, no hard-delete.
- No saltar permisos ni confirmación en mutaciones.
