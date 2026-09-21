@echo off
REM Arranque SIGA — no requiere Activate.ps1 (evita ExecutionPolicy)
cd /d "%~dp0"
set APP_ENV=local
set PYTHONPATH=%~dp0app\backend

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: no existe .venv. Crea el entorno e instala dependencias.
  echo   python -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -r app\backend\requirements.txt
  exit /b 1
)

echo MySQL XAMPP debe estar en marcha.
echo UI: http://127.0.0.1:8000/ui/
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
