# Parking Report Automation

Automated tool for extracting parking garage reports from Parkonect (https://secure.parkonect.com) for multiple client accounts. Processes 600+ accounts with intelligent batch processing, automatic browser recovery, and real-time data persistence.

## Features

- **Automatic Account Discovery**: Detects all available accounts from the Parkonect dropdown automatically
- **Batch Processing**: Processes accounts in batches of 25 with automatic browser restart for stability
- **Real-time Excel Export**: Writes data to Excel immediately after each account is processed (includes entries, exits, manual adjustments, net movement, and occupancy)
- **Progress Tracking**: Creates JSON backup files to enable resume capability
- **Resume Capability**: Can resume exactly where it left off if interrupted or crashed
- **Multi-Layer Error Recovery**:
  - Top-level exception handler catches all script crashes and retries up to 3 times
  - Per-batch exception handling with automatic retry
  - Per-account exception handling to skip problematic accounts
  - Browser health monitoring with automatic restart and verification
- **Session Management**: Automatic re-login after each batch to prevent session timeouts
- **Resource Cleanup**: Proper cleanup of browser resources prevents memory leaks
- **Failed Account Tracking**: Tracks accounts that fail for later review
- **Progress Bar**: Visual progress indicator with tqdm
- **Email Notifications**: Optional email alerts when processing completes

## Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser (installed automatically via Playwright)

## Installation

### 1. Clone or download the repository

```bash
cd parking-garage-report
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

## Configuration

Create a `login.txt` file with your Parkonect credentials (already exists in the project):

```
username=your_username
password=your_password
```

## Usage

### Basic Usage

Process all accounts for the current month:

```bash
python enhanced_parking_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD
```

### Specific Month and Year

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --year 2025 \
  --month 10
```

### Specific Date Range

Process only specific days within a month:

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --year 2025 \
  --month 10 \
  --start-day 1 \
  --end-day 15
```

### Resume from Interruption

If the script crashes or is stopped, resume from where it left off:

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --resume
```

### Process Specific Accounts Only

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --accounts "Account Name 1" "Account Name 2"
```

### Headless Mode

Run without displaying the browser window (recommended for overnight runs):

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --headless
```

### Custom Output Filename

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --output october_2025_reports.xlsx
```

### Email Notification

Receive an email when processing completes:

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --email-to recipient@email.com \
  --email-from sender@gmail.com \
  --email-password your_app_password
```

### Full Example

```bash
python enhanced_parking_automation.py \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --year 2025 \
  --month 10 \
  --start-day 1 \
  --end-day 31 \
  --output october_reports.xlsx \
  --headless \
  --email-to your@email.com \
  --email-from sender@gmail.com \
  --email-password app_password
```

## Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--username` | Yes | - | Parkonect login username |
| `--password` | Yes | - | Parkonect login password |
| `--year` | No | Current year | Year to process reports for |
| `--month` | No | Current month | Month to process (1-12) |
| `--start-day` | No | 1 | First day of date range |
| `--end-day` | No | Last day of month | Last day of date range |
| `--output` | No | `parking_reports.xlsx` | Output Excel filename |
| `--headless` | No | False | Run browser in headless mode |
| `--accounts` | No | All accounts | Specific account names to process |
| `--resume` | No | False | Resume from last saved progress |
| `--batch-size` | No | 25 | Accounts per batch (browser restart) |
| `--email-to` | No | - | Recipient email for notifications |
| `--email-from` | No | - | Sender email for notifications |
| `--email-password` | No | - | Email password for notifications |

## Output Files

### 1. Excel Report (`parking_reports.xlsx`)

- One sheet per account
- Columns: `date`, `start_time`, `end_time`, `entries`, `exits`, `manual_adjustments`, `net_movement`, `occupancy`
- Numeric values formatted as integers
- Auto-sized columns for readability
- Written in real-time as each account completes

### 2. Progress File (`automation_progress.json`)

- Tracks which accounts have been completed
- Tracks which accounts failed (`failed_accounts` list)
- Tracks batch retry attempts (`batch_retry_count`)
- Tracks current batch number
- Enables resume capability
- Automatically deleted when processing is 95%+ complete

### 3. Data Backup (`collected_data.json`)

- JSON backup of all collected data
- Updated after each account completes
- Can be used to regenerate Excel if needed

### 4. Error Log (`parking_report_errors.log`)

- Detailed logging of all operations
- Error messages and stack traces
- Processing timestamps
- Browser restart events

## How It Works

### 1. Automatic Account Discovery

The script logs into Parkonect and automatically extracts all available accounts from the dropdown menu on the Monthly Count Report page.

### 2. Batch Processing with Session Management

Accounts are split into batches of 25. After each batch:
- Browser is closed and restarted fresh
- **Automatic re-login** to prevent session timeouts
- Prevents memory leaks and connection issues
- Ensures stability for overnight runs

### 3. Multi-Layer Error Recovery

The script has multiple safety nets:

**Top-Level Recovery:**
- Catches any unhandled script crashes
- Automatically retries up to 3 times
- Cleans up browser resources before retry
- Resumes from last saved progress

**Batch-Level Recovery:**
- Catches batch failures
- Restarts browser and retries batch once
- Continues to next batch if retry fails

**Account-Level Recovery:**
- Catches individual account failures
- Tracks failed accounts in progress file
- Recovers browser and continues to next account

**Browser Health Monitoring:**
- Tests browser responsiveness before operations
- Restarts when needed (45 min uptime, 300 operations, or 1.5GB memory)
- Verifies restart succeeded before continuing

### 4. Real-time Data Persistence

After each account is processed:
- Data is immediately written to Excel (one sheet per account)
- Includes all 8 columns: date, start_time, end_time, entries, exits, manual_adjustments, net_movement, occupancy
- JSON backup is updated with all data collected so far
- Progress file is updated with completed account names
- Failed accounts tracked separately

### 5. Resume Capability

If the script stops or crashes:
1. Run with `--resume` flag (or it auto-enables on retry)
2. Loads previous progress from `automation_progress.json`
3. Loads previously collected data from `collected_data.json`
4. Skips completed batches and accounts
5. Continues exactly where it left off
6. Reviews `failed_accounts` list to identify problematic accounts

## Architecture

### Key Classes

**`BrowserHealthMonitor`**
- Monitors browser uptime, operation count, and memory usage
- Determines when browser should be restarted proactively

**`EnhancedParkingAutomation`**
- Main automation class
- Handles login, navigation, data extraction
- Manages batch processing and progress tracking
- Implements automatic recovery mechanisms

### Key Methods

- `get_account_list()`: Auto-discovers accounts from dropdown
- `process_all_reports()`: Main processing loop with batch management
- `generate_report_with_recovery()`: Generates report with automatic retry
- `save_account_to_excel()`: Real-time Excel export per account
- `ensure_browser_alive()`: Detects and recovers from browser crashes
- `split_accounts_into_batches()`: Divides accounts into manageable batches

## Troubleshooting

### Script Crashes After Processing Several Accounts

This is handled automatically! The script:
- Restarts the browser every 25 accounts
- Monitors browser health proactively
- Automatically recovers from browser crashes
- Saves progress continuously

Just run with `--resume` to continue.

### Login Fails

- Verify credentials in `login.txt` or command line
- Check if Parkonect site is accessible
- Run without `--headless` to see what's happening
- Check `parking_report_errors.log` for details

### Progress Bar Not Moving

- Check `parking_report_errors.log` for errors
- Verify you have access to the accounts
- Run without `--headless` to observe browser behavior

### Excel File Not Generated

- Check file permissions in the directory
- Verify `openpyxl` is installed: `pip install openpyxl`
- Check `parking_report_errors.log` for write errors

### Script Stops Responding

- Press Ctrl+C to stop gracefully
- Run again with `--resume` to continue
- Consider running in smaller date ranges

### Memory Issues

Install `psutil` for better memory monitoring:

```bash
pip install psutil
```

## Performance

- **Processing Speed**: ~2-3 seconds per account per day
- **Batch Size**: 25 accounts per browser session (configurable)
- **Browser Restart**: Every 45 minutes or 300 operations
- **Expected Runtime**:
  - 100 accounts × 30 days = ~2-3 hours
  - 600 accounts × 30 days = ~12-18 hours

## Best Practices

### For Overnight Runs

1. Use `--headless` mode
2. Run in a `screen` or `tmux` session (Linux/Mac) or keep terminal open (Windows)
3. Use `--resume` if you need to restart
4. Consider using `--email-to` for completion notifications

Example:

```bash
# Run in background with headless mode
nohup python enhanced_parking_automation.py \
  --username USER \
  --password PASS \
  --year 2025 \
  --month 10 \
  --headless \
  --email-to your@email.com \
  --email-from sender@gmail.com \
  --email-password app_pass \
  > output.log 2>&1 &
```

### For Testing

1. Test with a small date range first:
   ```bash
   python enhanced_parking_automation.py \
     --username USER --password PASS \
     --start-day 1 --end-day 3
   ```

2. Test with specific accounts:
   ```bash
   python enhanced_parking_automation.py \
     --username USER --password PASS \
     --accounts "Test Account"
   ```

3. Monitor the browser (without headless) to see what's happening

## Project Structure

```
parking-garage-report/
├── enhanced_parking_automation.py   # Main script
├── requirements.txt                 # Python dependencies
├── login.txt                        # Credentials (gitignored)
├── claude.md                        # Development documentation
├── README.md                        # This file
├── parking_reports.xlsx             # Output (auto-generated)
├── automation_progress.json         # Progress tracking (auto-generated)
├── collected_data.json              # Data backup (auto-generated)
└── parking_report_errors.log        # Error log (auto-generated)
```

## Security Notes

- Never commit `login.txt` to version control
- Use environment variables for credentials in production
- Consider using app-specific passwords for email notifications
- The `.gitignore` file already excludes sensitive files

## License

This project is for internal use only.

## Support

For issues or questions:
1. Check `parking_report_errors.log` for detailed error messages
2. Review this README for usage examples
3. Check `claude.md` for development documentation
