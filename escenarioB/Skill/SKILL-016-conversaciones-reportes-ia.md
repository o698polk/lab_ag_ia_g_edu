# SKILL-016 — Conversaciones unificadas + reportes IA

**Spec:** SPEC-017  
**También aplica:** SPEC-005, SPEC-006, SPEC-013, SPEC-016

## Rol del agente

Persistir y sincronizar el historial entre chat flotante y chat fijo; habilitar generación de reportes (PDF, Excel, JSON, MD) desde el agente con descarga segura.

## Procedimiento

### A. Persistencia

1. Leer SPEC-017.
2. Añadir modelos `AIConversation`, `AIMessage`, `AIArtifact` (+ migración/create_all en demo).
3. Endpoints bajo `/api/v1/ai/conversations*` y `/ai/artifacts/<id>/download`.
4. En `POST /ai/chat`:
   - Resolver/crear `conversation_id` del usuario.
   - Guardar mensaje user + assistant (+ tool si aplica).
   - Registrar `channel` (`panel`|`float`).
   - Devolver `conversation_id` y turnos nuevos.

### B. Frontend sync

1. Extraer helper `AIChatStore` en JS:
   - `loadActive()`, `render(boxEl)`, `send(message, channel)`.
2. `sendAI` (panel) y submit del flotante usan el mismo helper.
3. Al `bootApp` / `initFloatChat` / entrar a `Pages.ai`: cargar activa y pintar ambos contenedores si existen.
4. Botón “Nueva conversación” en el panel (y opcional en flotante).

### C. Reportes desde el agente

1. Tool `reports.generate` en el gateway (SKILL-015):
   - Inputs: `report_type`, `format` ∈ {pdf,xlsx,json,md}, `filters`.
   - Reutilizar `app/services/reports.py` para datos + scope.
   - PDF/XLSX: generadores existentes; JSON: `json.dumps`; MD: tabla markdown.
2. Persistir artifact; incluir `download_url` en `artifacts[]` de la respuesta.
3. En UI de burbujas: enlace “Descargar {filename}”.
4. Respetar permisos de export; si faltan, no generar archivo.

### D. Verificación

1. Escribir en flotante → abrir módulo IA → mismo texto.
2. Recargar página → historial intacto.
3. Pedir export xlsx/pdf/json/md con admin → descarga OK.
4. Usuario sin `reports.export` / view del módulo → rechazo sin artifact.
5. Usuario B no descarga artifact de A.

## Restricciones

- No mantener dos historiales locales independientes como fuente de verdad.
- No poner blobs enormes en localStorage; la fuente es la API.
- No saltarse filtros de visibilidad al generar reportes.
- Limpiar o expirar artifacts antiguos si se implementa `expires_at`.
