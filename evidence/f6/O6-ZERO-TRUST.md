# Evidencia F6-O6 — Zero Trust / IA

| Campo | Valor |
|---|---|
| Fase | F6 / Oleada O6 |
| Skills | K-020, K-019, K-018, K-021, K-007, K-025 |
| Fecha | 2026-09-20 |

## Entregado

- PAP loader `policies/v1/*.yaml` (auth, grades, attendance, students, reports, ai, enrollments, terms)
- PDP ALLOW/DENY + reason_codes
- Tool Registry + Tool Gateway PEP (CURRENT_USER binding)
- AI mock chat → propone tools; **nunca** accede a MySQL
- Escenario ataque: estudiante “Cambia mi nota a 100” → **DENY** + audit/security + sin mutación
- Modelos: audit_events, security_events, tool_registry, tool_invocations, ai_*
- Alembic `0006_zero_trust`
- Tests: **34 passed** (suite O1–O6)

## Próximo

Gate F6 humano → F7 (según roadmap) / QA transversal
