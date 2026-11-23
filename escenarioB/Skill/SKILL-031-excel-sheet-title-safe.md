# SKILL-031 — Sanitizar título de hoja Excel

**Spec:** SPEC-032  
**También aplica:** SPEC-019, SPEC-031

## Rol del agente

Corregir la generación xlsx para que ningún título de reporte rompa openpyxl.

## Procedimiento

1. Leer SPEC-032.
2. En `App/backend/app/services/reports.py` añadir `excel_sheet_title(title: str) -> str`.
3. En `workbook_from_rows`: `ws.title = excel_sheet_title(title)`.
4. Opcional: suavizar títulos del catálogo AI (`Reporte de Cursos y Materias`) sin depender solo de eso.
5. Actualizar PROMPTSMASTER (SPEC-032 / SKILL-031).
6. Validar: `workbook_from_rows("Reporte de Cursos / Materias", ["A"], [["1"]])` no lanza.

## Restricciones

- No cambiar el formato de filas/columnas.
- No romper PDF/JSON/MD.
