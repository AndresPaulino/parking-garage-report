# Parking Report Automation - Claude Code Instructions

## Project Context
You are working on a parking report automation tool that extracts data from Parkonect (https://secure.parkonect.com) for 600+ client accounts. The tool uses Playwright for browser automation and exports data to Excel.

## Critical Current Issue
The browser connection dies after processing ~5 accounts with error: "Target page, context or browser has been closed". This prevents overnight runs needed to process all 600+ accounts.

## File Structure
```
project/
├── enhanced_parking_automation.py  # Main automation script
├── parking_gui_standalone.py      # GUI interface
├── requirements.txt               # Dependencies
├── parking_report_errors.log     # Error log
└── automation_progress.json      # Resume progress file
```

## Primary Task: Fix Browser Stability

### Root Cause
The Playwright browser instance crashes after processing multiple accounts, likely due to:
- Memory accumulation over 15,870 operations
- No browser restart mechanism
- Session timeout or connection limits

### Required Solution
Implement browser lifecycle management:

```python
# Add to EnhancedParkingAutomation class
async def ensure_browser_alive(self):
    """Check if browser is alive and restart if needed"""
    try:
        # Test if browser is responsive
        await self.page.evaluate('() => true')
        return True
    except:
        logger.info("Browser died, restarting...")
        await self.setup_browser()
        await self.login()
        await self.navigate_to_reports()
        return True

async def process_with_browser_management(self, accounts, date_pairs):
    """Process accounts with periodic browser restart"""
    ACCOUNTS_PER_BROWSER = 25  # Restart every 25 accounts
    
    for i, (account_value, account_name) in enumerate(accounts):
        # Restart browser periodically
        if i > 0 and i % ACCOUNTS_PER_BROWSER == 0:
            logger.info(f"Restarting browser after {i} accounts...")
            await self.browser.close()
            await self.setup_browser()
            await self.login()
            await self.navigate_to_reports()
        
        # Process account...
```

## Secondary Tasks

### 1. Add Connection Recovery
```python
async def generate_report_with_recovery(self, account_value, account_name, start_date, end_date):
    """Generate report with automatic recovery on browser failure"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check browser health
            await self.ensure_browser_alive()
            
            # Generate report
            return await self.generate_report(account_value, account_name, start_date, end_date)
            
        except Exception as e:
            if "closed" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Browser died, attempting recovery (attempt {attempt + 1})")
                await self.setup_browser()
                await self.login() 
                await self.navigate_to_reports()
            else:
                raise
```

### 2. Implement Batch Processing
```python
def split_accounts_into_batches(accounts, batch_size=50):
    """Split accounts into manageable batches"""
    for i in range(0, len(accounts), batch_size):
        yield accounts[i:i + batch_size]

async def process_in_batches(self, accounts, date_pairs):
    """Process accounts in batches with fresh browser each time"""
    batches = list(split_accounts_into_batches(accounts, 50))
    
    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"Processing batch {batch_num} of {len(batches)}")
        
        # Fresh browser for each batch
        await self.setup_browser()
        await self.login()
        await self.navigate_to_reports()
        
        # Process batch
        for account in batch:
            # Process account...
        
        # Close browser after batch
        await self.browser.close()
        
        # Save progress after each batch
        self.save_batch_progress(batch_num)
```

### 3. Add Health Monitoring
```python
class BrowserHealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.operations_count = 0
        self.memory_threshold = 2 * 1024 * 1024 * 1024  # 2GB
        
    def should_restart(self):
        """Check if browser should be restarted"""
        # Restart after 1 hour
        if time.time() - self.start_time > 3600:
            return True
        
        # Restart after 500 operations
        if self.operations_count > 500:
            return True
            
        # Check memory usage
        process = psutil.Process()
        if process.memory_info().rss > self.memory_threshold:
            return True
            
        return False
```

## Testing Instructions

### Test Browser Recovery
```bash
# Test with known problematic account
python enhanced_parking_automation.py \
  --username USER --password PASS \
  --accounts "4141 - CSLL" \
  --year 2025 --month 9 --start-day 1 --end-day 3
```

### Test Batch Processing
```bash
# Test with first 100 accounts
python enhanced_parking_automation.py \
  --username USER --password PASS \
  --year 2025 --month 9 --start-day 1 --end-day 1 \
  --batch-size 25
```

## Performance Optimization

### 1. Reduce Wait Times
```python
# Current: 5 second wait after generate button
await asyncio.sleep(5)

# Optimized: Wait for table to update
await self.page.wait_for_function("""
    () => {
        const table = document.querySelector('table');
        return table && table.rows.length > 2;
    }
""", timeout=10000)
```

### 2. Parallel Processing
```python
# Process multiple accounts simultaneously
async def process_accounts_parallel(accounts, max_concurrent=3):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(account):
        async with semaphore:
            browser = await create_browser_instance()
            # Process account with dedicated browser
            await process_account(browser, account)
            await browser.close()
    
    tasks = [process_with_limit(acc) for acc in accounts]
    await asyncio.gather(*tasks)
```

## Error Handling Improvements

### 1. Specific Error Recovery
```python
ERROR_RECOVERY_MAP = {
    "Target page, context or browser has been closed": "restart_browser",
    "Session expired": "relogin", 
    "Navigation timeout": "retry_navigation",
    "Element not found": "wait_and_retry"
}

async def handle_error(self, error_message):
    for pattern, action in ERROR_RECOVERY_MAP.items():
        if pattern in error_message:
            return await getattr(self, f"handle_{action}")()
```

### 2. Progress Checkpointing
```python
def save_checkpoint(self, account_name, date, status):
    """Save detailed checkpoint for recovery"""
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "account": account_name,
        "date": date,
        "status": status,
        "browser_uptime": time.time() - self.browser_start_time,
        "operations_since_restart": self.operations_count
    }
    
    with open("checkpoint.json", "w") as f:
        json.dump(checkpoint, f, indent=2)
```

## Deployment Strategy

### Option 1: Multiple Smaller Runs
```bash
# Run accounts in groups overnight
python run_accounts.py --group 1 --of 10  # First 60 accounts
python run_accounts.py --group 2 --of 10  # Next 60 accounts
# ...schedule with Windows Task Scheduler
```

### Option 2: Cloud Deployment
- Deploy to AWS EC2 or Google Cloud
- Use larger instance with more memory
- Run with systemd service for auto-restart

### Option 3: Switch to Selenium
```python
# More stable for long runs but slower
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def create_stable_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    return webdriver.Chrome(options=options)
```

## Success Metrics
- Process all 529 accounts without manual intervention
- Complete within 8-hour overnight window
- Zero browser crashes requiring manual restart
- Automatic recovery from all transient errors
- Complete Excel report generated with all data

## Contact & Support
For Parkonect-specific issues:
- Check session timeout settings
- Verify rate limits
- Confirm IP isn't being blocked

## Final Notes
The browser stability issue is the primary blocker. Once fixed with proper lifecycle management, the tool should run overnight successfully. Consider implementing the batch processing approach as the most reliable solution.