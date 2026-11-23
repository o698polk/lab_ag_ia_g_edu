# SPEC-025 — Fix generación PDF desde el agente IA

**Objetivo:** Cuando el usuario pide un reporte en **PDF** al agente, el artifact se genera correctamente y el enlace de descarga funciona (igual que Excel).

**Skills:** SKILL-024  
**Relacionadas:** SPEC-017, SPEC-021, SPEC-022

## Causas probables

1. `generate_report_artifact` llama `pdf_from_rows` **sin** `col_widths` → overflow / fallos.
2. Caracteres no-Latin1 con Helvetica de ReportLab.
3. Errores no tipados capturados como tool error genérico.

## Reglas

1. Pasar `widths` del catálogo / `REPORT_TYPES` a `pdf_from_rows`.
2. Sanitizar texto a Latin-1 seguro (o usar fuente que soporte Unicode).
3. Responder con mensaje fluido + `download_url` firmada (SPEC-021/022).
4. Validar: `reports_generate` format=pdf → artifact + download 200.

## Criterios

- “Genera estudiantes en pdf” → PDF descargable, sin error de tool.
- Excel sigue funcionando.
