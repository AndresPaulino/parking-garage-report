# Parking Report Automation - Development Documentation

## Project Overview

Automated Python tool for extracting parking data from Parkonect (https://secure.parkonect.com) for 600+ client accounts. Uses Playwright for browser automation with intelligent batch processing, automatic recovery, and real-time data persistence.

## Current Status

**STABLE & PRODUCTION-READY**

The script successfully processes all accounts with the following proven features:
- ✅ Automatic account discovery from dropdown
- ✅ Batch processing (25 accounts per browser session)
- ✅ Real-time Excel export (incremental, per account)
- ✅ Progress tracking with JSON backup
- ✅ Full resume capability
- ✅ Browser health monitoring and automatic restart
- ✅ Automatic crash recovery
- ✅ Visual progress bar

## File Structure

```
parking-garage-report/
├── enhanced_parking_automation.py   # Main automation script (PRODUCTION)
├── requirements.txt                 # Python dependencies
├── login.txt                        # Credentials (gitignored)
├── claude.md                        # This file - dev documentation
├── README.md                        # User documentation
├── .gitignore                       # Git ignore rules
│
├── [Auto-generated files]
├── parking_reports.xlsx             # Output Excel file
├── automation_progress.json         # Resume progress tracker
├── collected_data.json              # Data backup (JSON)
└── parking_report_errors.log        # Error and info logs
```

## Architecture

### Core Components

#### 1. BrowserHealthMonitor Class

Monitors browser health to prevent crashes from memory leaks or long sessions.

**Restart Triggers:**
- **Time-based**: After 45 minutes (2700 seconds)
- **Operation-based**: After 300 operations
- **Memory-based**: When memory exceeds 1.5GB (requires psutil)

**Methods:**
- `should_restart()`: Checks if browser needs restart
- `increment_operation()`: Increments operation counter
- `reset()`: Resets all counters after browser restart

#### 2. EnhancedParkingAutomation Class

Main automation class handling all operations.

**Key Attributes:**
- `username`, `password`: Parkonect credentials
- `headless`: Boolean for headless browser mode
- `browser`, `page`: Playwright browser and page instances
- `base_url`: "https://secure.parkonect.com"
- `progress_file`: "automation_progress.json"
- `data_backup_file`: "collected_data.json"
- `health_monitor`: BrowserHealthMonitor instance
- `playwright_instance`: Persistent playwright instance

**Key Methods:**

##### Browser Management
- `setup_browser()`: Initializes Playwright browser with anti-detection args
- `login()`: Two-step login process (username → password)
- `navigate_to_reports()`: Direct navigation to Monthly Count Report page
- `ensure_browser_alive()`: Tests browser responsiveness, restarts if dead

##### Data Collection
- `get_account_list()`: Extracts all accounts from dropdown automatically
- `generate_report()`: Generates report for single account/date
- `generate_report_with_recovery()`: Wrapper with retry logic and health checks
- `extract_table_data()`: Parses HTML table data
- `wait_for_report_completion()`: Intelligent wait for table to populate

##### Batch Processing
- `split_accounts_into_batches()`: Splits accounts into batches of 25
- `process_all_reports()`: Main processing loop with batch management
- `save_batch_progress()`: Saves progress after each batch

##### Data Persistence
- `save_account_to_excel()`: Real-time Excel export (incremental, per account)
- `save_data_backup()`: JSON backup of all collected data
- `load_progress()`: Loads resume progress from file
- `save_progress()`: Saves current progress
- `clear_progress()`: Clears progress file after completion

##### Utilities
- `get_date_range()`: Generates list of date tuples for processing
- `export_to_excel()`: Legacy method (not used - replaced by incremental export)
- `send_email_notification()`: Sends completion email

### Data Flow

```
1. Start Script
   ↓
2. Load Progress (if --resume)
   ↓
3. Setup Browser & Login
   ↓
4. Navigate to Reports
   ↓
5. Get Account List (auto-discover from dropdown)
   ↓
6. Split into Batches (25 accounts each)
   ↓
7. For Each Batch:
   │
   ├─→ Restart Browser (except first batch)
   │   ↓
   ├─→ For Each Account in Batch:
   │   │
   │   ├─→ Skip if already completed (resume)
   │   │   ↓
   │   ├─→ For Each Day in Date Range:
   │   │   │
   │   │   ├─→ Check Browser Health
   │   │   │   ↓
   │   │   ├─→ Generate Report (with retry)
   │   │   │   ↓
   │   │   ├─→ Extract Table Data
   │   │   │   ↓
   │   │   └─→ Update Progress Bar
   │   │
   │   ├─→ Save Account to Excel (real-time)
   │   │   ↓
   │   ├─→ Save to JSON Backup
   │   │   ↓
   │   └─→ Update Progress File
   │
   └─→ Save Batch Progress

8. Clear Progress File (95%+ completion)
   ↓
9. Send Email (if configured)
   ↓
10. Complete
```

### Browser Stability Strategy

**Problem:** Browser crashes after ~5 accounts due to memory leaks and session timeouts.

**Solution:** Multi-layered approach

1. **Batch Processing**
   - Process 25 accounts per browser instance
   - Clean browser restart between batches
   - Prevents memory accumulation

2. **Health Monitoring**
   - Proactive restart based on time/operations/memory
   - Prevents crashes before they happen

3. **Automatic Recovery**
   - Detects browser death via `page.evaluate()` test
   - Automatically restarts browser
   - Retries operation up to 3 times
   - Preserves all progress

4. **Real-time Persistence**
   - Excel written after each account
   - JSON backup updated continuously
   - No data loss on crash

## Command Line Interface

### Arguments

```python
--username        # Required: Parkonect username
--password        # Required: Parkonect password
--year            # Optional: Year (default: current)
--month           # Optional: Month 1-12 (default: current)
--start-day       # Optional: Start day (default: 1)
--end-day         # Optional: End day (default: last day of month)
--output          # Optional: Excel filename (default: parking_reports.xlsx)
--headless        # Optional: Run headless (default: False)
--accounts        # Optional: Specific accounts to process (default: all)
--resume          # Optional: Resume from progress file (default: False)
--batch-size      # Optional: Accounts per batch (default: 25)
--email-to        # Optional: Notification recipient
--email-from      # Optional: Notification sender
--email-password  # Optional: Email password
```

### Usage Examples

```bash
# Process all accounts for current month
python enhanced_parking_automation.py --username USER --password PASS

# Process specific month
python enhanced_parking_automation.py --username USER --password PASS --year 2025 --month 10

# Process date range
python enhanced_parking_automation.py --username USER --password PASS --year 2025 --month 10 --start-day 1 --end-day 15

# Resume interrupted process
python enhanced_parking_automation.py --username USER --password PASS --resume

# Headless overnight run
python enhanced_parking_automation.py --username USER --password PASS --headless --email-to admin@company.com --email-from bot@company.com --email-password APP_PASSWORD

# Test with specific accounts
python enhanced_parking_automation.py --username USER --password PASS --accounts "Account 1" "Account 2"
```

## Technical Details

### Playwright Configuration

```python
Browser Args:
- --disable-blink-features=AutomationControlled  # Anti-detection
- --disable-dev-shm-usage                        # Docker compatibility
- --no-sandbox                                    # Linux compatibility
- --disable-gpu                                   # Performance
- --memory-pressure-off                          # Prevent memory throttling
- --disable-background-networking                # Reduce connections

Context:
- viewport: 1920x1080
- user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Login Flow

1. Navigate to `/Admin/Login.aspx`
2. Fill `#txtUserName` with username
3. Click `input[value="Continue"]`
4. Wait for `#txtPassword` to appear
5. Fill `#txtPassword` with password
6. Click `input[value="Log in"]`
7. Wait for navigation to `/Admin/**`

### Report Generation Flow

1. Navigate to `/Admin/Reporting.aspx?gid=1239&rpt=27` (Monthly Count Report)
2. Select account from `#ctl00_cphBody_ddlAccounts`
3. Fill `#ctl00_cphBody_txtStartDate` with MM/DD/YYYY
4. Fill `#ctl00_cphBody_txtEndDate` with MM/DD/YYYY
5. Click `#ctl00_cphBody_btnGenarate` (note: typo in site)
6. Wait for table to populate
7. Extract data from `table` element

### Data Extraction

Table structure:
```
Header Row:   Start Time | End Time | Entries | Exits | Manual Adjustments
Data Rows:    00:00:00   | 01:00:00 | 5       | 3     | 0
...
Totals Row:   TOTALS     | -        | 150     | 148   | 2
```

Extraction logic:
- Skip header row (index 0)
- Skip totals row (last row)
- Extract text from cells, handling both text and `<a>` links
- Return list of dictionaries with keys: `start_time`, `end_time`, `entries`, `exits`, `manual_adjustments`

### Excel Export Format

**Structure:**
- One sheet per account
- Sheet name: Account name (sanitized, max 31 chars)
- Invalid characters replaced: `/\?*[]:`

**Columns:**
1. `date` - MM/DD/YYYY format
2. `start_time` - HH:MM:SS
3. `end_time` - HH:MM:SS
4. `entries` - Integer (formatted as `0`)
5. `exits` - Integer (formatted as `0`)
6. `manual_adjustments` - Integer (formatted as `0`)

**Features:**
- Auto-sized columns
- Integer formatting (no decimals)
- Incremental writing (append mode)
- Replaces sheet if account re-processed

### Progress File Format

`automation_progress.json`:
```json
{
  "completed_accounts": [
    "Account 1",
    "Account 2",
    "..."
  ],
  "last_processed": "2025-10-01T14:30:00.000000",
  "current_batch": 3,
  "total_batches": 24,
  "batch_completed_at": "2025-10-01T14:30:00.000000"
}
```

### Data Backup Format

`collected_data.json`:
```json
{
  "Account 1": [
    {
      "date": "10/01/2025",
      "start_time": "00:00:00",
      "end_time": "01:00:00",
      "entries": "5",
      "exits": "3",
      "manual_adjustments": "0"
    },
    ...
  ],
  "Account 2": [...],
  ...
}
```

## Dependencies

### Required

```
playwright==1.40.0      # Browser automation
pandas==2.1.4           # Data manipulation
openpyxl==3.1.2         # Excel writing
tqdm==4.66.1            # Progress bars
```

### Optional

```
psutil                  # Memory monitoring (improves browser health checks)
python-dotenv==1.0.0    # Environment variables (not currently used)
```

### Development Only

```
pyinstaller==6.3.0      # EXE building (removed from production)
```

## Performance Metrics

### Processing Speed
- **Per operation**: ~2-3 seconds (account + date combination)
- **Per account** (30 days): ~60-90 seconds
- **Per batch** (25 accounts, 30 days): ~25-38 minutes
- **Full run** (600 accounts, 30 days): ~12-18 hours

### Resource Usage
- **Memory**: 200-400MB baseline, peaks to 1-1.5GB before restart
- **CPU**: 5-15% average (browser rendering)
- **Network**: Minimal (~1KB per request)
- **Disk**: ~500KB per 100 accounts (Excel)

### Batch Configuration
- **Default batch size**: 25 accounts
- **Browser restart frequency**: Every batch + health checks
- **Operations between restarts**: ~750 (25 accounts × 30 days)

## Error Handling

### Automatic Recovery

1. **Browser Death**
   - Detected via `page.evaluate()` test
   - Automatic browser restart
   - Re-login and navigate to reports
   - Retry operation (up to 3 times)

2. **Navigation Failures**
   - 3 retry attempts with 2-second delays
   - Extended timeouts (30s for navigation)
   - Fallback error logging

3. **Data Extraction Failures**
   - Logs warning but continues
   - Account marked as incomplete in logs
   - Progress still saved

### Manual Recovery

If script stops completely:
1. Data is already saved (Excel + JSON)
2. Run with `--resume` flag
3. Script loads progress and continues
4. Skips completed batches and accounts

## Testing Strategy

### Quick Test
```bash
# 3 days, visible browser
python enhanced_parking_automation.py \
  --username USER --password PASS \
  --start-day 1 --end-day 3
```

### Single Account Test
```bash
# Test specific account
python enhanced_parking_automation.py \
  --username USER --password PASS \
  --accounts "Test Account" \
  --start-day 1 --end-day 1
```

### Batch Test
```bash
# Test batch processing with small batch size
python enhanced_parking_automation.py \
  --username USER --password PASS \
  --start-day 1 --end-day 3 \
  --batch-size 5
```

### Resume Test
```bash
# Start process
python enhanced_parking_automation.py --username USER --password PASS

# Stop with Ctrl+C after a few accounts

# Resume
python enhanced_parking_automation.py --username USER --password PASS --resume
```

## Known Limitations

1. **Browser Stability**: Playwright connections can still fail after extended use (handled by restarts)
2. **Rate Limiting**: No explicit rate limiting (relies on natural processing delays)
3. **Session Timeout**: Site may have session timeouts (handled by health monitoring)
4. **Parallel Processing**: Not implemented (single-threaded for stability)
5. **Email**: Requires SMTP credentials (Gmail app passwords recommended)

## Future Improvements (Optional)

### Potential Enhancements
- [ ] Parallel processing with multiple browser instances
- [ ] Cloud deployment (AWS Lambda, Google Cloud Functions)
- [ ] Web dashboard for monitoring progress
- [ ] Database storage instead of JSON
- [ ] More sophisticated rate limiting
- [ ] Retry queue for failed accounts
- [ ] Prometheus metrics export

### Not Recommended
- ❌ Selenium migration (Playwright is more stable for long runs)
- ❌ Reducing batch size below 20 (too many restarts = slower)
- ❌ Removing health monitoring (critical for stability)
- ❌ Removing real-time Excel export (data loss risk)

## Troubleshooting Guide

### Common Issues

#### 1. "Target page, context or browser has been closed"
**Cause**: Browser crashed or timed out
**Solution**: Already handled automatically. If script stops, use `--resume`

#### 2. Login Failures
**Cause**: Invalid credentials or site changes
**Solution**:
- Verify credentials in `login.txt`
- Run without `--headless` to observe
- Check if selectors changed

#### 3. No Data Extracted
**Cause**: Table selector changed or data not available
**Solution**:
- Check `parking_report_errors.log`
- Verify account has data for date range
- Inspect page HTML for selector changes

#### 4. Progress File Not Clearing
**Cause**: Less than 95% completion
**Solution**:
- Delete `automation_progress.json` manually to start fresh
- Or let it remain for resume capability

#### 5. Memory Issues
**Cause**: Long runs without psutil
**Solution**:
```bash
pip install psutil
```

## Development Setup

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install browsers
playwright install chromium

# Optional: Install psutil for better monitoring
pip install psutil
```

### Code Style
- Follow PEP 8
- Use type hints where applicable
- Document all public methods
- Keep functions focused and small
- Use async/await consistently

### Logging
- Use `logger.info()` for progress updates
- Use `logger.warning()` for recoverable issues
- Use `logger.error()` for failures
- Log file: `parking_report_errors.log`

## Deployment Recommendations

### Production Deployment

1. **Use headless mode**: `--headless`
2. **Enable email notifications**: `--email-to`, `--email-from`, `--email-password`
3. **Run in background**: Use `nohup`, `screen`, or `tmux`
4. **Monitor logs**: Tail `parking_report_errors.log`
5. **Schedule runs**: Use cron (Linux/Mac) or Task Scheduler (Windows)

### Example Production Run
```bash
nohup python enhanced_parking_automation.py \
  --username "$USERNAME" \
  --password "$PASSWORD" \
  --year 2025 \
  --month 10 \
  --headless \
  --email-to admin@company.com \
  --email-from bot@company.com \
  --email-password "$EMAIL_PASS" \
  > output.log 2>&1 &
```

## Maintenance

### Regular Checks
- Monitor `parking_report_errors.log` for new error patterns
- Verify Excel output quality periodically
- Check if Parkonect site selectors changed
- Update dependencies quarterly: `pip install --upgrade -r requirements.txt`

### When Site Changes
1. Run without `--headless` to observe behavior
2. Use browser DevTools to find new selectors
3. Update selectors in `enhanced_parking_automation.py`
4. Test with small date range first
5. Deploy updated version

## Success Metrics

The script is considered successful when:
- ✅ Processes all accounts without manual intervention
- ✅ Completes within expected timeframe (~12-18 hours for 600 accounts)
- ✅ Zero unrecoverable browser crashes
- ✅ Complete Excel file with all account data
- ✅ Resume capability works when tested
- ✅ No data loss on interruption

## Contact & Support

For issues:
1. Check `parking_report_errors.log`
2. Review this documentation
3. Test with `--headless` disabled to observe
4. Use `--resume` to continue after interruptions

---

**Last Updated**: 2025-11-06
**Version**: 2.0 (Stable Production Release)
**Status**: ✅ Production Ready
