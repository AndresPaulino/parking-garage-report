@echo off
REM Launcher script for Parking Report Automation GUI (Windows)

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv

    echo Installing dependencies...
    .venv\Scripts\pip install -r requirements.txt
    .venv\Scripts\playwright install chromium
)

REM Activate virtual environment and run GUI
echo Starting Parking Report Automation GUI...
call .venv\Scripts\activate.bat
python parking_gui_app.py

pause
