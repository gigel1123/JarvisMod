@echo off
title JarvisMod First-Time Setup
echo ===================================================
echo               Installing JarvisMod
echo ===================================================
echo.
echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Activating environment and installing requirements...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Finalizing setup...
echo.
echo Setup complete! JarvisMod is ready to use.
echo This setup file will now close and clean up.
pause

:: Deletes this setup file automatically so the user doesn't click it again
del "%~f0"
exit