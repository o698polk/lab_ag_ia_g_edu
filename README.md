# SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`)

Metodología **PolkDev**: `SPEC → SKILL → APP` con gates humanos.

**Cierre laboratorio:** F1–F12 · **ACEPTADO CONDICIONADO** (2026-09-20) · evidencia `evidence/f12/GATE-F12.md`.

Solo **localhost** (`127.0.0.1`). FastAPI sirve la API y la UI (`/ui/`); no hay servidor frontend aparte.

---

## Guía de arranque (paso a paso)

### Requisitos

| Requisito | Notas |
|---|---|
| Windows + PowerShell o CMD | Ruta del repo: `d:\PROYECTOS\lab_ag_ia_g_edu` |
| Python 3.11+ | Con venv en `.venv` |
| XAMPP MySQL 8+ | Puerto `3306`, base `siga` |

---

### Paso 0 — Ir al proyecto

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
```

---

### Paso 1 — Arrancar MySQL (XAMPP)

1. Abre **XAMPP Control Panel**.
2. Pulsa **Start** en **MySQL**.
3. Comprueba:

```powershell
.\.venv\Scripts\python.exe scripts\check_mysql.py
```

Debes ver: `OK: MySQL reachable`.

Si falla: crea la base `siga` en phpMyAdmin y revisa usuario/clave en `.env` (`DB_USER`, `DB_PASSWORD`).

---

### Paso 2 — Primera vez (solo instalación)

Haz esto **una vez** (o tras clonar el repo):

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu

# 2.1 Entorno virtual
python -m venv .venv

# 2.2 Dependencias (usa el Python del venv; no el de sistema)
.\.venv\Scripts\python.exe -m pip install -r app\backend\requirements.txt

# 2.3 Variables de entorno
copy .env.example .env
# Edita .env: JWT_SECRET (mín. 32 caracteres) y credenciales MySQL si aplica

# 2.4 Validar .env
.\.venv\Scripts\python.exe scripts\check_env.py

# 2.5 Migraciones + datos demo
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts\seed_iam.py
.\.venv\Scripts\python.exe scripts\seed_demo_academic.py
```

Credenciales lab: [`documentation/CREDENCIALES-USUARIOS.md`](documentation/CREDENCIALES-USUARIOS.md)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | Administrador |
| `teacher1` | `Teacher123!` | Docente |
| `student1` | `Student123!` | Estudiante |

---

### Paso 3 — Arrancar la aplicación (cada día)

**Opción A — recomendada (Windows)**

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
.\start-siga.bat
```

**Opción B — PowerShell (sin Activate.ps1)**

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
$env:APP_ENV = "local"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Deja esa ventana abierta. Debes ver:

```text
Uvicorn running on http://127.0.0.1:8000
```

> Si `Activate.ps1` falla por ExecutionPolicy, **no** uses el `python` del sistema (faltará `jwt`). Usa siempre `.\.venv\Scripts\python.exe` o `start-siga.bat`.

---

### Paso 4 — Verificar que está arriba

En **otra** terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health -UseBasicParsing
```

| URL | Uso |
|---|---|
| http://127.0.0.1:8000/ui/ | UI (home → login) |
| http://127.0.0.1:8000/ui/pages/auth/login.html | Login |
| http://127.0.0.1:8000/ui/pages/dashboard/dashboard.html | Dashboard (con sesión) |
| http://127.0.0.1:8000/api/v1/health | Health API |
| http://127.0.0.1:8000/docs | OpenAPI (Swagger) |

---

### Paso 5 — Parar la aplicación

- En la ventana de uvicorn: `Ctrl+C`
- Si el puerto 8000 quedó ocupado:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { if ($_.OwningProcess -gt 0) { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }
```

---

### Resumen rápido (ya instalado)

```powershell
# 1) XAMPP → Start MySQL
# 2) Arrancar SIGA
cd d:\PROYECTOS\lab_ag_ia_g_edu
.\start-siga.bat
# 3) Abrir http://127.0.0.1:8000/ui/
#    login: admin / Admin123!
```

Guía ampliada: [`documentation/GUIA-ARRANQUE.md`](documentation/GUIA-ARRANQUE.md) · Instalación: [`documentation/deployment/INSTALACION.md`](documentation/deployment/INSTALACION.md)

---

## Estado del laboratorio

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
- Frontend: HTML/CSS/JS + Bootstrap 5 (`/ui/assets/` + `/ui/pages/`)
- Seguridad: RBAC + ABAC + PAP/PDP + Tool Gateway · Deny-by-Default

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
| Credenciales lab | [CREDENCIALES-USUARIOS](documentation/CREDENCIALES-USUARIOS.md) |

## Spec / Skills / Evidencia

- Spec: `spec/`
- Skills: `skills/`
- PromptMaster: `prompt_master.md`
- Evidencia: `evidence/`

## Reglas

- Ningún secreto en Git.
- Ningún código de negocio sin Spec + Skill + Gate.
- Despliegue solo **localhost** (ADR-009).
