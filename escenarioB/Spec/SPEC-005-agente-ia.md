# SPEC-005 — Agente de Inteligencia Artificial (DeepSeek)

> **Extensión multi-proveedor:** ver **SPEC-013** (GPT, Claude, Gemini, LM Studio) y **SKILL-012**.  
> **Gateway CRUD + privilegios:** **SPEC-016** / **SKILL-015**.  
> **Conversaciones unificadas + reportes IA:** **SPEC-017** / **SKILL-016**.

## Capacidades
- Consultar/crear/editar datos vía API interna con permisos del usuario (gateway de tools: SPEC-016).
- Responder sobre estado del sistema.
- Generar resúmenes y detectar anomalías.
- Acciones administrativas bajo confirmación.
- Configurable: API Key, modelo, temperatura, system prompt.
- Proveedores múltiples y modelo local (SPEC-013).
- Historial compartido chat flotante ↔ panel fijo (SPEC-017).
- Generar reportes PDF / Excel / JSON / Markdown desde el chat (SPEC-017).
- Gestión o solicitud de elevación de roles/privilegios auditada (SPEC-016).

## Seguridad
- API Key cifrada AES-256 en BD, nunca en frontend.
- Actúa con permisos del invocador.
- Acciones registradas en auditoría.
- Validación SSRF de URLs externas.

## Endpoint

```
POST /api/v1/ai/chat
Authorization: Bearer <token>
Body: { "message": "...", "context": "..." }
```
