@echo off
echo Installing Parking Report Tool...
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed! Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

echo.
echo Installing Playwright browsers...
playwright install chromium

echo.
echo ========================================
echo Installation complete!
echo.
echo To run the GUI version: python parking_gui.py
echo To run the CLI version: python enhanced_parking_automation.py --help
echo ========================================
pause
