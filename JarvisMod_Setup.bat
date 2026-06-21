@echo off
title JarvisMod Full Automated Setup
echo ===================================================
echo               Installing JarvisMod & Python
echo ===================================================
echo.

:: 1. Check if Python is already installed
python --version >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Python is already installed. Skipping Python installation...
    goto :create_venv
)

:: 2. If Python is missing, download and install it silently
echo [1/4] Python not found. Downloading Python 3.11 Installer...
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

echo [2/4] Installing Python silently (Please wait, this may take a minute)...
:: This runs the installer silently, installs it for all users, and adds it to the system PATH
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Clean up the installer executable
del python_installer.exe

:: Refresh environment variables so the script recognizes the new Python installation immediately
call refresh_env.bat >nul 2>&1
goto :create_venv

:create_venv
echo [3/4] Creating virtual environment...
python -m venv venv

echo [4/4] Activating environment and installing required packages...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===================================================
echo Setup complete! JarvisMod is ready to use.
echo Launch your assistant using 'Run_Jarvis.bat'
echo ===================================================
pause

:: Deletes this setup file automatically so the user's folder stays clean
del "%~f0"
exit