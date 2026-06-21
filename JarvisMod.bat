@echo off
:: Force the script to run from its own folder path
cd /d "%~dp0"

:: Check if the virtual environment exists
if not exist ".venv" (
    echo [ERROR] JarvisMod is not installed yet! 
    echo Please run JarvisMod_Setup.bat first.
    pause
    exit
)

:: Run using the absolute path of the local directory hiding the console
:: call .venv\Scripts\activate
::echo Please close the terminal window

:: 'start' tells the terminal to launch pythonw and immediately run the next line (exit)
start "" pythonw gui.py
exit