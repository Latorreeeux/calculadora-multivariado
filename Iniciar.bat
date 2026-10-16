@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Preparando entorno de Python...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -c "import scipy" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :error
exit /b 0
:error
echo.
echo No se pudo iniciar. Revisa el mensaje anterior. Se necesita Python 3.10 o superior.
pause
exit /b 1
