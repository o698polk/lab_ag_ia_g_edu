# SPEC-013 — Proveedores de IA múltiples (cloud + local)

**Objetivo:** Extender el módulo **Administración → Configuración IA** para permitir registrar y usar varios proveedores de modelos (DeepSeek, OpenAI/GPT, Anthropic/Claude, Google Gemini y modelos locales tipo **LM Studio**), configurando principalmente **nombre del modelo**, **API Key** (si aplica) y **URL base** (local / personalizada).

**Skills relacionadas:** SKILL-012  
**Specs relacionadas:** SPEC-005 (agente IA), SPEC-002 (SSRF / secretos)

---

## 1. Estado actual (baseline)

| Pieza | Hoy |
| --- | --- |
| Modelo | Una sola fila `ai_config` orientada a DeepSeek |
| Chat | `app/ai/deepseek.py` → solo `api.deepseek.com` |
| UI | Formulario “Configuración DeepSeek” (key, modelo, temp, prompt) |
| Seguridad | API Key AES; SSRF con allowlist fija de DeepSeek |

---

## 2. Proveedores soportados

| Código `provider` | Nombre UI | API Key | URL base por defecto | Notas |
| --- | --- | --- | --- | --- |
| `deepseek` | DeepSeek | Obligatoria | `https://api.deepseek.com/v1/chat/completions` | Compat. OpenAI |
| `openai` | OpenAI (GPT) | Obligatoria | `https://api.openai.com/v1/chat/completions` | GPT-4o, gpt-4.1, etc. |
| `anthropic` | Anthropic (Claude) | Obligatoria | `https://api.anthropic.com/v1/messages` | Adaptador nativo Messages API |
| `gemini` | Google Gemini | Obligatoria | `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` | Preferir endpoint OpenAI-compatible de Google; si falla, documentar fallback |
| `lmstudio` | LM Studio (local) | Opcional | `http://127.0.0.1:1234/v1/chat/completions` | Sin key o key dummy; **HTTP localhost permitido** |
| `custom_openai` | OpenAI-compatible (custom) | Opcional | Definida por admin | Cualquier proxy OpenAI-compatible (Ollama, vLLM, etc.) |

El admin solo necesita, en el caso típico:

1. Elegir proveedor (o “OpenAI-compatible”).
2. Escribir **nombre del modelo** (ej. `gpt-4o-mini`, `claude-sonnet-4-20250514`, `gemini-2.0-flash`, `local-model`).
3. Pegar **API Key** (excepto LM Studio / custom sin auth).
4. (Local/custom) confirmar o editar **URL base**.
5. Activar y marcar como **proveedor activo** para el chat del sistema.

---

## 3. Modelo de datos

### 3.1 Nueva tabla `ai_providers`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | int PK | |
| `name` | string(100) | Etiqueta amigable (ej. “GPT producción”) |
| `provider` | string(40) | Código de §2 |
| `model` | string(120) | Nombre del modelo |
| `api_key_encrypted` | text nullable | AES; null si local sin key |
| `base_url` | string(500) | Endpoint chat completions / messages |
| `temperature` | float | default 0.3 |
| `system_prompt` | text nullable | Override opcional |
| `is_enabled` | bool | Si se puede usar |
| `is_active` | bool | **Solo uno** activo a la vez (el que usa el chatbot) |
| `created_at` / `updated_at` | datetime | |

Migración / compatibilidad:

- Al arrancar o en seed: si existe `ai_config` legacy con datos, crear un `ai_providers` `deepseek` y marcarlo activo.
- Mantener `ai_config` en lectura por un tiempo **o** migrar y deprecar (preferido: migrar en el seeder/`sync` y que el chat lea solo `ai_providers`).

### 3.2 Respuesta API (máscara de secretos)

```json
{
  "id": 1,
  "name": "Claude institucional",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "has_api_key": true,
  "base_url": "https://api.anthropic.com/v1/messages",
  "temperature": 0.3,
  "system_prompt": "...",
  "is_enabled": true,
  "is_active": true
}
```

Nunca devolver la API Key en claro.

---

## 4. Endpoints

