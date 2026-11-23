# SKILL-026 — Typing/thinking UI + formato formal APA 7

**Spec:** SPEC-027  
**También aplica:** SPEC-022, SPEC-023

## Rol del agente

Implementar feedback visual «pensando / escribiendo» en el chat IA y forzar presentación textual simple y formal (guía APA 7), sin markdown ornamental.

## Procedimiento

1. Leer SPEC-027.
2. Crear `App/backend/app/services/ai_text_format.py` con `format_apa_plain(text)` (sanitiza `*`, `**`, viñetas, emojis).
3. Aplicar en `orchestrator.py` a toda reply de asistente antes de `add_message`; actualizar `_compose_user_reply` a listas numeradas y tono formal.
4. Ampliar system prompt en `provider.py` / `deepseek.py` con reglas APA 7 de presentación.
5. Frontend `ai-chat.js`: indicador thinking + typing dots; typewriter al mostrar reply nueva.
6. CSS: animaciones del icono y dots.
7. Validar sanitizer con string sintético; actualizar PROMPTSMASTER (SPEC-027 / SKILL-026).

## Restricciones

- No romper linkify de URLs de descarga.
- No reintroducir dumps DSML/JSON (SPEC-023).
- Typewriter no debe dejar el chat en estado inconsistente si hay error de red.
