# Parking Report Automation Setup Guide

## Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser

## Installation

1. **Clone/Download the script files:**
   - `parking_report_automation.py` (main script)
   - `requirements.txt` (dependencies)

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Configuration

### Update the script with your specific selectors:

Before running, you need to update these items in `parking_report_automation.py`:

1. **Base URL** (line ~35):
   ```python
   self.base_url = "https://your-actual-site.com"
   ```

2. **Login selectors** (lines ~60-65):
   - Update the username input selector
   - Update the password input selector
   - Update the login button selector
   - Update the post-login element selector

3. **Report page URL** (line ~85):
   ```python
   await self.page.goto(f"{self.base_url}/reports/monthly-count")
   ```

4. **Form selectors** (various lines):
   - Garage dropdown: `select#garage`
   - Account dropdown: `select#account`
   - Start date input: `input#start-date`
   - End date input: `input#end-date`
   - Generate report button: `button#generate-report`
   - Report table: `table`

## Usage

### Basic usage (current month):
```bash
python parking_report_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD
```

### Specific month:
```bash
python parking_report_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD --year 2025 --month 9
```

### Process specific accounts only:
```bash
python parking_report_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD --accounts "Account1" "Account2"
```

### Run in headless mode (no browser window):
```bash
python parking_report_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD --headless
```

### Custom output filename:
```bash
python parking_report_automation.py --username YOUR_USERNAME --password YOUR_PASSWORD --output september_reports.xlsx
```

# Process just 3 days (1st to 3rd)
python enhanced_parking_automation.py --username USER --password PASS --year 2025 --month 9 --start-day 1 --end-day 3

# Process ALL accounts with progress bar
python enhanced_parking_automation.py --username USER --password PASS

# Resume if interrupted
python enhanced_parking_automation.py --username USER --password PASS --resume

# With email notification
python enhanced_parking_automation.py --username USER --password PASS --email-to recipient@email.com --email-from sender@gmail.com --email-password app-password

### Full example with all options:
```bash
python parking_report_automation.py \
    --username YOUR_USERNAME \
    --password YOUR_PASSWORD \
    --year 2025 \
    --month 9 \
    --output parking_sept_2025.xlsx \
    --headless \
    --accounts "Company ABC" "Company XYZ"
```

## Using Environment Variables (Recommended for Security)

Create a `.env` file:
```
PARKING_USERNAME=your_username
PARKING_PASSWORD=your_password
```

Then create a wrapper script `run_reports.py`:
```python
import os
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()

username = os.getenv('PARKING_USERNAME')
password = os.getenv('PARKING_PASSWORD')

# Pass along any additional command line arguments
additional_args = sys.argv[1:]

cmd = [
    'python', 'parking_report_automation.py',
    '--username', username,
    '--password', password
] + additional_args

subprocess.run(cmd)
```

Then run:
```bash
python run_reports.py --year 2025 --month 9
```

## Output

The script generates:
1. **Excel file** (`parking_reports.xlsx` by default) with:
   - One sheet per account
   - Each sheet contains all days of the month
   - Columns: Date, Start Time, End Time, Entries, Exits, Manual Adjustments

2. **Log file** (`parking_report_errors.log`) containing:
   - Processing progress
   - Any errors encountered
   - Accounts/dates that failed

## Troubleshooting

### Common Issues:

1. **Login fails:**
   - Verify credentials
   - Check login selectors match your site
   - Try running without `--headless` to see what's happening

2. **No data extracted:**
   - Verify table selectors
   - Increase wait time after clicking "Generate Report"
   - Check if the site structure has changed

3. **Rate limiting:**
   - Increase delays between requests in the script
   - Process fewer accounts at a time

4. **Selector not found errors:**
   - Use browser developer tools to find correct selectors
   - Update selectors in the script

### Debugging Tips:

1. **Run without headless mode** to see the browser:
   ```bash
   python parking_report_automation.py --username USER --password PASS
   ```

2. **Check the error log** for specific issues:
   ```bash
   tail -f parking_report_errors.log
   ```

3. **Test with a single account first:**
   ```bash
   python parking_report_automation.py --username USER --password PASS --accounts "Test Account"
   ```

## Customization

### To add rate limiting:
In `process_all_reports()` method, increase the delay:
```python
await asyncio.sleep(3)  # Increase from 1 to 3 seconds
```

### To change which columns are extracted:
Modify the `extract_table_data()` method to include/exclude columns as needed.

### To change the date format:
Modify the `get_date_range()` method's strftime format.

## Next Steps

After initial setup and testing:

1. **Get the HTML selectors** from your site using browser developer tools
2. **Update all selectors** in the script
3. **Test with one account** for one day first
4. **Gradually increase** to full month and all accounts
5. **Monitor for any rate limiting** or blocking
6. **Schedule regular runs** using cron (Linux/Mac) or Task Scheduler (Windows) if needed