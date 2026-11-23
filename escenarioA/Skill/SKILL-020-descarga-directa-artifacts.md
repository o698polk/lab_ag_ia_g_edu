# SKILL-020 — Descarga directa artifacts por URL firmada

**Spec:** SPEC-021  
**También aplica:** SPEC-017

## Rol del agente

Permitir descarga del reporte IA abriendo/copiando  
`/api/v1/ai/artifacts/<id>/download` (con firma) además del botón autenticado.

## Procedimiento

1. Leer SPEC-021.
2. Crear helper `artifact_download_url` / `verify_artifact_download_sig` (HMAC).
3. `AIArtifact.to_dict()`: incluir `download_url` firmada completa (path API).
4. Endpoint download: aceptar JWT **o** `expires`+`sig`; respetar `expires_at` del artifact.
5. Orchestrator: mencionar el path en el mensaje cuando hay artifact.
6. `ai-chat.js`: burbuja con `<a href="download_url">` + botón; `downloadAuth` o navegación directa.
7. Validar GET con firma sin Bearer = 200.

## Restricciones

- No servir archivos sin JWT ni firma válida.
- No alargar validez más allá de `expires_at` del artifact.
