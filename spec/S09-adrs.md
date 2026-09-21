# S09 — Architecture Decision Records (ADR)

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fecha | 2026-09-20 |

Estados: **Accepted** | **Proposed** | **Superseded**

---

## ADR-001 — Stack backend FastAPI + MySQL

**Estado:** Accepted  
**Contexto:** Se requiere API REST segura, tipada y productiva para dominio académico.  
**Decisión:** Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, MySQL 8+ (XAMPP local).  
**Consecuencias:** Ecosistema maduro; dependencia de MySQL local; no usar PHP como runtime de App.

---

## ADR-002 — Hashing de contraseñas

**Estado:** Proposed (resolver en F5)  
**Contexto:** RF-AUTH-009 exige hash seguro.  
**Opciones:** Argon2id · Bcrypt (Passlib)  
**Decisión preliminar:** Preferir **Argon2id**; fallback Bcrypt si hay fricción de dependencias en entorno local.  
**Consecuencias:** Migración de hashes si se cambia algoritmo → documentar en F5.

---

## ADR-003 — Frontend sin SPA pesado

**Estado:** Accepted  
**Contexto:** PromptMaster impone HTML/CSS/JS + Bootstrap 5+.  
**Decisión:** No React/Vue/Angular salvo ADR futuro justificado.  
**Consecuencias:** Menor complejidad; UI administrativa clásica; Fetch API.

---

## ADR-004 — Autorización RBAC + permisos + ABAC + PDP

**Estado:** Accepted  
**Contexto:** Roles solos son insuficientes; Zero Trust exige contexto.  
**Decisión:** RBAC + permisos atómicos + ABAC (teaching_assignment, ownership) + PAP/PDP; Deny by Default; ADMIN no omnipotente.  
**Consecuencias:** Más diseño de políticas; mayor seguridad; tests de autorización obligatorios.

---

## ADR-005 — JWT no es autorización absoluta

**Estado:** Accepted  
**Contexto:** Tokens pueden filtrarse o quedar desactualizados.  
**Decisión:** JWT identifica sesión; cada op crítica revalida identidad, estado, rol, permiso, recurso, contexto y política.  
**Consecuencias:** Latencia adicional aceptable; mayor seguridad.

---

## ADR-006 — IA solo propone; Gateway decide

**Estado:** Accepted  
**Contexto:** Riesgo de prompt injection / privilege escalation vía IA.  
**Decisión:** Tool Registry + Tool Gateway (PEP) + PDP; IA sin SQL/MySQL/credenciales/bypass.  
**Consecuencias:** Arquitectura de laboratorio Zero Trust alineada; tools sensibles auditados.

---

## ADR-007 — Políticas como código en `policies/v1`

**Estado:** Accepted  
**Contexto:** Evitar permisos hardcodeados en controladores.  
**Decisión:** YAML versionados (authentication, students, grades, attendance, reports, ai, …) administrados por PAP.  
**Consecuencias:** Requiere loader + validación de schema; cambios de política trazables.

---

## ADR-008 — Soft delete en datos académicos críticos

**Estado:** Accepted  
**Contexto:** Integridad histórica y auditoría.  
**Decisión:** No borrado físico de información académica crítica salvo Spec explícita.  
**Consecuencias:** Consultas deben filtrar `deleted_at`/status.

---

## ADR-009 — Despliegue solo localhost en F11

**Estado:** Accepted  
**Contexto:** Entorno de desarrollo/laboratorio.  
**Decisión:** Bind a 127.0.0.1; sin Internet público sin autorización humana.  
**Consecuencias:** No CI/CD cloud obligatorio en baseline.

---

## ADR-010 — Cobertura de pruebas mínima

**Estado:** Accepted  
**Contexto:** Invariantes PolkDev.  
**Decisión:** Líneas ≥ 80%, ramas ≥ 70%; suites unit/integration/security/e2e.  
**Consecuencias:** Tiempo de F7/F8 significativo; automatizar desde O1.

---

## ADR-011 — Proveedor LLM

**Estado:** Proposed  
**Contexto:** Módulo IA requiere backend de modelo.  
**Opciones:** API cloud · modelo local · mock en tests  
**Decisión:** Definir en F5; tests deben poder mockear el proveedor.  
**Consecuencias:** Abstracción `AIProvider` obligatoria.

---

## ADR-012 — Nombre técnico del repo

**Estado:** Accepted  
**Contexto:** Identidad de proyecto.  
**Decisión:** Nombre técnico `siga-polkdev`; carpeta de trabajo actual puede migrar/estructurarse hacia layout PromptMaster en F5 sin romper Spec.  
**Consecuencias:** README y paths se alinean en F5/F9.
