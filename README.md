# SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`)

Metodología **PolkDev**: `SPEC → SKILL → APP` con gates humanos.

**Cierre laboratorio:** F1–F12 · **ACEPTADO CONDICIONADO** (2026-09-20) · evidencia `evidence/f12/GATE-F12.md`.

## Estado

| Fase | Estado |
|---|---|
| F1 Planificación | ✅ |
| F2 SPEC | ✅ |
| F3 Arquitectura | ✅ |
| F4 Skills | ✅ |
| F5 Configuración | ✅ |
| F6 Desarrollo | ✅ O1–O6 |
| F7 Tests | ✅ |
| F8 Security | ✅ |
| F9 Documentation | ✅ |
| F10 Validation | ✅ GO CONDICIONADO |
| F11 Deployment | ✅ GO |
| F12 Evaluation | ✅ CERRADO CONDICIONADO |

## Stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic, JWT
- DB: MySQL 8+ (XAMPP) · SQLite en tests
- Frontend: HTML/CSS/JS + Bootstrap 5 (`/ui/`)
- Seguridad: RBAC + ABAC + PAP/PDP + Tool Gateway · Deny-by-Default

## Arranque rápido

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
# Preferido en Windows (no usa Activate.ps1):
.\start-siga.bat
# O:
# $env:APP_ENV="local"
# .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Si `Activate.ps1` falla por ExecutionPolicy, **no** uses el `python` del sistema (faltará `jwt`). Usa `.\.venv\Scripts\python.exe` o `start-siga.bat`.

Guía completa: [`documentation/deployment/INSTALACION.md`](documentation/deployment/INSTALACION.md) · Arranque diario: [`documentation/GUIA-ARRANQUE.md`](documentation/GUIA-ARRANQUE.md)

| URL | Uso |
|---|---|
| http://127.0.0.1:8000/api/v1/health | Health |
| http://127.0.0.1:8000/docs | OpenAPI |
| http://127.0.0.1:8000/ui/ | UI dashboard |

## Documentación (F9)

Índice: [`documentation/D00-index.md`](documentation/D00-index.md)

| Tema | Enlace |
|---|---|
| Instalación | [INSTALACION](documentation/deployment/INSTALACION.md) |
| Configuración | [CONFIGURACION](documentation/deployment/CONFIGURACION.md) |
| Base de datos | [BASE-DE-DATOS](documentation/deployment/BASE-DE-DATOS.md) |
| API | [API](documentation/api/API.md) |
| Arquitectura | [A00](documentation/architecture/A00-index.md) |
| Seguridad | [SEC-01](documentation/security/SEC-01-owasp-assessment.md) |
| Manual usuario | [MANUAL-USUARIO](documentation/manuals/MANUAL-USUARIO.md) |
| Manual administrador | [MANUAL-ADMINISTRADOR](documentation/manuals/MANUAL-ADMINISTRADOR.md) |

## Spec / Skills / Evidencia

- Spec: `spec/`
- Skills: `skills/`
- PromptMaster: `prompt_master.md`
- Evidencia: `evidence/`

## Reglas

- Ningún secreto en Git.
- Ningún código de negocio sin Spec + Skill + Gate.
- Despliegue solo **localhost** (ADR-009).
