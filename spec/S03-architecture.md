# S03 — Arquitectura preliminar

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC · **refinado en F3** |
| Skill | K-001 Spec Builder → K-002 Architecture Designer |
| Detalle F3 | Ver `documentation/architecture/A00-index.md` |
| Fuente | `prompt_master.md` §§4–8, 35–44, 48, 82 |
| Fecha | 2026-09-20 |
| Actualizado | 2026-09-20 (Gate F2 → F3) |

---

## 1. Vista de contexto (C4 L1 — preliminar)

```text
[Administrador] ─┐
[Docente] ───────┼──► [SIGA Web] ──► [MySQL 8]
[Estudiante] ────┘         │
                           ├──► [Servicio IA / LLM]
                           └──► [Sistema de archivos local: policies, evidence, logs]
```

Actores externos: usuarios humanos por rol.  
Sistemas externos: proveedor de modelo IA (API). MySQL es persistencia primaria vía XAMPP local.

---

## 2. Vista de contenedores (C4 L2 — preliminar)

```text
┌─────────────────────────────────────────────────────────┐
│ Frontend (HTML/CSS/JS + Bootstrap 5)                    │
│  pages / components / Fetch API                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS/HTTP localhost
┌───────────────────────▼─────────────────────────────────┐
│ Backend FastAPI                                         │
│  API · Auth · Services · Repositories · Gateway · PDP  │
│  AI Service · Audit · PAP loader                        │
└───────┬─────────────────────────────┬───────────────────┘
        │                             │
        ▼                             ▼
   [MySQL 8]                   [policies/v1/*.yaml]
        │                             │
        └────────── Tool Registry / tool_invocations
```

---

## 3. Capas lógicas (obligatorias)

```text
Presentation (Frontend)
     ↓
API (routes/controllers — sin lógica de negocio)
     ↓
Application (services)
     ↓
Domain (reglas académicas + políticas de negocio)
     ↓
Authorization (PEP Gateway → PDP ← PAP)
     ↓
Repository
     ↓
Database (MySQL)
```

Auditoría transversal en operaciones sensibles.

---

## 4. Componentes backend (preliminar)

| Componente | Responsabilidad |
|---|---|
| `core` / `config` | Settings, logging, constants |
| `auth` | JWT access/refresh, sesiones, password hashing |
| `permissions` | Catálogo de permisos y resolución RBAC |
| `policy` (PAP) | Carga/versionado de políticas YAML |
| `gateway` (PEP) | Validación tool/schema, identity/context, llamada PDP |
| `policy` PDP | Decisión ALLOW/DENY + reason_code |
| `services` | Casos de uso académicos |
| `repositories` | Acceso SQLAlchemy |
| `models` / `schemas` | ORM + Pydantic |
| `ai` | Interpretación NL → tool proposal |
| `tools` | Tool Registry + handlers |
| `audit` | audit_events / security_events |
| `api` | Routers versionados |

---

## 5. Flujo Zero Trust (operación crítica / tool)

```text
JWT → Identity → User status → Role → Permission
  → Context → Policy (PDP) → Decision → Action → Audit
```

Regla: **Deny by Default**. JWT no autoriza por sí solo.

---

## 6. Flujo IA → Tool Gateway

```text
Usuario → Frontend → FastAPI AI Service → Modelo IA
  → Tool Proposal → Schema Validation → Tool Registry
  → Tool Gateway (PEP) → Identity/Context → PDP
  → ALLOW|DENY → Tool Handler → DB → Audit
```

Prohibido: IA → SQL, IA → MySQL, IA → credenciales, IA → bypass PDP.

---

## 7. Modelo de datos (entidades mínimas)

```text
IAM: users, roles, permissions, role_permissions, user_roles,
     sessions, refresh_tokens

Académico: students, teachers, careers, curriculum, subjects,
           subject_prerequisites, academic_terms, courses,
           course_sections, enrollments, teaching_assignments,
           schedules, classrooms, attendance, attendance_records,
           evaluation_types, evaluations, grades,
           academic_history, kardex

Plataforma: reports, report_logs, notifications,
            audit_events, security_events,
            ai_conversations, ai_messages,
            tool_registry, tool_invocations,
            policies, policy_versions, policy_decisions
```

Integridad: PK/FK, unique, indexes, checks, soft delete, timestamps, transacciones en operaciones críticas.

---

## 8. Frontend (preliminar)

| Área | Contenido |
|---|---|
| Auth | Login / logout / cambio contraseña |
| Admin | Usuarios, roles, permisos, periodos, catálogos, auditoría |
| Teacher | Cursos, asistencia, evaluaciones, calificaciones |
| Student | Notas, asistencia, horario, kardex, asistente IA |
| Shared | Dashboard, notificaciones, reportes autorizados |

Sin framework SPA pesado salvo ADR futuro.

---

## 9. Despliegue preliminar (F11)

```text
Developer machine
 ├── XAMPP → MySQL 8
 ├── Uvicorn → FastAPI (127.0.0.1)
 └── Browser → Frontend estático / servido local
```

Sin publicación a Internet sin autorización explícita.

---

## 10. Decisiones abiertas (para F3 / S09)

| ID | Tema | Estado |
|---|---|---|
| OPEN-01 | Argon2 vs Bcrypt | Ver ADR-002 |
| OPEN-02 | Formato exacto de policies YAML | Detallar en F3 |
| OPEN-03 | Proveedor LLM concreto | ADR en F3/F5 |
| OPEN-04 | PDF generation library | Diferido a módulo reportes |

---

## 11. Artefactos F3 (detalle normativo)

| ID | Ubicación | Contenido |
|---|---|---|
| A00 | `documentation/architecture/A00-index.md` | Índice |
| A01 | `.../A01-c4-context-container-component.md` | C4 L1–L3 |
| A02 | `.../A02-erd.md` | ERD completo |
| A03 | `.../A03-uml-sequences.md` | UML + secuencias |
| A04 | `.../A04-deployment.md` | Deployment localhost |
| A05 | `.../A05-gateway-pap-pdp-audit.md` | PAP / PDP / Gateway / Audit |

Este S03 permanece como **vista preliminar ejecutiva**. El detalle de diseño para implementación es A01–A05.

---

## 12. Trazabilidad

| Relaciona | Con |
|---|---|
| S01 / S02 | Objetivos y alcance |
| S05 | Requisitos no funcionales de arquitectura |
| S09 | ADRs de stack y seguridad |
| A01–A05 | Diagramas y contratos F3 |
