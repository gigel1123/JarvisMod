@echo off
title JarvisMod Full Automated Setup
cd /d "%~dp0"
echo ===================================================
echo               Installing JarvisMod & Python
echo ===================================================
echo.

:: 1. Check if Python is already there
python --version >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Python is already installed.
    set "PY_CMD=python"
    goto :create_venv
)

:: 2. Download and install Python silently if missing
echo [1/3] Python not found.
echo Downloading Python 3.12...
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe

echo [2/3] Installing Python silently... (This takes about a minute)
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
del python_installer.exe

:: Try to find the freshly installed python 3.12 executable manually
if exist "C:\Program Files\Python312\python.exe" (
    set "PY_CMD=C:\Program Files\Python312\python.exe"
) else if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
) else (
    set "PY_CMD=python"
)

:create_venv
echo [3/3] Setting up local virtual environment and dependencies...
:: Create the environment using our detected python path
"%PY_CMD%" -m venv .venv

if not exist ".venv" (
    echo [ERROR] Failed to create virtual environment. Try running this file as Administrator.
    pause
    exit
)

:: Activate and install requirements
call .venv\Scripts\activate
python -m pip install --upgrade pip
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found.
    echo Skipping dependency installation.
)

echo.
echo ===================================================
echo Setup complete! JarvisMod is ready to go.
echo Use 'Run_Jarvis.bat' to start the application.
echo ===================================================
pause
exit