# Evidencia F7 — TESTS

| Campo | Valor |
|---|---|
| Fase | F7 |
| Skills | K-006, K-007 |
| Gate previo | F6 GO |
| Fecha | 2026-09-20 |

## Suites

| Suite | Ubicación | Estado |
|---|---|---|
| Unit | `tests/unit/` | ✅ |
| Integration | `tests/integration/` | ✅ |
| Security | `tests/security/` | ✅ |
| E2E | `tests/e2e/` | ✅ |

## Ejecución

```text
pytest tests → 68 passed
```

## Cobertura

| Ámbito | Líneas | Ramas (combinado cov-branch) |
|---|---|---|
| App completa (`app`) | **85.7%** (≥80% ✓) | 57.3% (deuda → F8) |
| Ruta crítica Zero Trust (policy/gateway/ai/auth/audit/tools) | — | **83%** ✓ |

Gate F7 (S08): *“cobertura mínima en ruta crítica”* → **cumplido**.

RNF-QUA-001 ramas globales ≥70% queda como mejora en F8 (OWASP/hardening + más casos de borde).

## Seguridad cubierta (suite)

- JWT tampered / wrong secret / alg none
- IDOR grades
- SQLi login payloads
- XSS stored as JSON (no HTML)
- Privilege escalation / mass assignment
- AI DENY update_grade

## Artefactos

- `evidence/f7/coverage.json`
- `evidence/f6/GATE-F6.md`

## Próximo

Gate F7 → **F8 SECURITY** (OWASP profundo, secrets, residuales de ramas)
