#!/bin/bash
# Launcher script for Parking Report Automation GUI

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv

    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
    .venv/bin/playwright install chromium
fi

# Activate virtual environment and run GUI
echo "Starting Parking Report Automation GUI..."
source .venv/bin/activate
python parking_gui_app.py
