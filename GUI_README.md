# Parking Report Automation - GUI User Guide

## Overview

The Parking Report Automation GUI provides a user-friendly desktop interface for running parking reports. No command-line knowledge required!

## Quick Start

### macOS/Linux

1. Double-click `run_gui.sh` or run in terminal:
   ```bash
   ./run_gui.sh
   ```

### Windows

1. Double-click `run_gui.bat`

The first time you run the GUI, it will:
- Create a virtual environment
- Install all required dependencies
- Install the Chromium browser for automation

This may take a few minutes. Subsequent launches will be much faster.

## Using the GUI

### 1. Login Credentials

Enter your Parkonect username and password in the first section.

**Remember Credentials**: Check this box to securely save your login information (encrypted) for future use. Your credentials are stored locally on your computer using industry-standard encryption.

### 2. Garage Selection

Select the garage you want to process from the dropdown menu.

*Note: Currently only one garage is configured. Additional garages can be added later.*

### 3. Date Range

Configure the date range for the reports:

- **Year**: The year to process (2020 - current year + 1)
- **Month**: The month to process (1-12)
- **Start Day**: First day of the date range
- **End Day**: Last day of the date range (automatically adjusted for month length)

The script will generate reports for each day in this range.

### 4. Options

- **Output File**: The Excel file where results will be saved. Click "Browse..." to choose a location.
- **Batch Size**: Number of accounts to process before restarting the browser (default: 25). Lower values are more stable but slower.
- **Run in headless mode**: When checked, the browser runs in the background without showing a window. Recommended for overnight runs.
- **Resume from previous run**: Continue from where you left off if a previous run was interrupted.

### 5. Email Notifications (Optional)

Check "Enable email notifications" to receive an email when processing completes.

You'll need to provide:
- **To**: Recipient email address
- **From**: Sender email address (Gmail recommended)
- **Password**: Email password or app-specific password

*For Gmail users: You'll need to create an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.*

### 6. Advanced Options

**Specific Accounts**: If you only want to process specific accounts, enter their names here (one per line). Leave empty to process all accounts.

Example:
```
4141 - CSLL
5200 - Downtown Parking
6300 - Airport Garage
```

### 7. Save Preferences

Check "Save preferences for next time" to save your current settings (except passwords unless "Remember credentials" is also checked).

### 8. Start Processing

Click **"Start Processing"** to begin. The progress section will show:

- Current status (e.g., "Running automation...")
- Real-time log output from the automation script
- Any errors or warnings that occur

**Stop**: Click this button to stop the processing at any time. The script will finish the current account and then stop gracefully.

**Clear Log**: Clear the log viewer.

## Output Files

### Excel Report

The main output file (default: `parking_reports.xlsx`) contains:

- **One sheet per account**
- **8 columns**: date, start_time, end_time, entries, exits, manual_adjustments, net_movement, occupancy
- Real-time updates as each account is processed

### Progress Files

The script creates temporary files to track progress:

- `automation_progress.json`: Resume information
- `collected_data.json`: Backup of all collected data
- `parking_report_errors.log`: Detailed error log

These files are automatically managed by the script.

## Tips for Best Results

### For Overnight Runs

1. Check "Run in headless mode"
2. Check "Save preferences for next time"
3. Set a specific output filename with date (e.g., `reports_november_2025.xlsx`)
4. Enable email notifications to know when it's done
5. Keep your computer running and connected to the internet

### If the Script Stops

1. Check the log viewer for error messages
2. Note the last account that was processed
3. Check "Resume from previous run"
4. Click "Start Processing" again

The script will automatically continue from where it left off.

### For Testing

1. Use a small date range (e.g., 1-3 days)
2. Uncheck "Run in headless mode" to see what's happening
3. Monitor the log viewer for any issues

## Troubleshooting

### "Invalid Input" Errors

- Verify username and password are correct
- Check that date range is valid for the selected month
- Ensure garage is selected

### Script Won't Start

- Check `parking_report_errors.log` for details
- Ensure internet connection is active
- Verify Parkonect website is accessible

### Browser Keeps Crashing

- Try lowering the batch size (e.g., 15 instead of 25)
- Close other applications to free up memory
- Ensure sufficient disk space is available

### Progress Seems Stuck

- The script may be waiting for a slow page load
- Check the log viewer for activity
- Processing time: ~2-3 seconds per account per day is normal

## Security

### Credential Storage

When you check "Remember credentials", your username and password are:

1. Encrypted using the `cryptography` library (Fernet symmetric encryption)
2. Stored locally in `preferences.json`
3. Decrypted only when needed by the GUI
4. Never sent anywhere except to the Parkonect website during login

The encryption key is stored in a hidden file (`.key`) in the same directory. Keep both files secure.

### Clearing Saved Credentials

To clear saved credentials:

1. Uncheck "Remember credentials"
2. Check "Save preferences for next time"
3. Click "Start Processing" (or just save preferences)

Or manually delete `preferences.json`.

## Advanced: Adding New Garages

To add additional garages, you'll need to edit `gui_utils.py` and update the `get_garage_list()` method with the new garage information:

```python
return {
    "Garage 1 (Default)": {
        "gid": "1239",
        "rpt": "27",
        "url": "https://secure.parkonect.com"
    },
    "Garage 2 - New Location": {
        "gid": "YOUR_GID",
        "rpt": "YOUR_RPT",
        "url": "YOUR_URL"
    }
}
```

*This functionality will be made easier in a future update.*

## Performance Expectations

- **Processing Speed**: ~2-3 seconds per account per day
- **Expected Runtime**:
  - 100 accounts × 30 days = 2-3 hours
  - 600 accounts × 30 days = 12-18 hours
- **Browser Restart**: Automatically every 25 accounts (configurable)

## Support

For issues:

1. Check the log viewer in the GUI
2. Review `parking_report_errors.log` for detailed errors
3. See main [README.md](README.md) for script documentation
4. Check [claude.md](claude.md) for technical details

## Version Information

- GUI Version: 1.0
- Script Version: Enhanced with multi-layer error recovery
- Python: 3.8 or higher required
- Playwright: 1.40.0
