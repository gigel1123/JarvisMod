@echo off
setlocal enabledelayedexpansion
title JarvisMod Environment Setup

echo ===================================================
echo             JarvisMod Environment Setup            
echo ===================================================
echo.

:: Step 1: Check for Python 3.12
echo [*] Checking for Python 3.12...
py -3.12 -c "import sys; print('Found Python ' + sys.version.split()[0])" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.12
    goto create_venv
)

python -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto create_venv
)

:: Step 1b: Python missing -> Auto-install via winget
echo [!] Python 3.12 is required but was not found.
echo [*] Attempting to automatically install Python 3.12 via winget...

where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Error: Windows Package Manager (winget) is missing.
    echo     Please install Python 3.12 manually from python.org
    pause
    exit /b 1
)

echo [*] Installing Python 3.12. Please grant admin permissions if prompted...
winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo [!] Automatic installation failed.
    echo     Please download and install Python 3.12 manually.
    pause
    exit /b 1
)

echo [+] Python 3.12 installed successfully!
echo [*] Refreshing environment paths...

:: Refresh PATH without restarting the command prompt
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "SYS_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path') do set "USER_PATH=%%B"
set "PATH=%USER_PATH%;%SYS_PATH%"

:: Re-verify after install
py -3.12 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.12
    goto create_venv
)

python -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto create_venv
)

:: Fallback if paths are still stubborn in the current window
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe"
    goto create_venv
)

echo [!] Python was installed but the script cannot see it yet.
echo     Please close this window and run JarvisMod_Setup.bat again.
pause
exit /b 1

:create_venv
:: Step 2: Create Virtual Environment
echo [*] Using target: !PYTHON_CMD! [cite: 4]
if not exist .venv ( 
    echo [*] Creating virtual environment (.venv)... 
    !PYTHON_CMD! -m venv .venv 
    if %errorlevel% neq 0 ( 
        echo [!] Failed to create virtual environment. 
        pause 
        exit /b 1 
    ) 
    echo [^+] Virtual environment created successfully. 
) else ( 
    echo [*] Existing virtual environment (.venv) detected. Skipping creation. 
) 

:: Step 3: Activate venv and install dependencies
echo [*] Activating virtual environment... 
call .venv\Scripts\activate.bat 
if %errorlevel% neq 0 ( [cite: 5, 6]
    echo [!] Failed to activate virtual environment. 
    pause 
    exit /b 1 
) 

echo [*] Upgrading pip... 
python -m pip install --upgrade pip 

:: Step 4: Install requirements
if exist requirements.txt ( 
    echo [*] Installing requirements from requirements.txt... 
    pip install -r requirements.txt 
    if %errorlevel% neq 0 ( 
        echo [!] Error occurred during dependency installation. 
        pause 
        exit /b 1 
    ) 
    echo [^+] All dependencies installed successfully. [cite: 7]
) else ( [cite: 7]
    echo [!] Warning: requirements.txt not found. Skipping dependency installation. [cite: 7]
) [cite: 7]

echo. [cite: 7]
echo =================================================== [cite: 8]
echo     Setup Complete! You can now run JarvisMod.     [cite: 8]
echo =================================================== [cite: 8]
echo. [cite: 8]
pause [cite: 8]