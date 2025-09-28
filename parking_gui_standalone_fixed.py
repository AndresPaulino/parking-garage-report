"""
parking_gui_standalone_fixed.py - Fixed encoding issues for overnight runs
Handles special characters properly and adds auto-retry on errors
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
from datetime import datetime
import sys
import os
import json
import time
import codecs

class ParkingReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Report Generator - Overnight Edition")
        self.root.geometry("700x800")
        
        # Variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.month_var = tk.StringVar(value=str(datetime.now().month))
        self.start_day_var = tk.StringVar()
        self.end_day_var = tk.StringVar()
        self.output_file_var = tk.StringVar(value="parking_reports.xlsx")
        self.headless_var = tk.BooleanVar(value=True)
        self.resume_var = tk.BooleanVar(value=False)
        self.auto_retry_var = tk.BooleanVar(value=True)  # New: auto-retry on errors
        self.accounts_var = tk.StringVar()
        
        self.process = None
        self.selection_mode = tk.StringVar(value="all")
        self.error_count = 0
        self.retry_count = 0
        self.max_retries = 3
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI elements"""
        
        # Title
        title_label = tk.Label(self.root, text="Parking Report Generator - Overnight Edition", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Status Frame (NEW - shows progress stats)
        status_frame = tk.LabelFrame(self.root, text="Status", padx=20, pady=10)
        status_frame.pack(padx=20, pady=5, fill="x")
        
        self.status_info = tk.Label(status_frame, text="Ready to start", 
                                   font=("Arial", 10), fg="green")
        self.status_info.pack()
        
        # Login Frame
        login_frame = tk.LabelFrame(self.root, text="Login Credentials", padx=20, pady=10)
        login_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(login_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, pady=5)
        
        tk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(login_frame, textvariable=self.password_var, width=30, show="*").grid(row=1, column=1, pady=5)
        
        # Date Range Frame
        date_frame = tk.LabelFrame(self.root, text="Date Range", padx=20, pady=10)
        date_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Label(date_frame, text="Year:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(date_frame, textvariable=self.year_var, width=10).grid(row=0, column=1, pady=5, sticky="w")
        
        tk.Label(date_frame, text="Month (1-12):").grid(row=1, column=0, sticky="w", pady=5)
        month_combo = ttk.Combobox(date_frame, textvariable=self.month_var, 
                                   values=[str(i) for i in range(1, 13)], width=7, state="readonly")
        month_combo.grid(row=1, column=1, pady=5, sticky="w")
        
        tk.Label(date_frame, text="Start Day (optional):").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(date_frame, textvariable=self.start_day_var, width=10).grid(row=2, column=1, pady=5, sticky="w")
        
        tk.Label(date_frame, text="End Day (optional):").grid(row=3, column=0, sticky="w", pady=5)
        tk.Entry(date_frame, textvariable=self.end_day_var, width=10).grid(row=3, column=1, pady=5, sticky="w")
        
        # Account Selection Frame
        account_frame = tk.LabelFrame(self.root, text="Account Selection", padx=20, pady=10)
        account_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Radiobutton(account_frame, text="Process ALL accounts (600+)", 
                      variable=self.selection_mode, value="all",
                      command=self.toggle_account_entry,
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(account_frame, text="Process specific accounts only", 
                      variable=self.selection_mode, value="specific",
                      command=self.toggle_account_entry,
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        
        self.account_entry_frame = tk.Frame(account_frame)
        self.account_entry_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(self.account_entry_frame, text="Enter account names (comma-separated):").pack(anchor="w")
        self.account_entry = tk.Entry(self.account_entry_frame, textvariable=self.accounts_var, 
                                      width=50, state="disabled")
        self.account_entry.pack(anchor="w", pady=2)
        
        # Info label
        self.info_label = tk.Label(account_frame, text="Will process ALL accounts", 
                                  font=("Arial", 9), fg="blue")
        self.info_label.pack(pady=(5, 0))
        
        # Options Frame
        options_frame = tk.LabelFrame(self.root, text="Options", padx=20, pady=10)
        options_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Checkbutton(options_frame, text="Run in background (headless mode)", 
                      variable=self.headless_var).pack(anchor="w", pady=2)
        tk.Checkbutton(options_frame, text="Resume from last progress", 
                      variable=self.resume_var).pack(anchor="w", pady=2)
        tk.Checkbutton(options_frame, text="Auto-retry on errors (for overnight runs)", 
                      variable=self.auto_retry_var, fg="green").pack(anchor="w", pady=2)
        
        tk.Label(options_frame, text="Output File:").pack(anchor="w", pady=(10, 0))
        tk.Entry(options_frame, textvariable=self.output_file_var, width=40).pack(anchor="w", pady=2)
        
        # Buttons Frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)
        
        self.start_button = tk.Button(button_frame, text="Start Processing", 
                                      command=self.start_processing, 
                                      bg="#28a745", fg="white", padx=20, pady=10,
                                      font=("Arial", 10, "bold"))
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop", 
                                     command=self.stop_processing,
                                     bg="#dc3545", fg="white", padx=20, pady=10,
                                     state="disabled", font=("Arial", 10, "bold"))
        self.stop_button.pack(side="left", padx=5)
        
        # Log Frame
        log_frame = tk.LabelFrame(self.root, text="Output Log", padx=20, pady=10)
        log_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70, 
                                                  bg="#f8f9fa", fg="#212529")
        self.log_text.pack(fill="both", expand=True)
        
        # Status Bar
        self.status_label = tk.Label(self.root, text="Ready", bd=1, relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x")
        
    def toggle_account_entry(self):
        """Enable/disable account entry based on selection mode"""
        if self.selection_mode.get() == "all":
            self.account_entry.config(state="disabled")
            self.accounts_var.set("")
            self.info_label.config(text="Will process ALL accounts (600+)")
        else:
            self.account_entry.config(state="normal")
            self.info_label.config(text="Will process only specified accounts")
            
    def log_message(self, message, level="INFO"):
        """Add message to log window with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Color code by level
        if "ERROR" in message or level == "ERROR":
            message = f"⚠️ {message}"
            self.error_count += 1
        elif "SUCCESS" in message or level == "SUCCESS":
            message = f"✅ {message}"
        
        self.log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
        # Update status info
        if self.error_count > 0:
            self.status_info.config(
                text=f"Running... Errors: {self.error_count}, Retries: {self.retry_count}",
                fg="orange"
            )
    
    def get_python_executable(self):
        """Get the correct Python executable"""
        if getattr(sys, 'frozen', False):
            import shutil
            python_exe = shutil.which('python')
            if python_exe:
                return python_exe
            
            # Try common paths
            common_paths = [
                r"C:\Python39\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python311\python.exe",
                r"C:\Python312\python.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            return None
        else:
            return sys.executable
        
    def start_processing(self):
        """Start the processing in a separate thread"""
        if not self.username_var.get() or not self.password_var.get():
            messagebox.showerror("Error", "Please enter username and password")
            return
            
        if self.selection_mode.get() == "specific" and not self.accounts_var.get().strip():
            messagebox.showerror("Error", "Please enter at least one account name or select 'Process ALL accounts'")
            return
        
        python_exe = self.get_python_executable()
        if not python_exe:
            messagebox.showerror("Error", "Python not found!")
            return
            
        # Reset counters
        self.error_count = 0
        self.retry_count = 0
        
        # Disable start button, enable stop button
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="Processing...")
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=lambda: self.run_automation_with_retry(python_exe))
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def run_automation_with_retry(self, python_exe):
        """Run automation with automatic retry on failure"""
        attempt = 0
        max_attempts = 3 if self.auto_retry_var.get() else 1
        
        while attempt < max_attempts:
            attempt += 1
            
            if attempt > 1:
                self.retry_count += 1
                self.log_message(f"Retry attempt {attempt} of {max_attempts}...", "WARNING")
                time.sleep(5)  # Wait 5 seconds before retry
            
            success = self.run_automation(python_exe)
            
            if success:
                self.log_message("Processing completed successfully!", "SUCCESS")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Processing complete!\n\nReport saved to: {self.output_file_var.get()}\n"
                    f"Errors encountered: {self.error_count}\n"
                    f"Retries needed: {self.retry_count}"
                ))
                break
            else:
                if attempt < max_attempts and self.auto_retry_var.get():
                    self.log_message(f"Process failed, will retry... ({max_attempts - attempt} retries left)")
                else:
                    self.log_message("Process failed after all attempts", "ERROR")
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Process Incomplete",
                        f"The process encountered errors.\n\n"
                        f"Errors: {self.error_count}\n"
                        f"Retries: {self.retry_count}\n\n"
                        f"Check the log and try running with 'Resume from last progress' enabled."
                    ))
        
        self.root.after(0, self.processing_complete)
        
    def run_automation(self, python_exe):
        """Run the automation process using subprocess with fixed encoding"""
        try:
            self.log_message("Starting automation...")
            
            script_name = "enhanced_parking_automation.py"
            if not os.path.exists(script_name):
                if getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    script_path = os.path.join(exe_dir, script_name)
                    if not os.path.exists(script_path):
                        self.log_message(f"ERROR: {script_name} not found!")
                        return False
                else:
                    self.log_message(f"ERROR: {script_name} not found!")
                    return False
            
            # Build command
            cmd = [
                python_exe,
                script_name,
                "--username", self.username_var.get(),
                "--password", self.password_var.get(),
                "--year", self.year_var.get(),
                "--month", self.month_var.get(),
                "--output", self.output_file_var.get()
            ]
            
            # Add optional parameters
            if self.start_day_var.get():
                cmd.extend(["--start-day", self.start_day_var.get()])
            
            if self.end_day_var.get():
                cmd.extend(["--end-day", self.end_day_var.get()])
            
            if self.headless_var.get():
                cmd.append("--headless")
            
            if self.resume_var.get() or self.retry_count > 0:
                cmd.append("--resume")  # Always resume on retries
            
            # Add accounts if specific mode
            if self.selection_mode.get() == "specific":
                accounts = self.accounts_var.get().strip()
                if accounts:
                    cmd.append("--accounts")
                    for account in accounts.split(','):
                        account = account.strip()
                        if account:
                            cmd.append(account)
            
            self.log_message("Command prepared, starting process...")
            
            # FIX: Force UTF-8 encoding for Windows
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'  # Force Python to use UTF-8
            
            # Set console code page to UTF-8 on Windows
            if sys.platform == 'win32':
                subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
            
            # Run the process with UTF-8 encoding
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=False,  # Read as bytes
                env=env,
                errors=None  # Don't decode yet
            )
            
            # Read output with proper encoding handling
            while True:
                # Read stdout
                output = self.process.stdout.readline()
                if output:
                    try:
                        # Try UTF-8 first
                        line = output.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        try:
                            # Fallback to Windows encoding
                            line = output.decode('cp1252', errors='replace').strip()
                        except:
                            # Last resort - ignore errors
                            line = output.decode('utf-8', errors='ignore').strip()
                    
                    if line and not line.startswith("Exception ignored"):
                        self.log_message(line)
                
                # Check if process has ended
                if self.process.poll() is not None:
                    break
            
            # Get any remaining output
            remaining_out, remaining_err = self.process.communicate()
            
            if remaining_out:
                try:
                    lines = remaining_out.decode('utf-8', errors='ignore').strip()
                    if lines:
                        for line in lines.split('\n'):
                            if line and not line.startswith("Exception ignored"):
                                self.log_message(line)
                except:
                    pass
            
            # Check return code
            if self.process.returncode == 0:
                return True
            else:
                self.log_message(f"Process exited with code: {self.process.returncode}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Error running automation: {str(e)}", "ERROR")
            return False
            
    def processing_complete(self):
        """Reset GUI after processing completes"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if self.error_count == 0:
            self.status_label.config(text="Completed successfully")
            self.status_info.config(text="All done! No errors.", fg="green")
        else:
            self.status_label.config(text="Completed with errors")
            self.status_info.config(
                text=f"Completed. Errors: {self.error_count}, Retries: {self.retry_count}", 
                fg="orange"
            )
        
        self.process = None
        
    def stop_processing(self):
        """Stop the processing"""
        if self.process and self.process.poll() is None:
            if messagebox.askyesno("Confirm", "Stop processing? You can resume later with the Resume option."):
                self.process.terminate()
                self.log_message("Processing stopped by user")
                self.processing_complete()


def main():
    root = tk.Tk()
    app = ParkingReportGUI(root)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()