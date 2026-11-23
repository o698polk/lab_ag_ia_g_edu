@echo off
REM Ejecuta CP-01..CP-04 (A vs B, sin LLM) y genera RESULTADOS_CP.md
REM Sin bloques con parentesis: la ruta del proyecto contiene ")".
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%lab_venv"
if exist "%VENV%\Scripts\python.exe" goto RUN
python -m venv "%VENV%"
if errorlevel 1 goto ERR
"%VENV%\Scripts\python.exe" -m pip install -q -r "%ROOT%escenarioA\App\backend\requirements.txt"
if errorlevel 1 goto ERR
:RUN
"%VENV%\Scripts\python.exe" "%ROOT%documentacion_investigacion\COMPLETAR\protocolo_cp_demostrativo.py" --db-backend auto --md "%ROOT%RESULTADOS_CP.md"
set RC=%ERRORLEVEL%
echo Informe: %ROOT%RESULTADOS_CP.md  codigo=%RC%
goto END
:ERR
echo ERROR preparando el entorno (python/pip).
set RC=1
:END
if not "%1"=="nopause" pause
endlocal & exit /b %RC%
