"""
Parking Report Automation - GUI Application
User-friendly desktop interface for running parking reports
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import queue

from gui_utils import (
    PreferencesManager,
    GarageConfig,
    validate_credentials,
    validate_date_range,
    get_last_day_of_month
)


class ParkingReportGUI:
    """Main GUI application for parking report automation"""

    def __init__(self, root):
        self.root = root
        self.root.title("Parking Report Automation")
        self.root.geometry("800x900")
        self.root.resizable(True, True)

        # Initialize preferences manager
        self.prefs_manager = PreferencesManager()

        # Process tracking
        self.process = None
        self.is_running = False
        self.output_queue = queue.Queue()

        # Create GUI elements
        self.create_widgets()

        # Load saved preferences
        self.load_preferences()

        # Start output monitor
        self.monitor_output()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        row = 0

        # Title
        title_label = ttk.Label(main_frame, text="Parking Report Automation",
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1

        # === Login Credentials Section ===
        cred_frame = ttk.LabelFrame(main_frame, text="Login Credentials", padding="10")
        cred_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        cred_frame.columnconfigure(1, weight=1)
        row += 1

        ttk.Label(cred_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(cred_frame, textvariable=self.username_var, width=40)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(cred_frame, textvariable=self.password_var, show="*", width=40)
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        self.remember_creds_var = tk.BooleanVar()
        self.remember_creds_cb = ttk.Checkbutton(cred_frame, text="Remember credentials (encrypted)",
                                                 variable=self.remember_creds_var)
        self.remember_creds_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # === Garage Selection Section ===
        garage_frame = ttk.LabelFrame(main_frame, text="Garage Selection", padding="10")
        garage_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        garage_frame.columnconfigure(1, weight=1)
        row += 1

        ttk.Label(garage_frame, text="Garage:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.garage_var = tk.StringVar()
        self.garage_combo = ttk.Combobox(garage_frame, textvariable=self.garage_var,
                                        values=GarageConfig.get_garage_names(),
                                        state="readonly", width=37)
        self.garage_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        if self.garage_combo['values']:
            self.garage_combo.current(0)

        # === Date Range Section ===
        date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="10")
        date_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)
        row += 1

        now = datetime.now()

        # Year and Month
        ttk.Label(date_frame, text="Year:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.IntVar(value=now.year)
        self.year_spin = ttk.Spinbox(date_frame, from_=2020, to=now.year+1,
                                     textvariable=self.year_var, width=10,
                                     command=self.on_date_change)
        self.year_spin.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 20))

        ttk.Label(date_frame, text="Month:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.month_var = tk.IntVar(value=now.month)
        self.month_spin = ttk.Spinbox(date_frame, from_=1, to=12,
                                      textvariable=self.month_var, width=10,
                                      command=self.on_date_change)
        self.month_spin.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(10, 0))

        # Start and End Day
        ttk.Label(date_frame, text="Start Day:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_day_var = tk.IntVar(value=1)
        self.start_day_spin = ttk.Spinbox(date_frame, from_=1, to=31,
                                          textvariable=self.start_day_var, width=10)
        self.start_day_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 20))

        ttk.Label(date_frame, text="End Day:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.end_day_var = tk.IntVar(value=get_last_day_of_month(now.year, now.month))
        self.end_day_spin = ttk.Spinbox(date_frame, from_=1, to=31,
                                        textvariable=self.end_day_var, width=10)
        self.end_day_spin.grid(row=1, column=3, sticky=tk.W, pady=5, padx=(10, 0))

        # === Options Section ===
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        row += 1

        # Output file
        ttk.Label(options_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        output_subframe = ttk.Frame(options_frame)
        output_subframe.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        output_subframe.columnconfigure(0, weight=1)

        self.output_var = tk.StringVar(value="parking_reports.xlsx")
        self.output_entry = ttk.Entry(output_subframe, textvariable=self.output_var)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.browse_btn = ttk.Button(output_subframe, text="Browse...", command=self.browse_output_file)
        self.browse_btn.grid(row=0, column=1)

        # Batch size
        ttk.Label(options_frame, text="Batch Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.IntVar(value=25)
        self.batch_size_spin = ttk.Spinbox(options_frame, from_=1, to=100,
                                           textvariable=self.batch_size_var, width=10)
        self.batch_size_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Checkboxes
        self.headless_var = tk.BooleanVar(value=False)
        self.headless_cb = ttk.Checkbutton(options_frame, text="Run in headless mode (no browser window)",
                                          variable=self.headless_var)
        self.headless_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        self.resume_var = tk.BooleanVar(value=False)
        self.resume_cb = ttk.Checkbutton(options_frame, text="Resume from previous run",
                                        variable=self.resume_var)
        self.resume_cb.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # === Email Notifications Section (Collapsible) ===
        self.email_expanded = tk.BooleanVar(value=False)
        email_frame = ttk.LabelFrame(main_frame, text="Email Notifications (Optional)", padding="10")
        email_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        email_frame.columnconfigure(1, weight=1)
        row += 1

        self.email_enabled_var = tk.BooleanVar(value=False)
        self.email_enabled_cb = ttk.Checkbutton(email_frame, text="Enable email notifications",
                                               variable=self.email_enabled_var,
                                               command=self.toggle_email_fields)
        self.email_enabled_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        ttk.Label(email_frame, text="To:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_to_var = tk.StringVar()
        self.email_to_entry = ttk.Entry(email_frame, textvariable=self.email_to_var, state="disabled")
        self.email_to_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        ttk.Label(email_frame, text="From:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_from_var = tk.StringVar()
        self.email_from_entry = ttk.Entry(email_frame, textvariable=self.email_from_var, state="disabled")
        self.email_from_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        ttk.Label(email_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.email_password_var = tk.StringVar()
        self.email_password_entry = ttk.Entry(email_frame, textvariable=self.email_password_var,
                                             show="*", state="disabled")
        self.email_password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # === Advanced Section (Collapsible) ===
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        advanced_frame.columnconfigure(1, weight=1)
        row += 1

        ttk.Label(advanced_frame, text="Specific Accounts:").grid(row=0, column=0, sticky=(tk.W, tk.N), pady=5)
        self.accounts_text = tk.Text(advanced_frame, height=3, width=40)
        self.accounts_text.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        ttk.Label(advanced_frame, text="(One per line, leave empty for all)",
                 font=('Helvetica', 8, 'italic')).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # === Save Preferences ===
        self.save_prefs_var = tk.BooleanVar(value=False)
        self.save_prefs_cb = ttk.Checkbutton(main_frame, text="Save preferences for next time",
                                            variable=self.save_prefs_var)
        self.save_prefs_cb.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1

        # === Control Buttons ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1

        self.start_btn = ttk.Button(button_frame, text="Start Processing", command=self.start_processing,
                                    style="Accent.TButton")
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_processing,
                                   state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.clear_btn = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.grid(row=0, column=2, padx=5)

        # === Progress Section ===
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(row, weight=1)
        row += 1

        # Status label
        self.status_var = tk.StringVar(value="Ready to start")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var,
                                     font=('Helvetica', 10, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Log viewer
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=15, wrap=tk.WORD,
                                                  state="disabled", bg="black", fg="lightgreen",
                                                  font=('Courier', 9))
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def on_date_change(self):
        """Handle year/month change to update end day"""
        try:
            year = self.year_var.get()
            month = self.month_var.get()
            last_day = get_last_day_of_month(year, month)

            # Update end day spinbox max value
            self.end_day_spin.configure(to=last_day)

            # If current end day exceeds last day, adjust it
            if self.end_day_var.get() > last_day:
                self.end_day_var.set(last_day)
        except:
            pass

    def toggle_email_fields(self):
        """Enable/disable email fields based on checkbox"""
        state = "normal" if self.email_enabled_var.get() else "disabled"
        self.email_to_entry.configure(state=state)
        self.email_from_entry.configure(state=state)
        self.email_password_entry.configure(state=state)

    def browse_output_file(self):
        """Open file dialog to select output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=self.output_var.get()
        )
        if filename:
            self.output_var.set(filename)

    def load_preferences(self):
        """Load saved preferences"""
        prefs = self.prefs_manager.load_preferences()

        # Load credentials if remembered
        if prefs.get("remember_credentials") and prefs.get("encrypted_credentials"):
            username, password = self.prefs_manager.decrypt_credentials(
                prefs["encrypted_credentials"]
            )
            if username and password:
                self.username_var.set(username)
                self.password_var.set(password)
                self.remember_creds_var.set(True)

        # Load other preferences
        if prefs.get("selected_garage"):
            self.garage_var.set(prefs["selected_garage"])

        self.year_var.set(prefs.get("year", datetime.now().year))
        self.month_var.set(prefs.get("month", datetime.now().month))
        self.start_day_var.set(prefs.get("start_day", 1))
        self.end_day_var.set(prefs.get("end_day", 31))
        self.output_var.set(prefs.get("output_file", "parking_reports.xlsx"))
        self.batch_size_var.set(prefs.get("batch_size", 25))
        self.headless_var.set(prefs.get("headless", False))
        self.resume_var.set(prefs.get("resume", False))

        # Email preferences
        if prefs.get("email_enabled"):
            self.email_enabled_var.set(True)
            self.email_to_var.set(prefs.get("email_to", ""))
            self.email_from_var.set(prefs.get("email_from", ""))
            self.toggle_email_fields()

        self.save_prefs_var.set(prefs.get("save_preferences", False))

    def save_preferences_to_file(self):
        """Save current preferences to file"""
        prefs = {
            "remember_credentials": self.remember_creds_var.get(),
            "encrypted_credentials": "",
            "selected_garage": self.garage_var.get(),
            "year": self.year_var.get(),
            "month": self.month_var.get(),
            "start_day": self.start_day_var.get(),
            "end_day": self.end_day_var.get(),
            "output_file": self.output_var.get(),
            "batch_size": self.batch_size_var.get(),
            "headless": self.headless_var.get(),
            "resume": self.resume_var.get(),
            "email_enabled": self.email_enabled_var.get(),
            "email_to": self.email_to_var.get(),
            "email_from": self.email_from_var.get(),
            "save_preferences": self.save_prefs_var.get(),
            "last_run": datetime.now().isoformat()
        }

        # Encrypt and save credentials if requested
        if self.remember_creds_var.get():
            username = self.username_var.get()
            password = self.password_var.get()
            if username and password:
                prefs["encrypted_credentials"] = self.prefs_manager.encrypt_credentials(
                    username, password
                )

        self.prefs_manager.save_preferences(prefs)

    def validate_inputs(self) -> bool:
        """Validate all input fields"""
        # Validate credentials
        username = self.username_var.get()
        password = self.password_var.get()
        valid, msg = validate_credentials(username, password)
        if not valid:
            messagebox.showerror("Invalid Input", msg)
            return False

        # Validate date range
        year = self.year_var.get()
        month = self.month_var.get()
        start_day = self.start_day_var.get()
        end_day = self.end_day_var.get()
        valid, msg = validate_date_range(year, month, start_day, end_day)
        if not valid:
            messagebox.showerror("Invalid Input", msg)
            return False

        # Validate garage selection
        if not self.garage_var.get():
            messagebox.showerror("Invalid Input", "Please select a garage")
            return False

        # Validate email if enabled
        if self.email_enabled_var.get():
            if not self.email_to_var.get() or not self.email_from_var.get():
                messagebox.showerror("Invalid Input", "Email addresses cannot be empty when email is enabled")
                return False
            if not self.email_password_var.get():
                messagebox.showerror("Invalid Input", "Email password cannot be empty when email is enabled")
                return False

        return True

    def build_command(self) -> list:
        """Build command line arguments for the automation script"""
        script_path = Path(__file__).parent / "enhanced_parking_automation.py"

        cmd = [
            sys.executable,
            str(script_path),
            "--username", self.username_var.get(),
            "--password", self.password_var.get(),
            "--year", str(self.year_var.get()),
            "--month", str(self.month_var.get()),
            "--start-day", str(self.start_day_var.get()),
            "--end-day", str(self.end_day_var.get()),
            "--output", self.output_var.get(),
            "--batch-size", str(self.batch_size_var.get())
        ]

        if self.headless_var.get():
            cmd.append("--headless")

        if self.resume_var.get():
            cmd.append("--resume")

        if self.email_enabled_var.get():
            cmd.extend([
                "--email-to", self.email_to_var.get(),
                "--email-from", self.email_from_var.get(),
                "--email-password", self.email_password_var.get()
            ])

        # Handle specific accounts
        accounts_text = self.accounts_text.get("1.0", tk.END).strip()
        if accounts_text:
            accounts = [acc.strip() for acc in accounts_text.split('\n') if acc.strip()]
            if accounts:
                cmd.append("--accounts")
                cmd.extend(accounts)

        return cmd

    def start_processing(self):
        """Start the automation process"""
        # Validate inputs
        if not self.validate_inputs():
            return

        # Save preferences if requested
        if self.save_prefs_var.get():
            self.save_preferences_to_file()

        # Disable start button, enable stop button
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.is_running = True

        # Update status
        self.status_var.set("Starting automation...")
        self.log_message("Building command...")

        # Build command
        cmd = self.build_command()
        self.log_message(f"Command: {' '.join(cmd)}")

        # Start process in background thread
        thread = threading.Thread(target=self.run_process, args=(cmd,), daemon=True)
        thread.start()

    def run_process(self, cmd: list):
        """Run the automation process"""
        try:
            self.status_var.set("Running automation...")

            # Start subprocess
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_queue.put(('log', line.rstrip()))
                if not self.is_running:
                    break

            # Wait for process to complete
            self.process.wait()

            # Check exit code
            if self.process.returncode == 0:
                self.output_queue.put(('status', 'Completed successfully!'))
                self.output_queue.put(('log', '\n=== Process completed successfully ==='))
            else:
                self.output_queue.put(('status', f'Process failed with exit code {self.process.returncode}'))
                self.output_queue.put(('log', f'\n=== Process failed with exit code {self.process.returncode} ==='))

        except Exception as e:
            self.output_queue.put(('status', f'Error: {str(e)}'))
            self.output_queue.put(('log', f'\n=== Error: {str(e)} ==='))

        finally:
            self.output_queue.put(('done', None))

    def stop_processing(self):
        """Stop the automation process"""
        if self.process and self.is_running:
            self.status_var.set("Stopping...")
            self.log_message("\n=== Stopping process ===")
            self.is_running = False

            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

            self.log_message("Process stopped by user")

    def monitor_output(self):
        """Monitor output queue and update GUI"""
        try:
            while True:
                msg_type, msg = self.output_queue.get_nowait()

                if msg_type == 'log':
                    self.log_message(msg)
                elif msg_type == 'status':
                    self.status_var.set(msg)
                elif msg_type == 'done':
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.is_running = False

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.monitor_output)

    def log_message(self, message: str):
        """Add message to log viewer"""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def clear_log(self):
        """Clear the log viewer"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self.status_var.set("Ready to start")


def main():
    """Main entry point"""
    root = tk.Tk()

    # Set theme (try to use modern theme if available)
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'aqua' in available_themes:
            style.theme_use('aqua')
        elif 'clam' in available_themes:
            style.theme_use('clam')
    except:
        pass

    # Create GUI
    app = ParkingReportGUI(root)

    # Run event loop
    root.mainloop()


if __name__ == "__main__":
    main()
