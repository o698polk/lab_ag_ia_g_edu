# Matriz Backlog ↔ Skill

| Campo | Valor |
|---|---|
| Fase | F4 — Skills |
| Skill | K-003 Skill Creator |
| Fuente backlog | `spec/S06-backlog.md` |
| Fecha | 2026-09-20 |
| Resultado | **0 tareas sin Skill** |

Convención: **Skill primaria** ejecuta; **Skill apoyo** colabora/revisa.  
Estado post-F4: `Ready` solo tras Gate F4 + DoR; aquí se marca asignación = **Assigned**.

---

## O1 — IAM

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O1-001 | K-014 | K-005 | Assigned |
| BL-O1-002 | K-015 | K-013 | Assigned |
| BL-O1-003 | K-015 | K-007 | Assigned |
| BL-O1-004 | K-013 | K-016 | Assigned |
| BL-O1-005 | K-016 | K-013 | Assigned |
| BL-O1-006 | K-016 | K-020 | Assigned |
| BL-O1-007 | K-024 | K-016 | Assigned |
| BL-O1-008 | K-006 | K-007 | Assigned |

## O2 — Catálogo

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O2-001 | K-014 | K-017 | Assigned |
| BL-O2-002 | K-014 | K-017 | Assigned |
| BL-O2-003 | K-017 | K-014 | Assigned |
| BL-O2-004 | K-013 | K-017 | Assigned |
| BL-O2-005 | K-022 | K-013 | Assigned |

## O3 — Operación

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O3-001 | K-014 | K-017 | Assigned |
| BL-O3-002 | K-017 | K-016 | Assigned |
| BL-O3-003 | K-017 | K-013 | Assigned |
| BL-O3-004 | K-017 | K-006 | Assigned |
| BL-O3-005 | K-013 | K-022 | Assigned |

## O4 — Evaluación

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O4-001 | K-017 | K-016 | Assigned |
| BL-O4-002 | K-017 | K-013 | Assigned |
| BL-O4-003 | K-017 | K-021 | Assigned |
| BL-O4-004 | K-016 | K-020 | Assigned |
| BL-O4-005 | K-016 | K-007 | Assigned |
| BL-O4-006 | K-017 | K-023 | Assigned |
| BL-O4-007 | K-006 | K-007 | Assigned |

## O5 — Plataforma

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O5-001 | K-022 | K-013 | Done (F6-O5) |
| BL-O5-002 | K-023 | K-021 | Done (F6-O5) |
| BL-O5-003 | K-013 | K-022 | Done (F6-O5) |
| BL-O5-004 | K-021 | K-013 | Done (F6-O5) |
| BL-O5-005 | K-023 | K-008 | Assigned |

## O6 — Zero Trust / IA

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-O6-001 | K-020 | K-005 | Assigned |
| BL-O6-002 | K-020 | K-016 | Assigned |
| BL-O6-003 | K-019 | K-018 | Assigned |
| BL-O6-004 | K-019 | K-020 | Assigned |
| BL-O6-005 | K-018 | K-019 | Assigned |
| BL-O6-006 | K-021 | K-007 | Assigned |
| BL-O6-007 | K-007 | K-025 | Assigned |
| BL-O6-008 | K-020 | K-008 | Assigned |

## Transversal QA / Config / Docs

| BL | Skill primaria | Skill apoyo | Estado Skill |
|---|---|---|---|
| BL-QA-001 | K-004 | K-005 | Assigned |
| BL-QA-002 | K-006 | K-005 | Assigned |
| BL-QA-003 | K-007 | K-006 | Assigned |
| BL-QA-004 | K-006 | K-022 | Assigned |
| BL-QA-005 | K-008 | K-009 | Assigned |
| BL-QA-006 | K-009 | K-011 | Assigned |

---

## Artefactos de fase (ya ejecutados / por ejecutar)

| Artefacto / Fase | Skill |
|---|---|
| F1 Plan S01/S02/S08 | K-012 |
| F2 Spec S03–S12 | K-001 |
| F3 Architecture A01–A05 | K-002 |
| F4 Skills registry | K-003 |
| F5 Config | K-004 |
| F6 Implementation | K-005 (+ especialistas) |
| F7 Tests | K-006 |
| F8 Security | K-007 |
| F9 Docs | K-008 |
| F10 Validation | K-009 |
| F11 Deploy | K-010 |
| F12 Evaluation | K-011 |
| Mediciones laboratorio | K-025 |

---

## Verificación Gate F4

| Criterio | Resultado |
|---|---|
| K-001…K-025 registrados | ✅ 25/25 |
| Todo BL-* tiene Skill primaria | ✅ |
| Tareas huérfanas | ✅ 0 |
| Matriz publicada | ✅ este archivo |

## Regla operativa

```text
Si aparece un nuevo ítem de backlog sin Skill → Estado = BLOQUEADA
hasta asignación formal por K-003.
```
