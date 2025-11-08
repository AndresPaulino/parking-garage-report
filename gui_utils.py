"""
GUI Utilities for Parking Report Automation
Handles preferences management and credential encryption
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
import base64
import hashlib


class PreferencesManager:
    """Manages user preferences and encrypted credentials"""

    def __init__(self, prefs_file: str = "preferences.json"):
        self.prefs_file = prefs_file
        self.key_file = ".key"  # Hidden file for encryption key
        self._cipher = None
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize or load encryption key"""
        if os.path.exists(self.key_file):
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Make key file hidden on Unix-like systems
            if os.name != 'nt':  # Not Windows
                os.chmod(self.key_file, 0o600)

        self._cipher = Fernet(key)

    def encrypt_credentials(self, username: str, password: str) -> str:
        """
        Encrypt username and password

        Args:
            username: Parkonect username
            password: Parkonect password

        Returns:
            Encrypted credentials as base64 string
        """
        credentials = f"{username}:{password}"
        encrypted = self._cipher.encrypt(credentials.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_credentials(self, encrypted_data: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Decrypt username and password

        Args:
            encrypted_data: Base64 encoded encrypted credentials

        Returns:
            Tuple of (username, password) or (None, None) if decryption fails
        """
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = self._cipher.decrypt(encrypted).decode()
            username, password = decrypted.split(':', 1)
            return username, password
        except Exception as e:
            print(f"Failed to decrypt credentials: {e}")
            return None, None

    def save_preferences(self, prefs: Dict) -> bool:
        """
        Save preferences to JSON file

        Args:
            prefs: Dictionary of preferences to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(prefs, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save preferences: {e}")
            return False

    def load_preferences(self) -> Dict:
        """
        Load preferences from JSON file

        Returns:
            Dictionary of preferences, or empty dict if file doesn't exist
        """
        if not os.path.exists(self.prefs_file):
            return self._get_default_preferences()

        try:
            with open(self.prefs_file, 'r') as f:
                prefs = json.load(f)
            # Merge with defaults to ensure all keys exist
            default_prefs = self._get_default_preferences()
            default_prefs.update(prefs)
            return default_prefs
        except Exception as e:
            print(f"Failed to load preferences: {e}")
            return self._get_default_preferences()

    def _get_default_preferences(self) -> Dict:
        """Get default preferences"""
        from datetime import datetime
        now = datetime.now()

        return {
            "remember_credentials": False,
            "encrypted_credentials": "",
            "selected_garage": "",
            "year": now.year,
            "month": now.month,
            "start_day": 1,
            "end_day": 31,
            "output_file": "parking_reports.xlsx",
            "batch_size": 25,
            "headless": False,
            "resume": False,
            "email_enabled": False,
            "email_to": "",
            "email_from": "",
            "save_preferences": False,
            "last_run": None
        }

    def clear_credentials(self) -> bool:
        """Clear saved credentials from preferences"""
        try:
            prefs = self.load_preferences()
            prefs["remember_credentials"] = False
            prefs["encrypted_credentials"] = ""
            return self.save_preferences(prefs)
        except Exception as e:
            print(f"Failed to clear credentials: {e}")
            return False


class GarageConfig:
    """Manages garage configurations"""

    @staticmethod
    def get_garage_list() -> Dict[str, Dict[str, str]]:
        """
        Get list of available garages with their configuration

        Returns:
            Dictionary mapping garage names to their gid/rpt values
            Format: {"Garage Name": {"gid": "1239", "rpt": "27"}}
        """
        # Placeholder for now - will be populated with actual garage data
        # User will provide the 4 garage URLs later
        return {
            "Garage 1 (Default)": {
                "gid": "1239",
                "rpt": "27",
                "url": "https://secure.parkonect.com"
            }
            # Additional garages will be added here when provided by user
        }

    @staticmethod
    def get_garage_names() -> list:
        """Get list of garage names for dropdown"""
        garages = GarageConfig.get_garage_list()
        return list(garages.keys())

    @staticmethod
    def get_garage_config(garage_name: str) -> Optional[Dict[str, str]]:
        """
        Get configuration for specific garage

        Args:
            garage_name: Name of the garage

        Returns:
            Dictionary with gid, rpt, and url, or None if not found
        """
        garages = GarageConfig.get_garage_list()
        return garages.get(garage_name)

    @staticmethod
    def add_garage(name: str, gid: str, rpt: str, url: str,
                   config_file: str = "garage_config.json") -> bool:
        """
        Add a new garage configuration

        Args:
            name: Display name for the garage
            gid: Garage ID parameter
            rpt: Report type parameter
            url: Base URL for the garage
            config_file: Path to garage configuration file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing config
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    garages = json.load(f)
            else:
                garages = GarageConfig.get_garage_list()

            # Add new garage
            garages[name] = {
                "gid": gid,
                "rpt": rpt,
                "url": url
            }

            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(garages, f, indent=2)

            return True
        except Exception as e:
            print(f"Failed to add garage: {e}")
            return False


def validate_credentials(username: str, password: str) -> Tuple[bool, str]:
    """
    Validate username and password format

    Args:
        username: Username to validate
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username cannot be empty"

    if not password or not password.strip():
        return False, "Password cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(password) < 3:
        return False, "Password must be at least 3 characters"

    return True, ""


def validate_date_range(year: int, month: int, start_day: int, end_day: int) -> Tuple[bool, str]:
    """
    Validate date range

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        start_day: Starting day of month
        end_day: Ending day of month

    Returns:
        Tuple of (is_valid, error_message)
    """
    from datetime import datetime

    # Validate year
    current_year = datetime.now().year
    if year < 2020 or year > current_year + 1:
        return False, f"Year must be between 2020 and {current_year + 1}"

    # Validate month
    if month < 1 or month > 12:
        return False, "Month must be between 1 and 12"

    # Validate start_day
    if start_day < 1 or start_day > 31:
        return False, "Start day must be between 1 and 31"

    # Validate end_day
    if end_day < 1 or end_day > 31:
        return False, "End day must be between 1 and 31"

    # Validate start_day <= end_day
    if start_day > end_day:
        return False, "Start day must be less than or equal to end day"

    # Validate day exists in month
    try:
        datetime(year, month, start_day)
        datetime(year, month, end_day)
    except ValueError:
        return False, f"Invalid date for {year}-{month:02d}"

    return True, ""


def get_last_day_of_month(year: int, month: int) -> int:
    """
    Get the last day of a given month

    Args:
        year: Year
        month: Month (1-12)

    Returns:
        Last day of the month (28-31)
    """
    import calendar
    return calendar.monthrange(year, month)[1]


if __name__ == "__main__":
    # Test encryption
    print("Testing PreferencesManager...")
    pm = PreferencesManager()

    # Test credential encryption
    username = "testuser"
    password = "testpass123"
    encrypted = pm.encrypt_credentials(username, password)
    print(f"Encrypted: {encrypted[:50]}...")

    decrypted_user, decrypted_pass = pm.decrypt_credentials(encrypted)
    print(f"Decrypted: {decrypted_user} / {decrypted_pass}")
    assert decrypted_user == username
    assert decrypted_pass == password
    print("✓ Encryption/decryption working")

    # Test preferences
    test_prefs = pm._get_default_preferences()
    test_prefs["remember_credentials"] = True
    test_prefs["encrypted_credentials"] = encrypted

    pm.save_preferences(test_prefs)
    print("✓ Preferences saved")

    loaded_prefs = pm.load_preferences()
    assert loaded_prefs["remember_credentials"] == True
    print("✓ Preferences loaded")

    # Test validation
    valid, msg = validate_credentials("user", "pass")
    assert valid
    print("✓ Credential validation working")

    valid, msg = validate_date_range(2025, 10, 1, 31)
    assert valid
    print("✓ Date validation working")

    print("\nAll tests passed!")
