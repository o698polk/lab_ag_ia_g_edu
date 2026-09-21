# S06 — Backlog

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC · **Skills confirmadas en F4** |
| Skill | K-001 Spec Builder → K-003 Skill Creator |
| Nota F4 | Toda tarea sin Skill = BLOQUEADA |
| Matriz Skills | `skills/01-BACKLOG-MATRIX.md` |
| Registro | `skills/00-REGISTRY.md` |
| Fecha | 2026-09-20 |
| Actualizado | 2026-09-20 (Gate F3 → F4) |

---

## 1. Convención

```text
BL-<OLEADA>-NNN
Prioridad: P0 > P1 > P2
Estado: Backlog | Ready | Blocked | Done
```

Skills **confirmadas** en F4 (ver matriz). Columna "Skill" = Skill primaria Assigned.

---

## 2. Épicas

| Épica | Descripción | Oleada |
|---|---|---|
| EP-IAM | Autenticación y autorización base | O1 |
| EP-CAT | Catálogo académico | O2 |
| EP-OPS | Operación (cursos, matrículas, asignaciones) | O3 |
| EP-EVL | Asistencia, evaluaciones, notas, kardex | O4 |
| EP-PLT | Dashboard, reportes, notificaciones, historial | O5 |
| EP-ZT | Gateway, PAP/PDP, Tool Registry, IA, Audit | O6 |
| EP-QA | Tests, security, docs, validation | Transversal |

---

## 3. Backlog priorizado (P0 primero)

### O1 — Núcleo IAM

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O1-001 | Modelo users/roles/permissions + migraciones | RF-IAM-* | K-014 | P0 | Done (F6-O1) |
| BL-O1-002 | Auth login/logout/refresh JWT | RF-AUTH-001…004 | K-015 | P0 | Done (F6-O1) |
| BL-O1-003 | Hash passwords + políticas de sesión | RF-AUTH-008/009 | K-015 | P0 | Done (F6-O1) |
| BL-O1-004 | Servicios/API usuarios | RF-IAM-001…003 | K-013 | P0 | Done (F6-O1) |
| BL-O1-005 | Servicios/API roles y permisos | RF-IAM-004…007 | K-016 | P0 | Done (F6-O1) |
| BL-O1-006 | Middleware Deny by Default | RF-IAM-008, RF-AZN-* | K-016 | P0 | Done (F6-O1) |
| BL-O1-007 | Seed roles base ADMIN/TEACHER/STUDENT | RF-IAM-007 | K-024 | P0 | Done (F6-O1) |
| BL-O1-008 | Tests auth/IAM | RNF-QUA-001 | K-006 | P0 | Done (F6-O1) |

### O2 — Catálogo académico

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O2-001 | Modelos students/teachers | RF-STU/TCH | K-014 | P0 | Done (F6-O2) |
| BL-O2-002 | Modelos careers/curriculum/subjects/prereqs | RF-CAR/CUR/SUB | K-014 | P0 | Done (F6-O2) |
| BL-O2-003 | Modelos academic_terms + reglas CLOSED | RF-TRM-* | K-017 | P0 | Done (F6-O2) |
| BL-O2-004 | APIs catálogo + validaciones | RF-* | K-013 (+K-017) | P0 | Done (F6-O2) |
| BL-O2-005 | UI admin catálogo | RNF-UX-001 | K-022 | P1 | Backlog |

### O3 — Operación académica

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O3-001 | Courses/sections + cupos | RF-CRS-001 | K-014 | P0 | Done (F6-O3) |
| BL-O3-002 | Teaching assignments | RF-ASN-001 | K-017 | P0 | Done (F6-O3) |
| BL-O3-003 | Enrollments | RF-ENR-* | K-017 | P0 | Done (F6-O3) |
| BL-O3-004 | Schedules + conflictos | RF-SCH-001 | K-017 | P1 | Done (F6-O3) |
| BL-O3-005 | APIs + UI operación | — | K-013 (+K-022) | P0 | Done API (UI P1) |

