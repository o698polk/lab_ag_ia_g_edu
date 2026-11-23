# SPEC-032 — Nombres de hoja Excel seguros en reportes

**Objetivo:** Que la generación de reportes **xlsx** (agente, LogIA, exports de módulos) nunca falle por el nombre de la hoja de cálculo. Excel/openpyxl rechazan títulos con `\ / ? * [ ]` y limitan a **31** caracteres.

**Skills relacionadas:** SKILL-031  
**Specs relacionadas:** SPEC-019, SPEC-025, SPEC-031

---

## 1. Problema

| Título (ejemplo) | Resultado |
| --- | --- |
| `Reporte de Cursos / Materias` | `ValueError: Invalid character / found in sheet title` |
| Otros títulos con `?`, `*`, `[`, `]` | Mismo fallo |

El agente respondía que el reporte no pudo completarse por un “inconveniente técnico al procesar el nombre de la hoja”.

---

## 2. Requisitos

1. Función central `excel_sheet_title(title)` en `reports.py`:
   - Reemplazar caracteres inválidos `\ / ? * [ ]` (y similares) por espacio o guion.
   - Colapsar espacios, strip, truncar a 31.
   - Si queda vacío → `"Reporte"`.
2. `workbook_from_rows` **debe** usar siempre `excel_sheet_title` (única puerta de asignación de `ws.title`).
3. Callers pueden seguir pasando el título legible completo; el display del archivo/PDF no cambia.
4. Criterio: generar xlsx de `courses` (título con `/`) y LogIA export sin excepción.

---

## 3. Modelos sugeridos

Composer — leer SPEC-032 + SKILL-031.
