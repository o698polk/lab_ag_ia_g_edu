# S08 — Roadmap / Cronograma preliminar

| Campo | Valor |
|---|---|
| Proyecto | SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`) |
| Fase | F1 — Planificación |
| Skill | K-012 Planner |
| Estado | ⏳ Pendiente de Gate F1 |
| Fuente | `prompt_master.md` §§48, 77–78, 90 |
| Fecha | 2026-09-20 |
| Unidad de tiempo | Semanas relativas (W0 = inicio tras aprobación Gate F1) |

---

## 1. Principio de planificación

```text
F1 → Gate → F2 → Gate → F3 → Gate → … → F12
```

- No avanzar sin Gate completo.
- No saltar fases (ej. F2 → F6 prohibido).
- No código de App antes de completar Spec + Skills + Configuración según flujo PolkDev.

---

## 2. Roadmap por fases PolkDev

| Fase | Nombre | Artefactos / salida | Skill principal | Semana (preliminar) | Dependencia |
|---|---|---|---|---|---|
| F1 | Planificación | S01, S02, S08 + stakeholders/restricciones/supuestos | K-012 | Completada (artefactos) | — |
| F2 | SPEC | S03–S07, S09–S12 | K-001 | W0–W1 | Gate F1 |
| F3 | Arquitectura | C4, ERD, UML, secuencias, deployment | K-002 | W1–W2 | Gate F2 |
| F4 | Skills | Registro skills K-001…K-025 asignadas a tareas | K-003 | W2 | Gate F3 |
| F5 | Configuración | venv, FastAPI, MySQL/XAMPP, `.env`, JWT, logging, tests base | K-004 | W2–W3 | Gate F4 |
| F6 | Desarrollo | DB → Models → Repos → Services → Auth → AuthZ → API → FE → AI → Gateway → PAP/PDP → Audit | K-005, K-013…K-025 | W3–W8 | Gate F5 |
| F7 | Tests | Unit, Integration, Security, E2E | K-006 | W7–W9 | Builds F6 |
| F8 | Security | OWASP, JWT, RBAC/ABAC, IDOR, secrets | K-007 | W8–W9 | Gate parcial F7 |
| F9 | Documentation | README, API, arquitectura, instalación, manuales | K-008 | W9–W10 | F6–F8 |
| F10 | Validation | Requirements, AC, tests, security, trazabilidad | K-009 | W10 | Gate F7–F9 |
| F11 | Deployment | localhost / 127.0.0.1 | K-010 | W10–W11 | Gate F10 |
| F12 | Evaluation | Performance, security, usability, coverage, deuda | K-011 | W11–W12 | Gate F11 |

> Las semanas son **preliminares** y se ajustarán en Gate F2/F3 según complejidad del ERD y del laboratorio Zero Trust.

---

## 3. Cronograma de desarrollo (F6) — orden obligatorio

```text
Database
  ↓
Models
  ↓
Repositories
  ↓
Services
  ↓
Authentication
  ↓
Authorization
  ↓
API
  ↓
Frontend
  ↓
AI
  ↓
Gateway
  ↓
PAP/PDP
  ↓
Audit
```

### 3.1 Oleadas de módulos (preliminar)

| Oleada | Semana | Módulos | Skills |
|---|---|---|---|
| O1 — Núcleo IAM | W3–W4 | Auth, Users, Roles, Permissions | K-013, K-015, K-016 |
| O2 — Catálogo académico | W4–W5 | Students, Teachers, Careers, Subjects, Terms, Curriculum | K-014, K-017 |
| O3 — Operación académica | W5–W6 | Courses/Parallels, Enrollments, Assignments, Schedules | K-017, K-013 |
| O4 — Evaluación | W6–W7 | Attendance, Evaluations, Grades, Kardex | K-017 |
| O5 — Plataforma | W7–W8 | Dashboard, Notifications, Reports, History | K-022, K-023 |
| O6 — Zero Trust / IA | W7–W8 | Tool Registry, Tool Gateway, PAP, PDP, Audit, AI | K-018…K-021 |

---

## 4. Gates (criterios resumidos)

| Gate | Condición mínima para avanzar |
|---|---|
| Gate F1 | S01/S02/S08 aprobados por humano; sin código App |
| Gate F2 | Spec completa S01–S12 coherente y trazable |
| Gate F3 | Arquitectura C4 + ERD + decisiones críticas documentadas |
| Gate F4 | Toda tarea del backlog tiene Skill asignada |
| Gate F5 | Entorno local arranca; `.env.example` sin secretos reales |
| Gate F6 | Módulos implementados según contrato Spec; sin bypass de AuthZ |
| Gate F7 | Suites de prueba ejecutadas; cobertura mínima en ruta crítica |
| Gate F8 | Hallazgos de seguridad críticos resueltos o aceptados con ADR |
| Gate F9 | Documentación alineada a implementación |
| Gate F10 | Validación humana de AC / requirements / trazabilidad |
| Gate F11 | Deploy solo localhost autorizado |
| Gate F12 | Informe de evaluación y deuda técnica |

---

## 5. Hitos (milestones)

| ID | Hito | Evidencia |
|---|---|---|
| M-01 | Plan PolkDev aprobado | Gate F1 |
| M-02 | Spec baseline congelada | Gate F2 |
| M-03 | Arquitectura aprobada | Gate F3 |
| M-04 | Skills registradas | Gate F4 |
| M-05 | Hello-world seguro local | API + MySQL + JWT smoke |
| M-06 | IAM Deny-by-Default | Tests de autorización |
| M-07 | Núcleo académico operativo | Matrícula + notas + asistencia |
| M-08 | Gateway + PDP en ruta crítica | DENY documentado (ej. student update_grade) |
| M-09 | Suite de seguridad verde en críticos | Evidence F8 |
| M-10 | Validación humana Go/No-Go | Gate F10 |

---

## 6. Riesgos de planificación (preliminar)

| ID | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| RP-01 | Presión por código prematuro | Alto | Bloqueo PolkDev; Gate F1/F2 |
| RP-02 | Subestimar PDP/Gateway | Alto | Oleada O6 temprana en diseño F3 |
| RP-03 | Disponibilidad MySQL/XAMPP | Medio | Checklist F5; scripts de verificación |
| RP-04 | Alcance académico excesivo | Alto | Priorizar O1–O4; diferir extras a Spec |
| RP-05 | IA sin políticas | Crítico | Prohibir bypass; tools solo vía Gateway |

Detalle formal de riesgos: **S11** en F2.

---

## 7. Estado actual (2026-09-20)

```text
Fase activa: F1
Artefactos F1: S01 ✅ | S02 ✅ | S08 ✅
Código App: NO iniciado (correcto)
Gate F1: ⏳ Awaiting human approval
```

---

## 8. Próximo paso tras Gate F1

Abrir **F2 — SPEC** con Skill **K-001 Spec Builder** y producir:

```text
S03 Arquitectura preliminar
S04 Casos de uso
S05 Requisitos
S06 Backlog
S07 Historias de usuario
S09 ADR
S10 Glosario
S11 Riesgos
S12 Métricas
```

Sin modificar `app/` hasta superar Gates F2–F5 según flujo.
