# SPEC-022 — Respuestas fluidas del agente (estilo ChatGPT)

**Objetivo:** Tras ejecutar tools (p. ej. `reports_generate`), el usuario debe ver una **respuesta natural, organizada y útil** — nunca el dump `[Tool …]: {json…}`. Los enlaces de descarga van claros y clicables; el detalle técnico queda solo en logs internos.

**Skills relacionadas:** SKILL-021  
**Specs relacionadas:** SPEC-016, SPEC-017, SPEC-021

---

## 1. Problema

| Causa | Efecto |
| --- | --- |
| `history_for_llm` mete tools como `assistant` con `[Tool name]: {json}` | El modelo (o el historial) **repite** el JSON al usuario |
| Segunda pasada LLM a veces falla o regurgita el payload | Reply = JSON crudo |
| No hay composición determinística post-tool | Calidad inconsistente |

---

## 2. Reglas

1. **Nunca** mostrar al usuario el prefijo `[Tool …]` ni JSON de tool (`"ok": true`, `tool_payload`, etc.).
2. Tras tools exitosos: **componer** reply humano (`_compose_user_reply`) con:
   - qué se hizo,
   - resultado breve,
   - si hay artifact: nombre + link de descarga en línea propia.
3. Segunda pasada LLM (opcional): solo con **resúmenes sanitizados** (sin JSON completo); si falla o el contenido parece dump técnico → usar la composición determinística.
4. `history_for_llm`: tools → mensaje corto tipo `Resultado de reports_generate: reporte students.xlsx generado.` (máx. ~200 chars, sin JSON).
5. UI: filtrar mensajes cuyo contenido sea dump de tool; linkify URLs como SPEC-021.
6. Asociar `artifact_id` al mensaje `assistant` final cuando aplique.

---

## 3. Criterios de aceptación

1. Pedir “exporta estudiantes a excel” → respuesta tipo:  
   “Listo. Generé el reporte de estudiantes en Excel (`students_….xlsx`).  
   Puedes descargarlo aquí: `/api/v1/ai/artifacts/…`”
2. El chat **no** contiene `[Tool reports_generate]` ni bloques `{"ok": true`.
3. El link es clicable (SPEC-021).
4. Validación automatizada: reply post-report no matchea regex de dump.

---

## 4. Modelos sugeridos

Composer — leer SPEC-022 + SKILL-021 antes de editar.
