@echo off
if not exist "venv" (
    echo [ERROR] JarvisMod is not installed yet! 
    echo Please run JarvisMod_Setup.bat first.
    pause
    exit
)
start "" "venv\Scripts\pythonw.exe" gui.py
exit