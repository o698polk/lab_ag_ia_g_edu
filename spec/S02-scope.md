# S02 — Alcance

| Campo | Valor |
|---|---|
| Proyecto | SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`) |
| Fase | F1 — Planificación |
| Skill | K-012 Planner |
| Estado | ⏳ Pendiente de Gate F1 |
| Fuente | `prompt_master.md` §§2, 4–12, 35–38, 48, 77–78 |
| Fecha | 2026-09-20 |

---

## 1. Declaración de alcance

El proyecto desarrolla **SIGA (`siga-polkdev`)**: sistema web integral para procesos académicos y administrativos de educación superior, con stack obligatorio FastAPI + Python 3.11+ + MySQL 8+ (XAMPP local) + JWT + RBAC/ABAC + IA + Zero Trust, bajo metodología PolkDev.

---

## 2. Stakeholders

| ID | Actor | Interés | Influencia |
|---|---|---|---|
| STK-01 | Product Owner / Sponsor académico | Validar alcance, gates y entrega final | Alta |
| STK-02 | Administrador del sistema | Usuarios, roles, permisos, configuración, auditoría | Alta |
| STK-03 | Docente | Cursos asignados, asistencia, evaluaciones, calificaciones | Alta |
| STK-04 | Estudiante | Notas, asistencia, horario, kardex, asistente IA | Alta |
| STK-05 | Arquitecto / Agente PolkDev | Cumplir SPEC → SKILL → APP y gates | Alta |
| STK-06 | Seguridad / Auditor | Políticas, PDP/PAP, evidencias, OWASP | Alta |
| STK-07 | Operaciones locales (DevOps local) | Entorno XAMPP/MySQL, `.env`, localhost | Media |

Roles de sistema iniciales (no confundir con stakeholders humanos):

```text
ADMINISTRATOR
TEACHER
STUDENT
```

Roles futuros (fuera del alcance inicial salvo Spec posterior):

```text
COORDINATOR, SECRETARY, ACADEMIC_DIRECTOR, REGISTRAR,
FINANCE, CAREER_DIRECTOR, SUPPORT
```

---

## 3. Dentro del alcance (In Scope)

### 3.1 Producto funcional

| Área | Incluye |
|---|---|
| Identidad | Login, logout, refresh token, cambio/recuperación de contraseña, bloqueo/desbloqueo, sesiones |
| IAM | Usuarios, roles, permisos granulares, matriz de autorización |
| Dominio académico | Estudiantes, docentes, carreras, malla, asignaturas, periodos, paralelos, matrículas, asignaciones, horarios, asistencia, evaluaciones, calificaciones, kardex |
| Experiencia | Dashboards por rol, notificaciones, reportes |
| Seguridad | JWT, revalidación servidor, Deny by Default, Zero Trust |
| Autorización avanzada | PAP, PDP, políticas versionadas |
| IA | Asistente académico vía Tool Registry + Tool Gateway (sin IA → MySQL directo) |
| Observabilidad | Auditoría técnica + historial de usuario (conceptos separados) |
| Calidad | Tests unitarios, integración, seguridad, E2E; cobertura mínima definida |
| Documentación | README, API, arquitectura, instalación, seguridad, manuales |

### 3.2 Stack tecnológico (obligatorio)

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic |
| Auth | PyJWT, Passlib/Bcrypt o Argon2 |
| DB | MySQL 8+ vía XAMPP (phpMyAdmin solo administración) |
| Frontend | HTML5, CSS3, JS ES6+, Bootstrap 5+, Fetch API, Chart.js si aplica |
| Tests | pytest, pytest-cov |
| IA | Tool calling mediado por Gateway |

### 3.3 Estructura de repositorio (objetivo)

```text
siga-polkdev/
├── spec/
├── skills/
├── app/backend/
├── app/frontend/
├── tests/
├── policies/
├── scripts/
├── evidence/
├── documentation/
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Fuera del alcance (Out of Scope) — fase actual y baseline

| ID | Excluido | Motivo |
|---|---|---|
| OOS-01 | Código de App en F1 | F1 solo planificación; Gate obligatorio |
| OOS-02 | Framework frontend pesado (React/Vue/Angular) | Requiere ADR documentado |
| OOS-03 | Backend en PHP | XAMPP solo provee MySQL |
| OOS-04 | Acceso directo IA → MySQL / API interna sin Gateway | Zero Trust / PromptMaster |
| OOS-05 | Roles extendidos (COORDINATOR, etc.) | Solo si Spec posterior lo exige |
| OOS-06 | Publicación en Internet / producción pública | Requiere autorización explícita |
| OOS-07 | Pagos, facturación, finanzas institucionales | No listado como módulo base inicial |
| OOS-08 | Integraciones ERP/LMS externas | No especificadas en PromptMaster base |
| OOS-09 | App móvil nativa | Fuera del stack obligatorio |
| OOS-10 | Go/No-Go automático en F10 | Validación humana requerida |

---

## 5. Restricciones

| ID | Restricción |
|---|---|
| R-01 | Flujo obligatorio: `SPEC → SKILL → APP` |
| R-02 | Ninguna modificación de App sin Spec + Skill + Fase |
| R-03 | No saltar fases ni gates PolkDev |
| R-04 | Deny by Default en autorización |
| R-05 | No confiar solo en claims JWT para operaciones críticas |
| R-06 | No secretos en Git ni en código fuente |
| R-07 | Lógica de negocio fuera de routes / HTML / JS / models |
| R-08 | Autorización antes de operaciones sensibles |
| R-09 | Despliegue inicial solo `localhost` / `127.0.0.1` |
| R-10 | Stack y módulos mínimos definidos por PromptMaster |

---

## 6. Supuestos

| ID | Supuesto | Si falla |
|---|---|---|
| A-01 | Existe validación humana en cada Gate | Bloqueo PolkDev |
| A-02 | XAMPP/MySQL disponible en máquina de desarrollo | Bloqueo F5 |
| A-03 | Una institución educativa como contexto de dominio | Ajustar glosario (S10) |
| A-04 | Tres roles iniciales bastan para MVP funcional | Extender vía Spec |
| A-05 | Proveedor/servicio de IA accesible en desarrollo | Mock + Spec de integración |
| A-06 | PromptMaster es la fuente normativa del contrato | Conflictos → ADR (S09) |
| A-07 | Trabajo académico/laboratorio puede exigir evidencias extra | Registrar en `evidence/` |

---

## 7. Entregables de F1 (este plan)

| Artefacto | Archivo | Estado |
|---|---|---|
| Objetivos | `spec/S01-objectives.md` | Producido |
| Alcance | `spec/S02-scope.md` | Producido |
| Roadmap / cronograma | `spec/S08-roadmap.md` | Producido |

**No se produce código en F1.**

---

## 8. Criterios de aceptación del Gate F1

- [ ] S01, S02 y S08 existen y son coherentes entre sí
- [ ] Stakeholders, restricciones y supuestos están explícitos
- [ ] In Scope / Out of Scope claros
- [ ] Roadmap alineado a fases F1–F12 y gates
- [ ] Aprobación humana explícita para abrir F2 (SPEC)

---

## 9. Próxima fase (solo tras Gate F1)

**F2 — SPEC**: S03 Arquitectura preliminar, S04 Casos de uso, S05 Requisitos, S06 Backlog, S07 Historias, S09 ADR, S10 Glosario, S11 Riesgos, S12 Métricas (S01/S02/S08 se refinan si el Gate lo exige).
