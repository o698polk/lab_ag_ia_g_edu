# F10 — Matriz de trazabilidad RF → Backlog → Tests

| Campo | Valor |
|---|---|
| Fase | F10 |
| Skill | K-009 |
| Fecha | 2026-09-20 |
| Fuente | S05 · S06 · S07 · suites `tests/` |

**Leyenda:** ✅ Verificado · ⚠ Parcial · ❌ No implementado · P2 diferido

## 1. Auth / IAM (P0)

| RF | BL | Evidencia test | Estado |
|---|---|---|---|
| RF-AUTH-001 | BL-O1-002 | `test_login_success` | ✅ |
| RF-AUTH-002 | BL-O1-002 | tokens en login | ✅ |
| RF-AUTH-003 | BL-O1-002 | `test_refresh_and_logout` | ✅ |
| RF-AUTH-004 | BL-O1-002 | logout + refresh revoke | ✅ |
| RF-AUTH-005 | BL-O1-002 | `test_change_password` | ✅ |
| RF-AUTH-006 | — | recuperación password | ❌ P1 gap |
| RF-AUTH-007 | BL-O1-004 | status BLOCKED + login deny | ✅ |
| RF-AUTH-008 | BL-O1-002 | TTL JWT config | ✅ |
| RF-AUTH-009 | BL-O1-003 | argon2 hash | ✅ |
| RF-IAM-001 | BL-O1-004 | users CRUD lógico | ✅ |
| RF-IAM-002 | BL-O1-004 | PATCH status | ✅ |
| RF-IAM-003 | BL-O1-004 | PUT roles | ✅ |
| RF-IAM-004 | BL-O1-005 | roles list/assign perms (CRUD create rol ⚠) | ⚠ |
| RF-IAM-005 | BL-O1-005 | GET permissions | ✅ |
| RF-IAM-006 | BL-O1-005 | PUT role permissions | ✅ |
| RF-IAM-007 | BL-O1-007 | seed ADMIN/TEACHER/STUDENT | ✅ |
| RF-IAM-008 | BL-O1-006 | Deny-by-Default tests | ✅ |

## 2. Académico / operación / evaluación (P0–P1)

| RF | BL | Evidencia | Estado |
|---|---|---|---|
| RF-STU/TCH/CAR/CUR/SUB | O2 | catalog tests | ✅ |
| RF-TRM-001/002 | O2/O3 | CLOSED bloquea | ✅ |
| RF-CRS/ASN/ENR | O3 | operations + integration | ✅ |
| RF-SCH-001 | O3 | conflictos horario | ✅ |
| RF-ATT-001/002 | O4 | evaluation tests | ✅ |
| RF-EVL-001 | O4 | weight ≤100 | ✅ |
| RF-GRD-001/002 | O4 | ABAC + IDOR | ✅ |
| RF-KAR-001 | O4 | kardex | ✅ |
| RF-REP-001/002 | O5 | reports + logs (PDF P2 ❌) | ✅ / PDF P2 |
| RF-NTF-001 | O5 | notifications | ✅ |
| RF-DSH-001 | O5 | dashboard por rol | ✅ |

## 3. Zero Trust / IA / Audit (P0)

| RF | BL | Evidencia | Estado |
|---|---|---|---|
| RF-AZN-001…003 | O1/O6 | RBAC+ABAC+PDP | ✅ |
| RF-PAP-001 | O6 | policies/v1 | ✅ |
| RF-PDP-001 | O6 | `test_pdp_*` | ✅ |
| RF-GW-001 | O6 | ToolGateway | ✅ |
| RF-AI-001…005 | O6 | chat + CURRENT_USER + no SQL | ✅ |
| RF-AI-002 ataque | BL-O6-007 | DENY update_grade | ✅ |
| RF-AUD-001…003 | O6 | audit/security events | ✅ |
| RF-AUD-002 | O5/O6 | history ≠ audit | ✅ |

## 4. Gaps documentados (no bloquean lab P0 si se aceptan)

| Gap | Prioridad Spec | Nota |
|---|---|---|
| Recuperación de contraseña | P1 | Fuera de baseline lab |
| CRUD completo de roles (create/delete API) | P0 parcial | Seed + assign OK |
| UI catálogo completa | P1 | `/ui/` dashboard mínimo |
| Export PDF reportes | P2 | 501 diferido |
| Cobertura ramas global ≥70% | RNF-QUA | ADR-013 · ruta crítica OK |

## 5. Historias P0 — CA

| HU | CA verificados | Tests |
|---|---|---|
| HU-AUTH-001/002 | ✅ | iam_auth |
| HU-IAM-001/002 | ✅ | iam + security |
| HU-TRM-001 | ✅ | operations/integration |
| HU-ASN/ENR | ✅ | operations |
| HU-ATT/EVL/GRD/KAR | ✅ | evaluation |
| HU-AI-001/002 | ✅ | zero_trust + e2e |
| HU-AUD-001 | ✅ | audit API |
| HU-REP-001 | ✅ | platform |
