# Evidencia F6-O4 — Evaluación académica

| Campo | Valor |
|---|---|
| Fase | F6 / Oleada O4 |
| Skills | K-017, K-016, K-013, K-006, K-007 |
| Fecha | 2026-09-20 |

## Entregado

- Modelos: attendance, evaluations, grades, kardex
- Alembic `0004_evaluation`
- ABAC: docente sin `teaching_assignment` → DENY `CONTEXT_MISMATCH`
- Anti-IDOR: estudiante no ve notas ajenas → `RESOURCE_NOT_OWNED`
- Asistencia + % y Kardex
- Tests: **23 passed**

## Próximo

O5 — Dashboard, reportes, notificaciones, historial usuario