### O4 — Evaluación

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O4-001 | Attendance records + % | RF-ATT-* | K-017 | P0 | Done (F6-O4) |
| BL-O4-002 | Evaluations + validación % | RF-EVL-001 | K-017 | P0 | Done (F6-O4) |
| BL-O4-003 | Grades + transacción | RF-GRD-001 | K-017 | P0 | Done (F6-O4) |
| BL-O4-004 | ABAC: solo docente asignado | RF-AZN-001 | K-016 | P0 | Done (F6-O4) |
| BL-O4-005 | Consulta notas estudiante (IDOR-safe) | RF-GRD-002 | K-016 | P0 | Done (F6-O4) |
| BL-O4-006 | Kardex | RF-KAR-001 | K-017 | P1 | Done (F6-O4) |
| BL-O4-007 | Tests autorización grades/attendance | — | K-006 (+K-007) | P0 | Done (F6-O4) |

### O5 — Plataforma

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O5-001 | Dashboards por rol | RF-DSH-001 | K-022 | P1 | Done (F6-O5) |
| BL-O5-002 | Reportes HTML/CSV/JSON + logs | RF-REP-* | K-023 | P1 | Done (F6-O5) |
| BL-O5-003 | Notificaciones | RF-NTF-001 | K-013 | P2 | Done (F6-O5) |
| BL-O5-004 | Historial de usuario (≠ auditoría) | RF-AUD-002 | K-021 | P1 | Done (F6-O5) |
| BL-O5-005 | Export PDF reportes | RF-REP-001 | K-023 | P2 | Backlog |

### O6 — Zero Trust / IA

| ID | Ítem | RF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-O6-001 | PAP loader policies/v1 | RF-PAP-001 | K-020 | P0 | Done (F6-O6) |
| BL-O6-002 | PDP ALLOW/DENY | RF-PDP-001 | K-020 | P0 | Done (F6-O6) |
| BL-O6-003 | Tool Registry | RF-AI-003/004 | K-019 | P0 | Done (F6-O6) |
| BL-O6-004 | Tool Gateway PEP | RF-GW-001 | K-019 | P0 | Done (F6-O6) |
| BL-O6-005 | AI service + CURRENT_USER binding | RF-AI-001/005 | K-018 | P0 | Done (F6-O6) |
| BL-O6-006 | Audit/security events | RF-AUD-* | K-021 | P0 | Done (F6-O6) |
| BL-O6-007 | Escenario DENY update_grade vía IA | RF-AI-002 | K-007 (+K-025) | P0 | Done (F6-O6) |
| BL-O6-008 | Policies YAML (auth, grades, attendance, ai…) | RF-PAP-001 | K-020 | P0 | Done (F6-O6) |

### Transversal QA / Docs / Config

| ID | Ítem | RF/RNF | Skill | P | Estado |
|---|---|---|---|---|---|
| BL-QA-001 | Scaffold proyecto + venv + .env.example | RNF-DEP/SEC | K-004 | P0 | Done (F5) |
| BL-QA-002 | Suite unit/integration | RNF-QUA-001 | K-006 | P0 | Done (F7) |
| BL-QA-003 | Suite security (IDOR, JWT, SQLi, XSS) | RNF-SEC-001 | K-007 | P0 | Done (F7) |
| BL-QA-004 | E2E flujos críticos | — | K-006 | P1 | Done (F7) |
| BL-QA-005 | Documentación API/arquitectura/seguridad | — | K-008 | P1 | Done (F9) |
| BL-QA-006 | Validación Gate F10 | — | K-009 | P0 | Backlog |

---

## 4. Orden de extracción a Ready

1. ~~Completar F3 arquitectura + F4 skills.~~ ✅ (pendiente solo Gate F4 humano)  
2. F5 configuración (BL-QA-001) — Skill K-004.  
3. O1 → O2 → O3 → O4 en paralelo controlado con O6 (PAP/PDP ya diseñados en F3).  
4. O5 tras núcleo académico estable.  
5. QA continuo desde O1.

**Asignación formal:** `skills/01-BACKLOG-MATRIX.md` (0 huérfanas).

---

## 5. Definición de Ready (DoR)

- Spec (RF/HU) referenciada  
- Skill asignada (F4)  
- Criterios de aceptación claros  
- Dependencias conocidas  
- Sin secretos ni alcance fuera de S02  

## 6. Definición de Done (DoD)

- Implementado según capas  
- Tests asociados pasan  
- Autorización verificada  
- Auditoría si es sensible  
- Documentación mínima del módulo  
- Trazabilidad actualizada  
