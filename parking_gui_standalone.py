"""
parking_gui_standalone.py - FIXED VERSION
No infinite loop when compiled to exe
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
from datetime import datetime
import sys
import os
import json

class ParkingReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Report Generator")
        self.root.geometry("650x750")
        
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
        self.accounts_var = tk.StringVar()
        
        self.process = None
        self.selection_mode = tk.StringVar(value="all")
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI elements"""
        
        # Title
        title_label = tk.Label(self.root, text="Parking Report Generator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
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
        
        tk.Label(date_frame, text="(Leave empty for full month)", 
                font=("Arial", 8, "italic")).grid(row=4, column=0, columnspan=2, pady=2)
        
        # Account Selection Frame
        account_frame = tk.LabelFrame(self.root, text="Account Selection", padx=20, pady=10)
        account_frame.pack(padx=20, pady=10, fill="x")
        
        # Radio buttons for selection mode
        tk.Radiobutton(account_frame, text="Process ALL accounts (600+)", 
                      variable=self.selection_mode, value="all",
                      command=self.toggle_account_entry,
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(account_frame, text="Process specific accounts only", 
                      variable=self.selection_mode, value="specific",
                      command=self.toggle_account_entry,
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        
        # Account entry frame
        self.account_entry_frame = tk.Frame(account_frame)
        self.account_entry_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(self.account_entry_frame, text="Enter account names (comma-separated):").pack(anchor="w")
        self.account_entry = tk.Entry(self.account_entry_frame, textvariable=self.accounts_var, 
                                      width=50, state="disabled")
        self.account_entry.pack(anchor="w", pady=2)
        
        tk.Label(self.account_entry_frame, 
                text="Example: 50 EGGS HOSPITALITY GROUP, ACNE STUDIOS", 
                font=("Arial", 8, "italic")).pack(anchor="w")
        
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
            self.accounts_var.set("")  # Clear the field
            self.info_label.config(text="Will process ALL accounts (600+)")
        else:
            self.account_entry.config(state="normal")
            self.info_label.config(text="Will process only specified accounts")
            
    def log_message(self, message):
        """Add message to log window"""
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def get_python_executable(self):
        """Get the correct Python executable, avoiding infinite loops"""
        # Check if we're running as a frozen exe
        if getattr(sys, 'frozen', False):
            # We're running as an exe, need to find actual Python
            
            # Try to find Python in PATH
            import shutil
            python_exe = shutil.which('python')
            if python_exe:
                self.log_message(f"Found Python at: {python_exe}")
                return python_exe
            
            # Try common Python locations
            common_paths = [
                r"C:\Python39\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python311\python.exe",
                r"C:\Python312\python.exe",
                r"C:\Program Files\Python39\python.exe",
                r"C:\Program Files\Python310\python.exe",
                r"C:\Program Files\Python311\python.exe",
                r"C:\Program Files\Python312\python.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe",
            ]
            
            for path in common_paths:
                expanded_path = os.path.expandvars(path)
                if os.path.exists(expanded_path):
                    self.log_message(f"Found Python at: {expanded_path}")
                    return expanded_path
            
            # Python not found
            self.log_message("ERROR: Python not found in system!")
            self.log_message("Please ensure Python is installed and in PATH")
            messagebox.showerror("Python Not Found", 
                               "Python is required but not found!\n\n"
                               "Please install Python and add it to PATH,\n"
                               "or run the .py file directly instead of the .exe")
            return None
        else:
            # Running as a Python script, use sys.executable
            return sys.executable
        
    def start_processing(self):
        """Start the processing in a separate thread"""
        # Validate inputs
        if not self.username_var.get() or not self.password_var.get():
            messagebox.showerror("Error", "Please enter username and password")
            return
            
        # Check if specific accounts selected but none entered
        if self.selection_mode.get() == "specific" and not self.accounts_var.get().strip():
            messagebox.showerror("Error", "Please enter at least one account name or select 'Process ALL accounts'")
            return
        
        # Get Python executable
        python_exe = self.get_python_executable()
        if not python_exe:
            return
            
        # Disable start button, enable stop button
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="Processing...")
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=lambda: self.run_automation(python_exe))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def run_automation(self, python_exe):
        """Run the automation process using subprocess"""
        try:
            self.log_message("Starting automation...")
            
            # Check if automation script exists
            script_name = "enhanced_parking_automation.py"
            if not os.path.exists(script_name):
                # Try in the same directory as the exe
                if getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    script_path = os.path.join(exe_dir, script_name)
                    if not os.path.exists(script_path):
                        self.log_message(f"ERROR: {script_name} not found!")
                        self.log_message("Please ensure the script is in the same directory as this program")
                        return
                else:
                    self.log_message(f"ERROR: {script_name} not found!")
                    return
            
            # Build command
            cmd = [
                python_exe,  # Use the found Python executable
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
            
            if self.resume_var.get():
                cmd.append("--resume")
            
            # Add accounts only if specific mode is selected
            if self.selection_mode.get() == "specific":
                accounts = self.accounts_var.get().strip()
                if accounts:
                    cmd.append("--accounts")
                    # Split by comma and clean up
                    for account in accounts.split(','):
                        account = account.strip()
                        if account:
                            cmd.append(account)
                    self.log_message(f"Processing {len(accounts.split(','))} specific accounts")
            else:
                self.log_message("Processing ALL accounts")
            
            self.log_message("Command prepared, starting process...")
            
            # Create environment with proper encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Run the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    # Filter out certain noise from logs
                    line = line.strip()
                    if line and not line.startswith("Exception ignored"):
                        self.log_message(line)
            
            # Wait for process to complete
            self.process.wait()
            
            if self.process.returncode == 0:
                self.log_message("Processing completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Processing complete!\n\nReport saved to: {self.output_file_var.get()}"
                ))
            else:
                self.log_message(f"Process failed with return code: {self.process.returncode}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    "Processing failed. Check the log for details."
                ))
                
        except FileNotFoundError:
            error_msg = f"{script_name} not found. Please ensure it's in the same directory."
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            
        finally:
            # Re-enable buttons
            self.root.after(0, self.processing_complete)
            
    def processing_complete(self):
        """Reset GUI after processing completes"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Ready")
        self.process = None
        
    def stop_processing(self):
        """Stop the processing"""
        if self.process and self.process.poll() is None:
            if messagebox.askyesno("Confirm", "Stop processing? You can resume later if you have the resume option checked."):
                self.process.terminate()
                self.log_message("Processing stopped by user")
                self.processing_complete()


def main():
    # Safety check to prevent infinite loops
    if '--check-loop' in sys.argv:
        print("ERROR: Infinite loop detected! The GUI is calling itself.")
        print("This should not happen. Exiting to prevent system crash.")
        sys.exit(1)
    
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