Prefijo existente `/api/v1`. Permiso: `ai.configure` (CRUD); chat sigue con `ai.use`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/ai/providers` | Lista proveedores (keys enmascaradas) |
| GET | `/ai/providers/catalog` | Catálogo estático: proveedores + URL default + si requiere key |
| POST | `/ai/providers` | Crear (name, provider, model, api_key?, base_url?, …) |
| PUT | `/ai/providers/<id>` | Actualizar; `api_key` vacío = no cambiar |
| DELETE | `/ai/providers/<id>` | Eliminar (no borrar el único activo sin reasignar) |
| POST | `/ai/providers/<id>/activate` | Marca `is_active=true` y desactiva los demás |
| GET | `/ai/config` | **Compat:** devuelve el proveedor activo en forma legacy + lista resumida |
| PUT | `/ai/config` | **Compat:** actualiza el activo o crea deepseek si no hay |

`POST /ai/chat` usa el proveedor con `is_active=true` e `is_enabled=true`.

---

## 5. Capa de chat (adapters)

Archivo sugerido: `app/ai/providers.py` (+ mantener `deepseek.py` como wrapper o fusionar).

### 5.1 Interfaz común

```text
chat_with_provider(provider_row, system: str, message: str) -> { reply, tokens_used, source }
```

### 5.2 Adaptadores

| Provider | Formato request |
| --- | --- |
| deepseek, openai, gemini (compat), lmstudio, custom_openai | OpenAI Chat Completions: `{ model, temperature, messages[] }` + `Authorization: Bearer` (omitir si no hay key) |
| anthropic | Messages API: `{ model, max_tokens, temperature, system, messages:[{role,content}] }` + headers `x-api-key`, `anthropic-version` |

### 5.3 SSRF (SPEC-002)

Allowlist de hosts cloud:

- `api.deepseek.com`
- `api.openai.com`
- `api.anthropic.com`
- `generativelanguage.googleapis.com`

Local (solo LM Studio / custom con flag local):

- Permitir `http://127.0.0.1`, `http://localhost`, y opcionalmente IPs privadas de LAN **solo** si `provider in (lmstudio, custom_openai)` y admin confirma URL.
- Rechazar metadata cloud (`169.254.169.254`, etc.).

---

## 6. UI — Administración

Reemplazar/ampliar el panel “Configuración DeepSeek” por **Proveedores de IA**:

1. **Tabla** de proveedores: nombre, tipo, modelo, activo, habilitado, acciones (Editar, Activar, Eliminar).
2. **Botón “Agregar proveedor”** → modal/formulario:
   - Nombre amigable
   - Selector de proveedor (DeepSeek / OpenAI GPT / Claude / Gemini / LM Studio / OpenAI-compatible)
   - Nombre del modelo (texto libre)
   - API Key (password; opcional si LM Studio / custom)
   - URL base (prellenada según catálogo; editable)
   - Temperatura, system prompt, habilitado
3. Al elegir proveedor del catálogo, autocompletar `base_url`.
4. Indicador claro del **proveedor activo** (el del chatbot flotante).
5. Texto de ayuda LM Studio: “Inicie el servidor local (puerto 1234) y use el nombre de modelo que muestra LM Studio.”

---

## 7. Criterios de aceptación

1. Admin puede crear un proveedor OpenAI con solo nombre + model + api_key y activarlo.
2. Admin puede crear Claude y Gemini de la misma forma.
3. Admin puede crear LM Studio con URL `http://127.0.0.1:1234/v1/chat/completions` **sin** API Key y activarlo.
4. El chatbot usa únicamente el proveedor `is_active`.
5. Las API Keys nunca aparecen en JSON ni en el HTML.
6. URLs no allowlisted se rechazan (excepto localhost para lmstudio/custom).
7. Migración: instalación con `ai_config` DeepSeek existente sigue funcionando tras el cambio.

---

## 8. Fuera de alcance (esta SPEC)

- Fine-tuning o subida de archivos.
- Facturación / cuotas por proveedor.
- UI de prueba de latencia avanzada (opcional futuro: botón “Probar conexión”).

---

## 9. Modelos de IA sugeridos para implementar

Composer, Claude Sonnet, GPT-4o — leer SPEC-013 + SKILL-012 antes de tocar código.
