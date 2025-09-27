"""
Build Script for Parking Report Tool
Handles Playwright browser installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile

def create_launcher_script():
    """Create a launcher script that checks for Playwright browsers"""
    launcher_content = '''
import os
import sys
import subprocess
from pathlib import Path

def check_and_install_playwright():
    """Check if Playwright browsers are installed, install if needed"""
    try:
        # Check if browsers exist
        home = Path.home()
        playwright_path = home / '.cache' / 'ms-playwright'
        
        if not playwright_path.exists():
            print("First-time setup: Installing browser components...")
            print("This may take a few minutes...")
            
            # Install playwright browsers
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                          check=True, capture_output=True)
            print("Browser components installed successfully!")
            
    except Exception as e:
        print(f"Note: Browser setup may be needed: {e}")
        print("You may need to run: playwright install chromium")

# Check browsers before importing main app
check_and_install_playwright()

# Now import and run the actual GUI
from parking_gui_standalone import main
main()
'''
    
    with open('launcher.py', 'w') as f:
        f.write(launcher_content)
    
    print("Created launcher.py")

def build_gui_exe():
    """Build the GUI executable"""
    
    print("\n" + "="*50)
    print("Building Parking Report Tool GUI")
    print("="*50 + "\n")
    
    # Create launcher script
    create_launcher_script()
    
    # Build command for GUI (using launcher)
    gui_command = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'ParkingReportGUI',
        '--onefile',
        '--windowed',
        '--clean',
        '--add-data', f'parking_gui_standalone.py{os.pathsep}.',
        '--add-data', f'enhanced_parking_automation.py{os.pathsep}.',
        '--hidden-import', 'tkinter',
        '--hidden-import', 'subprocess',
        '--hidden-import', 'threading',
        'launcher.py'
    ]
    
    try:
        print("Building GUI executable...")
        subprocess.run(gui_command, check=True)
        print("✓ GUI executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ GUI build failed: {e}")
        return False

def build_cli_exe():
    """Build the CLI executable with embedded Playwright"""
    
    print("\n" + "="*50)
    print("Building CLI Tool")
    print("="*50 + "\n")
    
    cli_command = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'ParkingReportCLI',
        '--onefile',
        '--console',
        '--clean',
        '--hidden-import', 'playwright',
        '--hidden-import', 'pandas',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'tqdm',
        '--hidden-import', 'asyncio',
        'enhanced_parking_automation.py'
    ]
    
    try:
        print("Building CLI executable...")
        subprocess.run(cli_command, check=True)
        print("✓ CLI executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ CLI build failed: {e}")
        return False

def create_batch_files():
    """Create helper batch files"""
    
    # Simple GUI launcher
    gui_bat = """@echo off
echo Starting Parking Report Tool...
cd /d "%~dp0"
if exist "dist\\ParkingReportGUI.exe" (
    dist\\ParkingReportGUI.exe
) else if exist "ParkingReportGUI.exe" (
    ParkingReportGUI.exe
) else (
    echo Error: ParkingReportGUI.exe not found
    echo Please run build_exe.py first
    pause
)
"""
    
    with open('run_gui.bat', 'w') as f:
        f.write(gui_bat)
    
    # CLI launcher with parameters
    cli_bat = """@echo off
REM Parking Report Tool - CLI Version
REM Edit these values with your credentials

SET USERNAME=your_username_here
SET PASSWORD=your_password_here
SET YEAR=2025
SET MONTH=9

echo Running Parking Report CLI...
cd /d "%~dp0"

if exist "dist\\ParkingReportCLI.exe" (
    dist\\ParkingReportCLI.exe --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
) else if exist "ParkingReportCLI.exe" (
    ParkingReportCLI.exe --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
) else (
    python enhanced_parking_automation.py --username %USERNAME% --password %PASSWORD% --year %YEAR% --month %MONTH% --headless
)

pause
"""
    
    with open('run_cli.bat', 'w') as f:
        f.write(cli_bat)
    
    # Development launcher (uses Python directly)
    dev_bat = """@echo off
echo Starting Parking Report Tool (Development Mode)...
python parking_gui_standalone.py
pause
"""
    
    with open('run_dev.bat', 'w') as f:
        f.write(dev_bat)
    
    print("Created batch files:")
    print("  - run_gui.bat (runs the GUI exe)")
    print("  - run_cli.bat (runs the CLI exe)")
    print("  - run_dev.bat (runs GUI with Python)")

def create_installer_script():
    """Create an installer that sets up Playwright"""
    
    installer_content = '''@echo off
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
'''
    
    with open('setup_browsers.bat', 'w') as f:
        f.write(installer_content)
    
    print("Created setup_browsers.bat")

def create_readme():
    """Create a simple readme for the distribution"""
    
    readme = """
PARKING REPORT TOOL - Quick Start Guide
========================================

FIRST TIME SETUP:
1. Run 'setup_browsers.bat' (only needed once)
2. This installs required browser components

TO RUN THE TOOL:
- Double-click 'run_gui.bat' for the graphical interface
- OR edit 'run_cli.bat' with your credentials for command-line mode

TROUBLESHOOTING:
- If you get a browser error, run 'setup_browsers.bat'
- If the exe doesn't work, install Python and use 'run_dev.bat'

FILES:
- ParkingReportGUI.exe - Main application
- ParkingReportCLI.exe - Command-line version  
- run_gui.bat - Launch GUI
- run_cli.bat - Launch CLI (edit with credentials)
- setup_browsers.bat - Install browser components

REQUIREMENTS:
- Windows 10 or later
- Internet connection for first-time setup
"""
    
    with open('README.txt', 'w') as f:
        f.write(readme)
    
    print("Created README.txt")

def main():
    """Main build process"""
    
    print("\n" + "="*60)
    print("  PARKING REPORT TOOL - BUILD SCRIPT")
    print("="*60)
    
    # Check for required files
    required_files = [
        'enhanced_parking_automation.py',
        'parking_gui_standalone.py'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print("\n❌ ERROR: Missing required files:")
        for f in missing:
            print(f"   - {f}")
        print("\nPlease ensure all files are in the current directory.")
        input("\nPress Enter to exit...")
        return
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    print("\nWhat would you like to build?")
    print("1. GUI only")
    print("2. CLI only")
    print("3. Both GUI and CLI")
    print("4. Just create batch files")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    success = True
    
    if choice in ['1', '3']:
        success = build_gui_exe() and success
    
    if choice in ['2', '3']:
        success = build_cli_exe() and success
    
    # Always create batch files and readme
    create_batch_files()
    create_installer_script()
    create_readme()
    
    if success and choice != '4':
        print("\n" + "="*60)
        print("  BUILD COMPLETE!")
        print("="*60)
        print("\nExecutables are in the 'dist' folder")
        print("\nFor distribution, include these files:")
        print("  - dist/ParkingReportGUI.exe")
        print("  - dist/ParkingReportCLI.exe")
        print("  - run_gui.bat")
        print("  - run_cli.bat")
        print("  - setup_browsers.bat")
        print("  - README.txt")
        print("\nYour friend should:")
        print("  1. Run setup_browsers.bat once")
        print("  2. Then use run_gui.bat to start the tool")
    
    # Clean up temporary files
    if os.path.exists('launcher.py'):
        os.remove('launcher.py')
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()