@echo off
REM Parking Report Tool - CLI Version
REM Edit these values with your credentials

SET USERNAME=your_username_here
SET PASSWORD=your_password_here
SET YEAR=2025
SET MONTH=9

echo Running Parking Report CLI...
cd /d "%~dp0"

if exist "dist\ParkingReportCLI.exe" (
    dist\ParkingReportCLI.exe --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
) else if exist "ParkingReportCLI.exe" (
    ParkingReportCLI.exe --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
) else (
    python enhanced_parking_automation.py --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
)

pause
