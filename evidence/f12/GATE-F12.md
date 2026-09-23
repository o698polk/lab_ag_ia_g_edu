# Evidencia Gate F12 — Cierre del laboratorio

| Campo | Valor |
|---|---|
| Gate | F12 — Evaluation |
| Decisión | **ACEPTAR CIERRE CONDICIONADO** |
| Aprobador | Humano (SI) |
| Fecha | 2026-09-20 |
| Skill | K-011 Evaluator |
| Alcance | Fases PolkDev **F1 → F12** |

## Condiciones aceptadas

- Gaps P1: recuperación password · UI rica (notas/asistencia)
- Gap P2: export PDF (501)
- ADR-013: cobertura de ramas global diferida
- ADR-009: solo `127.0.0.1` / localhost · sin Internet

## Evidencia de cierre

- `evidence/f12/F12-EVALUATION.md`
- `evidence/f12/perf.json`
- `evidence/f12/pytest-f12.txt` (74 passed)
- `evidence/f10/coverage.json` (85.65% líneas)
- `evidence/f8/F8-SECURITY.md` (0 críticos)

## Estado final

```text
Laboratorio SIGA (siga-polkdev) — CERRADO CONDICIONADO
No hay fase F13.
```

Addendum 2026-09-22: la UI de notas/asistencia/catálogos quedó implementada en PromptMaster F2–F10. No reabre F13. Deuda que sigue: recuperación de contraseña y PDF (501).
