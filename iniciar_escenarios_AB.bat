@echo off
REM Inicia Escenario A (puerto 5001) y Escenario B (puerto 5002) en ventanas separadas.
REM Requiere MySQL (XAMPP) encendido: DATABASE_URL en escenario*/App/.env.
REM La API key de DeepSeek se carga luego desde la UI (admin > configuracion IA).
REM Nota: sin bloques con parentesis porque la ruta del proyecto contiene ")".
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%lab_venv"
if exist "%VENV%\Scripts\python.exe" goto RUN
echo Creando entorno virtual lab_venv e instalando dependencias...
python -m venv "%VENV%"
if errorlevel 1 goto ERR
"%VENV%\Scripts\python.exe" -m pip install -q -r "%ROOT%escenarioA\App\backend\requirements.txt"
if errorlevel 1 goto ERR
:RUN
start "Escenario A :5001 relajado" cmd /k "cd /d "%ROOT%escenarioA\App\backend" && set PORT=5001&& set PYTHONIOENCODING=utf-8&& "%VENV%\Scripts\python.exe" run.py"
start "Escenario B :5002 endurecido" cmd /k "cd /d "%ROOT%escenarioB\App\backend" && set PORT=5002&& set PYTHONIOENCODING=utf-8&& "%VENV%\Scripts\python.exe" run.py"
echo Escenario A: http://127.0.0.1:5001
echo Escenario B: http://127.0.0.1:5002
echo Inicie sesion como admin y configure la API key de DeepSeek en cada escenario.
goto END
:ERR
echo ERROR preparando el entorno (python/pip).
pause
:END
endlocal
