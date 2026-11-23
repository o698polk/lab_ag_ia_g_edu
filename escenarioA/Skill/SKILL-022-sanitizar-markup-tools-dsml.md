# SKILL-022 — Sanitizar / parsear markup DSML de tools

**Spec:** SPEC-023  
**También aplica:** SPEC-016, SPEC-022

## Rol del agente

Impedir que el chat muestre DSML/`invoke name=…`; parsear esas marcas como tool-calls y responder en lenguaje natural.

## Procedimiento

1. Leer SPEC-023.
2. `provider.py`: ampliar `parse_tool_calls` + `parse_dsml_tool_calls` + `strip_tool_markup`.
3. `orchestrator.py`: usar parse ampliado; sanitizar reply; actualizar `_is_raw_tool_dump`.
4. Prompt sistema: no emitir DSML.
5. `ai-chat.js`: filtrar burbujas con DSML.
6. Validar con string DSML sintético → tools ejecutadas, reply limpia.

## Restricciones

- No mostrar markup al usuario.
- Mantener confirmación en mutaciones.
