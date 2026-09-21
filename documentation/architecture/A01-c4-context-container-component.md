# A01 — C4 Architecture (Context · Container · Component)

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F3 — Arquitectura |
| Skill | K-002 Architecture Designer |
| Spec | S03, S05, S09 |
| Fecha | 2026-09-20 |

---

## 1. C4 Level 1 — System Context

```mermaid
C4Context
title SIGA — System Context

Person(admin, "Administrador", "Gestiona IAM, catálogos, auditoría")
Person(teacher, "Docente", "Opera cursos asignados")
Person(student, "Estudiante", "Consulta info propia y usa IA")

System(siga, "SIGA", "Sistema Integral de Gestión Académica — FastAPI + Frontend + Zero Trust")

System_Ext(mysql, "MySQL 8", "Persistencia académica e IAM (XAMPP)")
System_Ext(llm, "Proveedor LLM", "Modelo de lenguaje para asistente académico")
SystemDb_Ext(fs, "Filesystem local", "policies/, evidence/, logs")

Rel(admin, siga, "Usa")
Rel(teacher, siga, "Usa")
Rel(student, siga, "Usa")
Rel(siga, mysql, "Lee/Escribe vía SQLAlchemy")
Rel(siga, llm, "Envía prompts / recibe tool proposals")
Rel(siga, fs, "Carga políticas YAML y evidencia")
```

### Responsabilidades del sistema

| Sistema | Responsabilidad |
|---|---|
| SIGA | Autenticación, autorización, dominio académico, IA mediada, auditoría |
| MySQL | Persistencia transaccional |
| LLM | Interpretar NL y proponer tools (sin ejecución privilegiada) |
| Filesystem | Políticas versionadas y evidencia de laboratorio |

---

## 2. C4 Level 2 — Containers

```mermaid
C4Container
title SIGA — Containers

Person(user, "Usuario", "Admin / Teacher / Student")

System_Boundary(siga, "SIGA") {
  Container(fe, "Frontend Web", "HTML/CSS/JS + Bootstrap 5", "UI administrativa y dashboards")
  Container(api, "Backend API", "Python FastAPI", "REST, Auth, Services, Gateway, PDP, AI, Audit")
  ContainerDb(db, "siga_db", "MySQL 8", "Datos IAM + académicos + audit")
  Container(pol, "Policy Store", "YAML files", "policies/v1/*.yaml")
}

System_Ext(llm, "LLM Provider", "API externa o mock")

Rel(user, fe, "HTTPS localhost", "Browser")
Rel(fe, api, "JSON/REST + JWT", "Fetch API")
Rel(api, db, "SQL", "SQLAlchemy")
Rel(api, pol, "Load/version", "PAP")
Rel(api, llm, "HTTPS", "AI Service")
```

### Contratos entre contenedores

| Desde | Hacia | Protocolo | Auth |
|---|---|---|---|
| Frontend | Backend API | HTTP JSON REST | Bearer JWT |
| Backend | MySQL | TCP 3306 | Credenciales `.env` |
| Backend | LLM | HTTPS | API key en `.env` |
| Backend | Policy Store | Filesystem read | Solo proceso backend |

---

## 3. C4 Level 3 — Components (Backend)

```mermaid
C4Component
title SIGA Backend — Components

Container_Boundary(api, "Backend FastAPI") {
  Component(routes, "API Routers", "FastAPI", "Endpoints versionados; sin lógica de negocio")
  Component(authc, "Auth Module", "PyJWT + Passlib", "Login, refresh, sesiones")
  Component(svc, "Application Services", "Python", "Casos de uso académicos")
  Component(repo, "Repositories", "SQLAlchemy", "Acceso a datos")
  Component(perm, "RBAC Resolver", "Python", "roles + permisos atómicos")
  Component(pap, "PAP", "Python", "Carga y versiona políticas")
  Component(pdp, "PDP", "Python", "ALLOW / DENY + reason")
  Component(gw, "Tool Gateway (PEP)", "Python", "Valida tools, contexto, aplica PDP")
  Component(tools, "Tool Registry + Handlers", "Python", "Catálogo y ejecución autorizada")
  Component(ai, "AI Service", "Python", "NL → tool proposal")
  Component(audit, "Audit Service", "Python", "audit_events / security_events")
  Component(models, "ORM Models + Schemas", "SQLAlchemy/Pydantic", "Persistencia y validación I/O")
}

Rel(routes, authc, "Autentica")
Rel(routes, svc, "Delega casos de uso")
Rel(routes, ai, "Chat / assist")
Rel(svc, perm, "Chequeo RBAC")
Rel(svc, pdp, "Decisión contextual")
Rel(svc, repo, "CRUD")
Rel(svc, audit, "Registra")
Rel(ai, gw, "Tool proposal")
Rel(gw, tools, "Lookup registry")
Rel(gw, pdp, "Authorize")
Rel(gw, audit, "Registra decisión")
Rel(pdp, pap, "Obtiene políticas activas")
Rel(pap, models, "Opcional mirror DB")
Rel(repo, models, "Usa")
Rel(tools, svc, "Ejecuta vía servicios")
```

### Mapa componente → paquete objetivo (`app/backend/app/`)

| Componente | Paquete |
|---|---|
| API Routers | `api/` |
| Auth | `auth/` |
| Services | `services/` |
| Repositories | `repositories/` |
| RBAC | `permissions/` |
| PAP/PDP | `policy/` |
| Tool Gateway | `gateway/` |
| Tools | `tools/` |
| AI | `ai/` |
| Audit | `audit/` |
| Models/Schemas | `models/`, `schemas/` |
| Config | `core/`, `config/`, `db/` |

---

## 4. Frontend — componentes lógicos

```text
frontend/
├── pages/          # login, dashboards, módulos por rol
├── components/     # tablas, forms, nav, alerts
├── js/             # api-client, auth-store, guards UI (no autoridad real)
├── css/
└── assets/
```

Regla: **el frontend nunca autoriza**; solo oculta UI. La autoridad es siempre backend/PDP.

---

## 5. Definición de bloques F3 (checklist PromptMaster)

| Bloque | Documento / sección |
|---|---|
| Backend | A01 §3 + A04 deployment |
| Frontend | A01 §4 |
| Database | A02 ERD |
| AI | A01 + A03 SEQ-AI |
| Gateway | A01 Component `gw` + A03 SEQ-AI |
| PAP | A01 Component `pap` + A05 |
| PDP | A01 Component `pdp` + A05 |
| Audit | A01 Component `audit` + A03 |

---

## 6. Trazabilidad

| Artefacto | Relación |
|---|---|
| S03 | Vista preliminar refinada aquí |
| S09 ADR-004/005/006/007 | Decisiones aplicadas |
| A02 | Persistencia |
| A03 | Comportamiento dinámico |
| A04 | Despliegue local |
| A05 | Contratos PAP/PDP/Gateway |
