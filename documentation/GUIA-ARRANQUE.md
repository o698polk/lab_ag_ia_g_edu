# Guía de arranque — SIGA (terminal)

Solo **localhost / 127.0.0.1**. El frontend no es un servidor aparte: FastAPI sirve la API y la UI.

| Pieza | Cómo se levanta |
|---|---|
| MySQL (XAMPP) | Panel XAMPP → Start MySQL |
| Backend + UI | `uvicorn` con el Python del `.venv` |

Credenciales: [`CREDENCIALES-USUARIOS.md`](./CREDENCIALES-USUARIOS.md)

---

## Forma recomendada (Windows)

Doble clic o en PowerShell/CMD:

```bat
cd d:\PROYECTOS\lab_ag_ia_g_edu
.\start-siga.bat
```

Eso usa `.venv\Scripts\python.exe` y **no necesita** `Activate.ps1`.

---

## Si PowerShell bloquea Activate.ps1

Error típico: *la ejecución de scripts está deshabilitada*.

**No uses** `python` del sistema (falla con `No module named 'jwt'`). Usa el Python del venv:

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
$env:APP_ENV = "local"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Opciones alternativas para activar el venv:

```powershell
# Opción A — CMD (no usa ExecutionPolicy de PowerShell)
.\.venv\Scripts\activate.bat

# Opción B — bypass solo para esta sesión
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 0) Parar todo (si algo quedó colgado)

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { if ($_.OwningProcess -gt 0) { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|lab_ag_ia_g_edu' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```

---

## 1) MySQL (XAMPP)

1. Panel XAMPP → **Start** en **MySQL**.
2. Comprobar:

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
.\.venv\Scripts\python.exe scripts\check_mysql.py
```

---

## 2) Backend (API + UI)

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
$env:APP_ENV = "local"

# Primera vez / BD:
.\.venv\Scripts\python.exe scripts\check_env.py
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts\seed_iam.py
.\.venv\Scripts\python.exe scripts\seed_demo_academic.py

# Arranque (deja la ventana abierta) — o usa start-siga.bat
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Debes ver: `Uvicorn running on http://127.0.0.1:8000`

Verificación en **otra** terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health -UseBasicParsing
```

Login API:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/auth/login `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"admin","password":"Admin123!"}' `
  -UseBasicParsing
```

---

## 3) Frontend (UI)

Con el backend arriba:

1. Abre **http://127.0.0.1:8000/ui/**
2. **Ctrl+F5**
3. Entra con `admin` / `Admin123!`

| URL | Uso |
|---|---|
| http://127.0.0.1:8000/ui/ | Aplicación |
| http://127.0.0.1:8000/api/v1/health | Salud API |
| http://127.0.0.1:8000/docs | OpenAPI (si `APP_DEBUG=true`) |

### No hagas esto

- Usar `python` global en lugar de `.\.venv\Scripts\python.exe`.
- Abrir `index.html` desde el disco (`file://`).
- Mezclar `localhost` y `127.0.0.1`.
- Lanzar **dos** `uvicorn` a la vez.

---

## Resumen rápido (día a día)

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
.\start-siga.bat
```

O:

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
$env:APP_ENV = "local"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Navegador: http://127.0.0.1:8000/ui/
