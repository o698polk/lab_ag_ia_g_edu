# SKILL-012 — Integrador de proveedores de IA (cloud + LM Studio)

**Spec:** SPEC-013  
**También aplica:** SPEC-005, SPEC-002

## Rol del agente

Implementar en el sistema la gestión de **múltiples proveedores de IA** desde Administración, permitiendo agregar GPT, Claude, Gemini (API key + nombre de modelo) y un modelo local tipo **LM Studio** (URL local, key opcional), y enrutar el chat al proveedor activo.

## Antes de codificar

1. Leer completa `Spec/SPEC-013-proveedores-ia.md`.
2. Revisar:
   - `App/backend/app/models/system.py` → `AIConfig`
   - `App/backend/app/ai/deepseek.py`
   - `App/backend/app/api/system_api.py` → `/ai/config`, `/ai/chat`
   - `App/frontend/static/js/app.js` → panel admin IA / `saveAI`
3. No dejar el chat atado solo a DeepSeek ni hardcodear un único host.

## Procedimiento (orden obligatorio)

### Paso A — Modelo y migración suave

1. Crear modelo `AIProvider` (`ai_providers`) con campos de SPEC-013 §3.1.
2. Exportar en `app/models/__init__.py`.
3. En arranque (`run.py` / `db.create_all`) crear tablas.
4. Función `migrate_legacy_ai_config()`:
   - Si hay fila en `ai_config` y no hay providers → crear provider `deepseek` con esos datos y `is_active=True`.

### Paso B — Catálogo y SSRF

1. Definir `PROVIDER_CATALOG` (código, label, default_base_url, requires_api_key, api_style: `openai`|`anthropic`).
2. Ampliar validación de URL:
   - Hosts cloud allowlist (SPEC-013 §5.3).
   - `lmstudio` / `custom_openai`: permitir `http://127.0.0.1` y `http://localhost` (+ puerto).

### Paso C — Adapters de chat

1. Crear `app/ai/providers.py` con:
   - `get_active_provider()`
   - `chat(user, message, context)` que lea el activo.
   - `_chat_openai_compatible(...)`
   - `_chat_anthropic(...)`
2. Actualizar `/ai/chat` para llamar al nuevo módulo (dejar `deepseek.py` delegando o eliminando duplicación).

### Paso D — API REST

Implementar rutas SPEC-013 §4:

- `GET/POST /ai/providers`
- `PUT/DELETE /ai/providers/<id>`
- `POST /ai/providers/<id>/activate`
- `GET /ai/providers/catalog`
- Mantener `GET/PUT /ai/config` como compat del activo.

Reglas:

- Al activar uno, `is_active=False` en los demás.
- `api_key` vacío en PUT → no sobrescribir.
- Cifrar key con `encrypt_value` / leer con `decrypt_value`.

### Paso E — Frontend Administración

1. Renombrar sección a **Proveedores de IA**.
2. Listar providers + badge “Activo”.
3. Formulario/modal “Agregar / Editar”:
   - select proveedor → autocompleta `base_url`
   - inputs: name, model, api_key, base_url, temperature, system_prompt, is_enabled
4. Botones: Guardar, Activar, Eliminar.
5. Ayuda visible para LM Studio (puerto 1234, sin key).
6. Chatbot flotante sin cambios de UX (sigue `/ai/chat`).

### Paso F — Verificación

1. Crear provider OpenAI de prueba (aunque la key sea inválida): debe guardar y listarse.
2. Crear LM Studio con URL local sin key → activar → chat intenta localhost (error de conexión aceptable si LM Studio no corre; no debe fallar por SSRF).
3. Activar DeepSeek migrado → chat se comporta como antes si hay key válida.
4. Confirmar que respuestas JSON no incluyen la key.

## Restricciones

- Nunca loguear API keys.
- No permitir hosts arbitrarios en providers cloud.
- Un solo `is_active` a la vez.
- No romper permiso `ai.configure` / `ai.use`.
- No exigir key para `lmstudio`.

## Entregables

- Modelo + endpoints + adapters + UI admin.
- Migración desde `ai_config`.
- Prueba manual documentada (al menos listar/activar/local SSRF ok).

## Checklist rápido

- [ ] `AIProvider` en BD  
- [ ] Catálogo + CRUD + activate  
- [ ] Chat usa provider activo (OpenAI-compat + Anthropic)  
- [ ] LM Studio localhost permitido  
- [ ] UI Administración con alta por API key + modelo  
- [ ] Legacy DeepSeek migrado  
