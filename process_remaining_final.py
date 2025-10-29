#!/usr/bin/env python3
"""
Final script to process remaining accounts with graceful skipping
"""

import asyncio
import json
from enhanced_parking_automation import EnhancedParkingAutomation

async def process_remaining_final():
    """Process remaining accounts with automatic skipping of unmatched accounts"""
    print("Starting final processing of remaining accounts...")

    # Load the processing list
    try:
        with open('final_processing_list.json', 'r') as f:
            processing_data = json.load(f)
    except FileNotFoundError:
        print("Error: final_processing_list.json not found. Run analyze_accounts_final.py first.")
        return

    # Get account lists
    confident_accounts = processing_data['confident_accounts']
    probable_accounts = processing_data['probable_accounts']
    all_processable = processing_data['all_processable']

    print(f"Found {len(confident_accounts)} confident matches")
    print(f"Found {len(probable_accounts)} probable matches")
    print(f"Total processable: {len(all_processable)} accounts")
    print(f"Unprocessed: {len(processing_data['unprocessed_accounts'])} accounts (saved separately)")

    # Ask user which set to process
    print(f"\\nProcessing options:")
    print(f"1. Process {len(confident_accounts)} confident matches only (SAFEST)")
    print(f"2. Process {len(all_processable)} confident + probable matches")
    print(f"3. Show first 10 accounts that will be processed")
    print(f"4. Exit")

    choice = input("Choice (1-4): ").strip()

    if choice == "3":
        print(f"\\nFirst 10 confident matches:")
        for i, account in enumerate(confident_accounts[:10]):
            print(f"  {i+1}. {account}")
        if probable_accounts:
            print(f"\\nFirst 5 probable matches:")
            for i, account in enumerate(probable_accounts[:5]):
                print(f"  {i+1}. {account}")
        return

    if choice == "4":
        print("Exiting...")
        return

    # Select accounts to process
    if choice == "1":
        accounts_to_process = confident_accounts
        print(f"Processing {len(accounts_to_process)} confident matches...")
    elif choice == "2":
        accounts_to_process = all_processable
        print(f"Processing {len(accounts_to_process)} confident + probable matches...")
    else:
        print("Invalid choice. Using confident matches only.")
        accounts_to_process = confident_accounts

    if not accounts_to_process:
        print("No accounts to process. Exiting.")
        return

    # Read credentials
    try:
        with open('login.txt', 'r') as f:
            lines = f.readlines()
            username = lines[0].split(': ')[1].strip()
            password = lines[1].split(': ')[1].strip()
    except Exception as e:
        print(f"Error reading login.txt: {e}")
        return

    print(f"\\nStarting automated processing...")
    print(f"- Accounts to process: {len(accounts_to_process)}")
    print(f"- Output Excel: remaining_accounts_reports.xlsx")
    print(f"- JSON backup: collected_data.json")
    print(f"- Progress tracking: automation_progress.json")
    print(f"- Unprocessed accounts: unprocessed_accounts_final.json")

    # Start processing
    try:
        automation = EnhancedParkingAutomation(username, password, headless=False)

        # Process accounts with dual persistence
        data = await automation.process_all_reports(
            year=2025,
            month=9,
            account_filter=accounts_to_process,
            start_day=1,
            end_day=30,
            resume=True,  # Resume if previously interrupted
            batch_size=20,  # Smaller batches for stability
            output_file="remaining_accounts_reports.xlsx"
        )

        print(f"\\n=== PROCESSING COMPLETED ===")
        print(f"Processed accounts: {len(accounts_to_process)}")
        print(f"Excel file: remaining_accounts_reports.xlsx")
        print(f"JSON backup: collected_data.json")
        print(f"Manual review needed: unprocessed_accounts_final.json")

        print(f"\\nThe Excel file contains one sheet per account with all parking data.")
        print(f"Data is automatically saved after each account, so no data loss on crashes.")

    except KeyboardInterrupt:
        print(f"\\n=== PROCESSING INTERRUPTED ===")
        print(f"Progress has been saved. You can resume by running this script again.")
        print(f"All completed accounts are already in the Excel file.")

    except Exception as e:
        print(f"Error during processing: {e}")
        print(f"Check the logs and try resuming with the same command.")

def main():
    """Main entry point"""
    print("=== PARKING AUTOMATION - REMAINING ACCOUNTS ===")
    print("This script will process your remaining accounts with:")
    print("- Smart account matching")
    print("- Incremental Excel writing (one sheet per account)")
    print("- JSON backup for crash recovery")
    print("- Automatic skipping of unmatched accounts")
    print("- Resume capability")

    # Check if analysis was done
    try:
        with open('final_processing_list.json', 'r') as f:
            pass
    except FileNotFoundError:
        print(f"\\nFirst-time setup needed...")
        print(f"Run: python analyze_accounts_final.py")
        return

    asyncio.run(process_remaining_final())

if __name__ == "__main__":
    main()