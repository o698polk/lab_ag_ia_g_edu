# S12 — Métricas de calidad

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fuente | `prompt_master.md` §§51–53, 77 F7–F8, ADR-010 |
| Fecha | 2026-09-20 |

---

## 1. Métricas de producto

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-P01 | Cobertura RF P0 implementados | 100% P0 | Trazabilidad S05↔código↔tests |
| MQ-P02 | Historias P0 con CA verificados | 100% | Gate F10 |
| MQ-P03 | Módulos mínimos PromptMaster presentes | 100% baseline | Checklist F9/F10 |

---

## 2. Métricas de código y pruebas

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-Q01 | Cobertura de líneas | ≥ 80% | pytest-cov |
| MQ-Q02 | Cobertura de ramas | ≥ 70% | pytest-cov |
| MQ-Q03 | Suites obligatorias | Unit + Integration + Security + E2E | CI local / scripts |
| MQ-Q04 | Tests de autorización críticos | ≥ 12 casos (matriz PromptMaster §53) | Suite security |
| MQ-Q05 | Fallos flaky | 0 en main local | Re-run evidencia |

---

## 3. Métricas de seguridad

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-S01 | Hallazgos críticos abiertos | 0 al Gate F8 | Informe K-007 |
| MQ-S02 | Intentos IDOR denegados (casos prueba) | 100% DENY | Tests security |
| MQ-S03 | Tools sensibles vía IA sin auth | 100% DENY | BL-O6-007 |
| MQ-S04 | Secretos en repo | 0 | Revisión + git scan |
| MQ-S05 | Ops sensibles con audit event | 100% P0 sensibles | Muestreo + tests |
| MQ-S06 | ADMIN sin permiso explícito | DENY | Tests IAM |

---

## 4. Métricas de proceso (locales, orientativas)

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-R01 | p95 login | &lt; 500 ms (local) | Medición manual/script |
| MQ-R02 | p95 get_grades (autorizado) | &lt; 500 ms (local) | Script |
| MQ-R03 | Disponibilidad entorno local | Sesión de demo sin crash | Smoke F11 |

---

## 5. Métricas de proceso PolkDev

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-D01 | Cambios App sin Spec | 0 | Review |
| MQ-D02 | Tareas sin Skill | 0 (post F4) | Backlog |
| MQ-D03 | Gates saltados | 0 | Registro de fases |
| MQ-D04 | Spec drift | 0 críticos al F10 | K-009 |

---

## 6. Métricas UX (baseline)

| ID | Métrica | Meta | Medición |
|---|---|---|---|
| MQ-U01 | Flujos críticos usables en desktop | Login + nota + asistencia | Prueba manual |
| MQ-U02 | Layout usable en viewport móvil básico | Sin bloqueo total | Prueba manual Bootstrap |

---

## 7. Umbrales de Gate

| Gate | Métricas bloqueantes |
|---|---|---|
| F7 | MQ-Q01, MQ-Q02 en módulos entregados; suites existen |
| F8 | MQ-S01…S06 |
| F10 | MQ-P01, MQ-P02, MQ-D01…D03 |
| F12 | Informe de deuda + MQ-* alcanzados o excepciones ADR |

---

## 8. Evidencia

Toda medición se almacena bajo `evidence/` (crear en F5/F7) con fecha, comando y resultado.
