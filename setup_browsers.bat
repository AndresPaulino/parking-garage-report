@echo off
echo ========================================
echo Parking Report Tool - First Time Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Installing Playwright browsers...
echo This is required for the tool to work properly.
echo (This only needs to be done once)
echo.

playwright install chromium

if %errorlevel% neq 0 (
    echo.
    echo If the above failed, try:
    echo   pip install playwright
    echo   playwright install chromium
)

echo.
echo ========================================
echo Setup complete!
echo You can now run:
echo   - run_gui.bat for the graphical interface
echo   - run_cli.bat for command-line mode
echo ========================================
pause
