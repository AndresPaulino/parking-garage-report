"""
Parking Garage Report Automation Tool
Extracts daily entry/exit data from parking management system
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from playwright.async_api import async_playwright, Page, Browser
import argparse
from pathlib import Path

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

class ParkingReportAutomation:
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
        self.base_url = "https://secure.parkonect.com/Admin/Login.aspx" 
        
    async def setup_browser(self):
        """Setup Playwright browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        logger.info("Browser setup completed")
        
    async def login(self):
        """Login to the parking management system"""
        try:
            logger.info("Attempting login...")
            await self.page.goto(f"{self.base_url}")  # Update with actual login URL
            
            # Fill in credentials
            await self.page.fill('input[name="username"]', self.username)  # Update selector
            await self.page.fill('input[name="password"]', self.password)  # Update selector
            
            # Click login button
            await self.page.click('button[type="submit"]')  # Update selector
            
            # Wait for navigation or specific element that appears after login
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_selector('.dashboard', timeout=10000)  # Update selector
            
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    async def navigate_to_reports(self):
        """Navigate to the reports section"""
        try:
            logger.info("Navigating to reports...")
            
            # Navigate to reports page - update URL/selectors as needed
            await self.page.goto(f"{self.base_url}/reports/monthly-count")
            await self.page.wait_for_load_state('networkidle')
            
            logger.info("Successfully navigated to reports")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to reports: {str(e)}")
            return False
    
    async def get_account_list(self) -> List[Tuple[str, str]]:
        """
        Extract list of accounts from dropdown
        Returns list of tuples (account_value, account_name)
        """
        try:
            logger.info("Extracting account list...")
            
            # Wait for account dropdown to be present
            await self.page.wait_for_selector('select#account')  # Update selector
            
            # Get all options from the dropdown
            accounts = await self.page.evaluate('''
                () => {
                    const select = document.querySelector('select#account');
                    const options = Array.from(select.options);
                    return options.map(opt => ({
                        value: opt.value,
                        text: opt.text
                    })).filter(opt => opt.value !== '');  // Filter out empty/placeholder options
                }
            ''')
            
            account_list = [(acc['value'], acc['text']) for acc in accounts]
            logger.info(f"Found {len(account_list)} accounts")
            
            return account_list
            
        except Exception as e:
            logger.error(f"Failed to get account list: {str(e)}")
            return []
    
    async def select_garage(self):
        """Select Miami DD - Museum Garage from dropdown"""
        try:
            garage_name = "Miami DD - Museum Garage"
            logger.info(f"Selecting garage: {garage_name}")
            
            await self.page.select_option('select#garage', label=garage_name)  # Update selector
            await asyncio.sleep(1)  # Small delay for form to update
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to select garage: {str(e)}")
            return False
    
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
            
            # Select account
            await self.page.select_option('select#account', value=account_value)  # Update selector
            await asyncio.sleep(0.5)
            
            # Set start date
            await self.page.fill('input#start-date', start_date)  # Update selector
            await asyncio.sleep(0.5)
            
            # Set end date
            await self.page.fill('input#end-date', end_date)  # Update selector
            await asyncio.sleep(0.5)
            
            # Click Generate Report button
            await self.page.click('button#generate-report')  # Update selector
            
            # Wait for report to load (approximately 5 seconds as mentioned)
            await asyncio.sleep(5)
            
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
    
    async def extract_table_data(self) -> Optional[List[Dict]]:
        """
        Extract data from the report table
        
        Returns:
            List of dictionaries containing row data
        """
        try:
            # Wait for table to be present
            await self.page.wait_for_selector('table', timeout=10000)  # Update selector
            
            # Extract table data using JavaScript
            table_data = await self.page.evaluate('''
                () => {
                    const table = document.querySelector('table');
                    const rows = Array.from(table.querySelectorAll('tr'));
                    
                    // Skip header row and totals row
                    const dataRows = rows.slice(1, -1);
                    
                    return dataRows.map(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        return {
                            start_time: cells[0]?.innerText?.trim() || '',
                            end_time: cells[1]?.innerText?.trim() || '',
                            entries: cells[2]?.innerText?.trim() || '0',
                            exits: cells[3]?.innerText?.trim() || '0',
                            manual_adjustments: cells[4]?.innerText?.trim() || '0'
                        };
                    });
                }
            ''')
            
            return table_data
            
        except Exception as e:
            logger.error(f"Failed to extract table data: {str(e)}")
            return None
    
    def get_date_range(self, year: int, month: int) -> List[Tuple[str, str]]:
        """
        Generate list of date pairs for a given month
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            List of tuples (start_date, end_date) in MM/DD/YYYY format
        """
        # Get first day of month
        first_day = datetime(year, month, 1)
        
        # Get last day of month
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
    
    async def process_all_reports(self, year: int, month: int, 
                                account_filter: Optional[List[str]] = None) -> Dict:
        """
        Process reports for all accounts and days in the specified month
        
        Args:
            year: Year to process
            month: Month to process (1-12)
            account_filter: Optional list of account names to process (None = all)
            
        Returns:
            Dictionary with all collected data
        """
        all_data = {}
        
        # Setup browser and login
        await self.setup_browser()
        
        if not await self.login():
            logger.error("Login failed, aborting...")
            return all_data
        
        if not await self.navigate_to_reports():
            logger.error("Failed to navigate to reports, aborting...")
            return all_data
        
        if not await self.select_garage():
            logger.error("Failed to select garage, aborting...")
            return all_data
        
        # Get list of accounts
        accounts = await self.get_account_list()
        
        if account_filter:
            accounts = [(v, n) for v, n in accounts if n in account_filter]
        
        # Get date range for the month
        date_pairs = self.get_date_range(year, month)
        
        logger.info(f"Processing {len(accounts)} accounts for {len(date_pairs)} days")
        
        # Process each account
        for account_value, account_name in accounts:
            logger.info(f"Processing account: {account_name}")
            account_data = []
            
            # Process each day
            for start_date, end_date in date_pairs:
                report = await self.generate_report(
                    account_value, account_name, start_date, end_date
                )
                
                if report:
                    # Add date to each row of data
                    for row in report['data']:
                        row['date'] = start_date
                    account_data.extend(report['data'])
                
                # Small delay between requests to avoid overwhelming the server
                await asyncio.sleep(1)
            
            all_data[account_name] = account_data
        
        await self.browser.close()
        logger.info("Data collection completed")
        
        return all_data
    
    def export_to_excel(self, data: Dict, output_file: str = "parking_reports.xlsx"):
        """
        Export collected data to Excel file
        
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
                        
                        # Reorder columns
                        column_order = ['date', 'start_time', 'end_time', 
                                      'entries', 'exits', 'manual_adjustments']
                        df = df[column_order]
                        
                        # Clean sheet name (Excel has limitations on sheet names)
                        sheet_name = account_name[:31].replace('/', '-').replace('\\', '-')
                        
                        # Write to Excel
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets[sheet_name]
                        for column in df:
                            column_width = max(df[column].astype(str).str.len().max(), 
                                             len(column)) + 2
                            col_idx = df.columns.get_loc(column)
                            worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
            
            logger.info(f"Successfully exported data to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {str(e)}")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Parking Report Automation')
    parser.add_argument('--username', required=True, help='Login username')
    parser.add_argument('--password', required=True, help='Login password')
    parser.add_argument('--year', type=int, default=datetime.now().year, 
                       help='Year to process (default: current year)')
    parser.add_argument('--month', type=int, default=datetime.now().month, 
                       help='Month to process (1-12, default: current month)')
    parser.add_argument('--output', default='parking_reports.xlsx', 
                       help='Output Excel filename')
    parser.add_argument('--headless', action='store_true', 
                       help='Run browser in headless mode')
    parser.add_argument('--accounts', nargs='+', 
                       help='Specific account names to process (optional)')
    
    args = parser.parse_args()
    
    # Create automation instance
    automation = ParkingReportAutomation(
        username=args.username,
        password=args.password,
        headless=args.headless
    )
    
    # Process all reports
    data = await automation.process_all_reports(
        year=args.year,
        month=args.month,
        account_filter=args.accounts
    )
    
    # Export to Excel
    if data:
        automation.export_to_excel(data, args.output)
        logger.info("Process completed successfully")
    else:
        logger.error("No data collected")


if __name__ == "__main__":
    asyncio.run(main())