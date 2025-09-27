# save as: simple_build.py
import subprocess
import sys

# Build GUI exe
print("Building GUI executable...")
subprocess.run([
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--windowed', 
    '--name', 'ParkingReportGUI',
    'parking_gui.py'  # Make sure you have a file named parking_gui.py
])

# Build CLI exe  
print("Building CLI executable...")
subprocess.run([
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--console',
    '--name', 'ParkingReportCLI', 
    'parking_report_automation.py'
])

print("Done! Check the 'dist' folder for executables.")