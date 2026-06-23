@echo off
ollama pull llama3
exit
cd /d "%~dp0"

if not exist ".venv" (
    echo [ERROR] JarvisMod is not installed yet! Please run JarvisMod_Setup.bat first.
    pause
    exit
)

:: Launch pythonw in a completely detached process and instantly exit the terminal
start "" ".venv\Scripts\pythonw.exe" src\gui.py
exit