"""
Enhanced Parking Garage Report Automation Tool
With progress bar, resume capability, and proper number formatting
"""

import os
import asyncio
import logging
import json
import smtplib
import time
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright, Page, Browser
import argparse
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parking_report_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BrowserHealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.operations_count = 0
        self.memory_threshold = 1.5 * 1024 * 1024 * 1024  # 1.5GB

    def should_restart(self):
        """Check if browser should be restarted"""
        # Restart after 45 minutes
        if time.time() - self.start_time > 2700:
            return True

        # Restart after 300 operations
        if self.operations_count > 300:
            return True

        # Check memory usage if psutil is available
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                if process.memory_info().rss > self.memory_threshold:
                    return True
            except:
                pass

        return False

    def increment_operation(self):
        self.operations_count += 1

    def reset(self):
        self.start_time = time.time()
        self.operations_count = 0


class EnhancedParkingAutomation:
    def __init__(self, username: str, password: str, headless: bool = False):
        """
        Initialize the automation with credentials

        Args:
            username: Login username
            password: Login password
            headless: Run browser in headless mode
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://secure.parkonect.com"
        self.progress_file = "automation_progress.json"
        self.data_backup_file = "collected_data.json"
        self.progress_bar = None
        self.health_monitor = BrowserHealthMonitor()
        self.playwright_instance = None
        self.browser_start_time = time.time()
        
    def load_progress(self) -> Dict:
        """Load saved progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_progress(self, progress: Dict):
        """Save current progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def load_data_backup(self) -> Dict:
        """Load previously collected data from backup file"""
        if os.path.exists(self.data_backup_file):
            try:
                with open(self.data_backup_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load data backup: {e}")
        return {}

    def save_data_backup(self, all_data: Dict):
        """Save collected data to backup file"""
        try:
            with open(self.data_backup_file, 'w') as f:
                json.dump(all_data, f, indent=2)
            logger.debug(f"Data backup saved to {self.data_backup_file}")
        except Exception as e:
            logger.error(f"Failed to save data backup: {e}")

    def save_account_to_excel(self, account_name: str, account_data: List[Dict], output_file: str = "parking_reports.xlsx"):
        """Save single account data to Excel file incrementally"""
        if not account_data:
            logger.warning(f"No data to save for account: {account_name}")
            return False

        try:
            # Create DataFrame
            df = pd.DataFrame(account_data)

            # Convert numeric columns to integers
            numeric_columns = ['entries', 'exits', 'manual_adjustments']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # Reorder columns
            column_order = ['date', 'start_time', 'end_time', 'entries', 'exits', 'manual_adjustments']
            df = df[column_order]

            # Clean sheet name
            sheet_name = account_name
            for char in ['/', '\\', '?', '*', '[', ']', ':', '&']:
                sheet_name = sheet_name.replace(char, '-')
            sheet_name = sheet_name[:31]

            # Check if file exists
            if os.path.exists(output_file):
                # Append to existing file
                with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Format the worksheet
                    worksheet = writer.sheets[sheet_name]
                    for idx, column in enumerate(df.columns):
                        max_length = max(df[column].astype(str).str.len().max(), len(column)) + 2
                        col_letter = chr(65 + idx)
                        worksheet.column_dimensions[col_letter].width = max_length

                        if column in numeric_columns:
                            for row in range(2, len(df) + 2):
                                cell = worksheet[f'{col_letter}{row}']
                                cell.number_format = '0'
            else:
                # Create new file
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Format the worksheet
                    worksheet = writer.sheets[sheet_name]
                    for idx, column in enumerate(df.columns):
                        max_length = max(df[column].astype(str).str.len().max(), len(column)) + 2
                        col_letter = chr(65 + idx)
                        worksheet.column_dimensions[col_letter].width = max_length

                        if column in numeric_columns:
                            for row in range(2, len(df) + 2):
                                cell = worksheet[f'{col_letter}{row}']
                                cell.number_format = '0'

            logger.info(f"Successfully saved {account_name} to Excel sheet in {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save {account_name} to Excel: {str(e)}")
            return False
    
    def clear_progress(self):
        """Clear the progress file"""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            logger.info("Progress file cleared")
            
    async def setup_browser(self):
        """Setup Playwright browser and page"""
        try:
            # Close existing browser if any
            if self.browser:
                await self.browser.close()

            # Start new playwright instance if needed
            if not self.playwright_instance:
                self.playwright_instance = await async_playwright().start()

            self.browser = await self.playwright_instance.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--memory-pressure-off',
                    '--disable-background-networking'
                ]
            )
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await context.new_page()

            # Reset health monitor
            self.health_monitor.reset()
            self.browser_start_time = time.time()

            logger.info("Browser setup completed")
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            raise
        
    async def login(self):
        """Login to the parking management system (two-step process)"""
        try:
            logger.info("Attempting login...")
            await self.page.goto(f"{self.base_url}/Admin/Login.aspx")
            
            # Step 1: Enter username and click Continue
            await self.page.fill('#txtUserName', self.username)
            
            # Click Continue button (selecting by value since ID is same as login)
            await self.page.click('input[value="Continue"]')
            
            # Wait for password field to appear
            await self.page.wait_for_selector('#txtPassword', timeout=5000)
            
            # Step 2: Enter password
            await self.page.fill('#txtPassword', self.password)
            
            # Click Login button
            await self.page.click('input[value="Log in"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state('networkidle')
            
            # Verify login by checking URL or element
            await self.page.wait_for_url('**/Admin/**', timeout=10000)
            
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    async def navigate_to_reports(self, max_retries: int = 3):
        """Navigate to the reports section with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to reports... (attempt {attempt + 1})")

                # Direct URL to Monthly Count Report with extended timeout
                await self.page.goto(f"{self.base_url}/Admin/Reporting.aspx?gid=1239&rpt=27", timeout=30000)
                await self.page.wait_for_load_state('networkidle', timeout=20000)

                # Verify we're on the right page
                await self.page.wait_for_selector('#ctl00_cphBody_ddlAccounts', timeout=10000)

                logger.info("Successfully navigated to reports")
                return True

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Navigation attempt {attempt + 1} failed: {error_msg}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying navigation in 2 seconds... ({max_retries - attempt - 1} attempts left)")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"Navigation failed after {max_retries} attempts: {error_msg}")
                    return False

        return False

    async def ensure_browser_alive(self):
        """Check if browser is alive and restart if needed"""
        try:
            # Test if browser is responsive
            await self.page.evaluate('() => true')
            return True
        except Exception as e:
            if "closed" in str(e).lower():
                logger.info("Browser died, restarting...")
                await self.setup_browser()
                await self.login()
                await self.navigate_to_reports()
                return True
            else:
                raise e
    
    async def get_account_list(self) -> List[Tuple[str, str]]:
        """
        Extract list of accounts from dropdown
        Returns list of tuples (account_value, account_name)
        """
        try:
            logger.info("Extracting account list...")
            
            # Wait for account dropdown to be present
            await self.page.wait_for_selector('#ctl00_cphBody_ddlAccounts')
            
            # Get all options from the dropdown
            accounts = await self.page.evaluate('''
                () => {
                    const select = document.querySelector('#ctl00_cphBody_ddlAccounts');
                    const options = Array.from(select.options);
                    return options.map(opt => ({
                        value: opt.value,
                        text: opt.text
                    })).filter(opt => opt.value !== '-1');  // Filter out "All Accounts" option
                }
            ''')
            
            account_list = [(acc['value'], acc['text']) for acc in accounts]
            logger.info(f"Found {len(account_list)} accounts")
            
            return account_list
            
        except Exception as e:
            logger.error(f"Failed to get account list: {str(e)}")
            return []
    
    async def generate_report_with_recovery(self, account_value: str, account_name: str,
                                          start_date: str, end_date: str) -> Optional[Dict]:
        """Generate report with automatic recovery on browser failure"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check browser health before operation
                await self.ensure_browser_alive()

                # Check if we should restart browser for memory management
                if self.health_monitor.should_restart():
                    logger.info("Browser health check: restarting for maintenance...")
                    await self.setup_browser()
                    await self.login()
                    await self.navigate_to_reports()

                # Generate report
                return await self.generate_report(account_value, account_name, start_date, end_date)

            except Exception as e:
                error_msg = str(e).lower()
                if ("closed" in error_msg or "target page" in error_msg) and attempt < max_retries - 1:
                    logger.warning(f"Browser died, attempting recovery (attempt {attempt + 1})")
                    await self.setup_browser()
                    await self.login()
                    await self.navigate_to_reports()
                    await asyncio.sleep(2)  # Brief pause before retry
                else:
                    logger.error(f"Failed to generate report after {attempt + 1} attempts: {str(e)}")
                    return None
        return None

    async def generate_report(self, account_value: str, account_name: str,
                            start_date: str, end_date: str) -> Optional[Dict]:
        """
        Generate report for specific account and date range

        Args:
            account_value: Account value for dropdown
            account_name: Account display name
            start_date: Start date in MM/DD/YYYY format
            end_date: End date in MM/DD/YYYY format

        Returns:
            Dictionary with report data or None if failed
        """
        try:
            logger.info(f"Generating report for {account_name} from {start_date} to {end_date}")

            # Increment operation count for health monitoring
            self.health_monitor.increment_operation()

            # Select account
            await self.page.select_option('#ctl00_cphBody_ddlAccounts', value=account_value)
            await asyncio.sleep(0.5)

            # Clear and set start date
            await self.page.fill('#ctl00_cphBody_txtStartDate', '')
            await self.page.fill('#ctl00_cphBody_txtStartDate', start_date)
            await asyncio.sleep(0.5)

            # Clear and set end date
            await self.page.fill('#ctl00_cphBody_txtEndDate', '')
            await self.page.fill('#ctl00_cphBody_txtEndDate', end_date)
            await asyncio.sleep(0.5)

            # Click Generate Report button
            await self.page.click('#ctl00_cphBody_btnGenarate')

            # Wait for table to update with more intelligent waiting
            await self.wait_for_report_completion()

            # Extract table data
            report_data = await self.extract_table_data()

            if report_data:
                return {
                    'account': account_name,
                    'date': start_date,
                    'data': report_data
                }
            else:
                logger.warning(f"No data extracted for {account_name} on {start_date}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate report for {account_name} on {start_date}: {str(e)}")
            return None

    async def wait_for_report_completion(self):
        """Wait for report to complete with intelligent waiting"""
        try:
            # Wait for table to appear and update
            await self.page.wait_for_function("""
                () => {
                    const table = document.querySelector('table');
                    return table && table.rows.length > 2;
                }
            """, timeout=15000)

            # Additional small wait for final render
            await asyncio.sleep(1)
        except:
            # Fallback to original timing if smart wait fails
            await asyncio.sleep(5)
    
    async def extract_table_data(self) -> Optional[List[Dict]]:
        """
        Extract data from the report table
        
        Returns:
            List of dictionaries containing row data
        """
        try:
            # Wait for table to be present
            await self.page.wait_for_selector('table', timeout=10000)
            
            # Extract table data using JavaScript
            table_data = await self.page.evaluate('''
                () => {
                    const table = document.querySelector('table');
                    const rows = Array.from(table.querySelectorAll('tr'));
                    
                    // Skip header row and totals row
                    const dataRows = rows.slice(1, -1);
                    
                    return dataRows.map(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        
                        // Extract text content, handling both plain text and hyperlinks
                        const getText = (cell) => {
                            if (!cell) return '';
                            // Check if cell contains a link
                            const link = cell.querySelector('a');
                            return link ? link.innerText.trim() : cell.innerText.trim();
                        };
                        
                        return {
                            start_time: getText(cells[0]),
                            end_time: getText(cells[1]),
                            entries: getText(cells[2]) || '0',
                            exits: getText(cells[3]) || '0',
                            manual_adjustments: getText(cells[4]) || '0'
                        };
                    });
                }
            ''')
            
            return table_data
            
        except Exception as e:
            logger.error(f"Failed to extract table data: {str(e)}")
            return None
    
    def get_date_range(self, year: int, month: int, 
                      start_day: Optional[int] = None, 
                      end_day: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Generate list of date pairs for a given month or custom range
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            start_day: Optional start day (default: 1)
            end_day: Optional end day (default: last day of month)
            
        Returns:
            List of tuples (start_date, end_date) in MM/DD/YYYY format
        """
        # Get first day of month
        first_day = datetime(year, month, start_day or 1)
        
        # Get last day of month or specified end day
        if end_day:
            last_day = datetime(year, month, end_day)
        else:
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Generate date pairs (each day individually)
        date_pairs = []
        current_date = first_day
        
        while current_date <= last_day:
            date_str = current_date.strftime("%m/%d/%Y")
            date_pairs.append((date_str, date_str))
            current_date += timedelta(days=1)
        
        return date_pairs

    def split_accounts_into_batches(self, accounts: List[Tuple[str, str]], batch_size: int = 25) -> List[List[Tuple[str, str]]]:
        """Split accounts into manageable batches"""
        batches = []
        for i in range(0, len(accounts), batch_size):
            batch = accounts[i:i + batch_size]
            batches.append(batch)
        return batches

    def save_batch_progress(self, progress: Dict, batch_num: int, total_batches: int):
        """Save progress after each batch with detailed info"""
        progress['current_batch'] = batch_num
        progress['total_batches'] = total_batches
        progress['batch_completed_at'] = datetime.now().isoformat()
        self.save_progress(progress)
        logger.info(f"Batch {batch_num}/{total_batches} completed and progress saved")

    async def process_all_reports(self, year: int, month: int,
                                account_filter: Optional[List[str]] = None,
                                start_day: Optional[int] = None,
                                end_day: Optional[int] = None,
                                resume: bool = False,
                                batch_size: int = 25,
                                output_file: str = "parking_reports.xlsx") -> Dict:
        """
        Process reports for all accounts and days in the specified month with batch processing

        Args:
            year: Year to process
            month: Month to process (1-12)
            account_filter: Optional list of account names to process (None = all)
            start_day: Optional start day
            end_day: Optional end day
            resume: Whether to resume from last progress
            batch_size: Number of accounts to process before browser restart

        Returns:
            Dictionary with all collected data
        """
        # Load existing data if resuming
        all_data = self.load_data_backup() if resume else {}
        progress = self.load_progress() if resume else {}

        logger.info(f"{'Resuming with' if resume else 'Starting with'} {len(all_data)} accounts already processed")

        # Setup browser and login
        await self.setup_browser()

        if not await self.login():
            logger.error("Login failed, aborting...")
            return all_data

        if not await self.navigate_to_reports():
            logger.error("Failed to navigate to reports, aborting...")
            return all_data

        # Get list of accounts
        accounts = await self.get_account_list()

        if account_filter:
            accounts = [(v, n) for v, n in accounts if n in account_filter]

        # Get date range for the month
        date_pairs = self.get_date_range(year, month, start_day, end_day)

        # Split accounts into batches for browser management
        batches = self.split_accounts_into_batches(accounts, batch_size)

        # Calculate total operations for progress bar
        total_operations = len(accounts) * len(date_pairs)

        logger.info(f"Processing {len(accounts)} accounts in {len(batches)} batches for {len(date_pairs)} days = {total_operations} operations")

        # Create progress bar
        self.progress_bar = tqdm(total=total_operations, desc="Processing reports")

        # Process batches
        start_batch = progress.get('current_batch', 0) if resume else 0

        for batch_num, batch in enumerate(batches, 1):
            # Skip completed batches on resume
            if batch_num <= start_batch:
                completed_accounts = len(batch) * len(date_pairs)
                self.progress_bar.update(completed_accounts)
                logger.info(f"Skipping completed batch {batch_num}/{len(batches)}")
                continue

            logger.info(f"Processing batch {batch_num} of {len(batches)} ({len(batch)} accounts)")

            # Restart browser for each batch (except first)
            if batch_num > 1:
                logger.info("Restarting browser for new batch...")
                await self.setup_browser()
                if not await self.login():
                    logger.error("Login failed during batch processing")
                    break
                if not await self.navigate_to_reports():
                    logger.error("Failed to navigate to reports during batch processing")
                    break

            # Process accounts in this batch
            batch_success = True
            for account_value, account_name in batch:
                # Check if this account was already processed (for resume within batch)
                if resume and account_name in progress.get('completed_accounts', []):
                    logger.info(f"Skipping already completed account: {account_name}")
                    self.progress_bar.update(len(date_pairs))
                    continue

                logger.info(f"Processing account: {account_name}")
                account_data = []

                # Process each day for this account
                account_success = True
                for start_date, end_date in date_pairs:
                    report = await self.generate_report_with_recovery(
                        account_value, account_name, start_date, end_date
                    )

                    if report:
                        # Add date to each row of data
                        for row in report['data']:
                            row['date'] = start_date
                        account_data.extend(report['data'])
                    else:
                        logger.warning(f"Failed to get report for {account_name} on {start_date}")
                        account_success = False

                    # Update progress bar
                    self.progress_bar.update(1)

                    # Small delay between requests
                    await asyncio.sleep(0.5)

                all_data[account_name] = account_data

                # DUAL PERSISTENCE: Save immediately after each account
                # 1. Save to Excel (incremental - one sheet per account)
                if account_data:
                    self.save_account_to_excel(account_name, account_data, output_file)

                # 2. Save to JSON backup (all data so far)
                self.save_data_backup(all_data)

                # Save progress after each account
                if 'completed_accounts' not in progress:
                    progress['completed_accounts'] = []
                progress['completed_accounts'].append(account_name)
                progress['last_processed'] = datetime.now().isoformat()

                if not account_success:
                    batch_success = False

            # Save batch progress
            self.save_batch_progress(progress, batch_num, len(batches))

            # Brief pause between batches
            if batch_num < len(batches):
                await asyncio.sleep(2)

        # Close progress bar
        self.progress_bar.close()

        # Clear progress file after successful completion
        if len(progress.get('completed_accounts', [])) >= len(accounts) * 0.95:  # 95% completion
            self.clear_progress()
            logger.info("Process completed successfully - progress file cleared")

        # Clean browser shutdown
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright_instance:
                await self.playwright_instance.stop()
        except:
            pass

        logger.info("Data collection completed")

        return all_data
    
    def export_to_excel(self, data: Dict, output_file: str = "parking_reports.xlsx"):
        """
        Export collected data to Excel file with proper number formatting
        
        Args:
            data: Dictionary with account names as keys and data lists as values
            output_file: Output Excel filename
        """
        try:
            logger.info(f"Exporting data to {output_file}")
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for account_name, account_data in data.items():
                    if account_data:
                        # Create DataFrame
                        df = pd.DataFrame(account_data)
                        
                        # Convert numeric columns to integers
                        numeric_columns = ['entries', 'exits', 'manual_adjustments']
                        for col in numeric_columns:
                            if col in df.columns:
                                # Convert to numeric, handling any non-numeric values
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                        
                        # Reorder columns
                        column_order = ['date', 'start_time', 'end_time', 
                                      'entries', 'exits', 'manual_adjustments']
                        df = df[column_order]
                        
                        # Clean sheet name (Excel has limitations on sheet names)
                        # Remove invalid characters and limit to 31 characters
                        sheet_name = account_name
                        for char in ['/', '\\', '?', '*', '[', ']', ':', '&']:
                            sheet_name = sheet_name.replace(char, '-')
                        sheet_name = sheet_name[:31]
                        
                        # Write to Excel
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # Get the worksheet to format it
                        worksheet = writer.sheets[sheet_name]
                        
                        # Auto-adjust column widths and format numbers
                        for idx, column in enumerate(df.columns):
                            max_length = max(
                                df[column].astype(str).str.len().max(),
                                len(column)
                            ) + 2
                            # Excel columns use letters A, B, C, etc.
                            col_letter = chr(65 + idx)
                            worksheet.column_dimensions[col_letter].width = max_length
                            
                            # Format numeric columns
                            if column in numeric_columns:
                                for row in range(2, len(df) + 2):  # Start from row 2 (after header)
                                    cell = worksheet[f'{col_letter}{row}']
                                    cell.number_format = '0'  # Format as integer
            
            logger.info(f"Successfully exported data to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {str(e)}")
    
    def send_email_notification(self, to_email: str, from_email: str, 
                               password: str, smtp_server: str = "smtp.gmail.com",
                               smtp_port: int = 587):
        """
        Send email notification when process is complete
        
        Args:
            to_email: Recipient email
            from_email: Sender email
            password: Email password
            smtp_server: SMTP server address
            smtp_port: SMTP port
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"Parking Report Generation Complete - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
            The parking report generation has been completed successfully.
            
            Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Output File: parking_reports.xlsx
            
            Please find the Excel file with all the reports.
            
            Best regards,
            Parking Report Automation
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Enhanced Parking Report Automation')
    parser.add_argument('--username', required=True, help='Login username')
    parser.add_argument('--password', required=True, help='Login password')
    parser.add_argument('--year', type=int, default=datetime.now().year, 
                       help='Year to process (default: current year)')
    parser.add_argument('--month', type=int, default=datetime.now().month, 
                       help='Month to process (1-12, default: current month)')
    parser.add_argument('--start-day', type=int, help='Start day (optional)')
    parser.add_argument('--end-day', type=int, help='End day (optional)')
    parser.add_argument('--output', default='parking_reports.xlsx', 
                       help='Output Excel filename')
    parser.add_argument('--headless', action='store_true', 
                       help='Run browser in headless mode')
    parser.add_argument('--accounts', nargs='+', 
                       help='Specific account names to process (optional)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last saved progress')
    parser.add_argument('--email-to', help='Send notification to this email when complete')
    parser.add_argument('--email-from', help='Send notification from this email')
    parser.add_argument('--email-password', help='Email password for sending notifications')
    parser.add_argument('--batch-size', type=int, default=25,
                       help='Number of accounts to process before browser restart (default: 25)')
    
    args = parser.parse_args()
    
    # Create automation instance
    automation = EnhancedParkingAutomation(
        username=args.username,
        password=args.password,
        headless=args.headless
    )
    
    # Process all reports with batch processing
    data = await automation.process_all_reports(
        year=args.year,
        month=args.month,
        account_filter=args.accounts,
        start_day=args.start_day,
        end_day=args.end_day,
        resume=args.resume,
        batch_size=25,  # Process 25 accounts before browser restart
        output_file=args.output
    )
    
    # Excel export is now done incrementally during processing
    # Final export is no longer needed since data is saved per account
    logger.info(f"All processing complete. Excel file: {args.output}")

    # Send email notification if configured
    if args.email_to and args.email_from and args.email_password:
        automation.send_email_notification(
            to_email=args.email_to,
            from_email=args.email_from,
            password=args.email_password
        )

    logger.info("Process completed successfully")


if __name__ == "__main__":
    asyncio.run(main())