"""
file_manager.py - CSV file operations for Personal Finance Manager
Handles all data persistence: read, write, backup, restore.
"""

import csv
import os
import shutil
from datetime import datetime
from expense import Expense

# File paths — PFM_ROOT is set by main.py; fallback to src's parent
_ROOT       = os.environ.get("PFM_ROOT", os.path.dirname(os.path.dirname(__file__)))
DATA_DIR    = os.path.join(_ROOT, "data")
REPORTS_DIR = os.path.join(_ROOT, "reports")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.csv")
BACKUP_DIR  = os.path.join(DATA_DIR, "backups")

CSV_FIELDNAMES = ["id", "amount", "category", "date", "description"]


def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def initialize_csv():
    """Create the CSV file with headers if it doesn't exist."""
    ensure_directories()
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()


def load_expenses() -> list[Expense]:
    """
    Load all expenses from the CSV file.

    Returns:
        list[Expense]: List of Expense objects
    """
    initialize_csv()
    expenses = []
    try:
        with open(EXPENSES_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    expense = Expense.from_dict(row)
                    expenses.append(expense)
                except (ValueError, KeyError) as e:
                    print(f"  ⚠ Skipping corrupted row: {e}")
    except FileNotFoundError:
        pass  # Will be created on next save
    except Exception as e:
        print(f"  ✗ Error reading data file: {e}")
    return expenses


def save_expenses(expenses: list[Expense]) -> bool:
    """
    Save all expenses to the CSV file (overwrites existing data).

    Args:
        expenses: List of Expense objects to save

    Returns:
        bool: True if successful, False otherwise
    """
    ensure_directories()
    try:
        with open(EXPENSES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            for expense in expenses:
                writer.writerow(expense.to_dict())
        return True
    except Exception as e:
        print(f"  ✗ Error saving data: {e}")
        return False


def add_expense(expense: Expense) -> bool:
    """
    Append a single expense to the CSV file.

    Args:
        expense: Expense object to add

    Returns:
        bool: True if successful
    """
    initialize_csv()
    try:
        with open(EXPENSES_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writerow(expense.to_dict())
        return True
    except Exception as e:
        print(f"  ✗ Error adding expense: {e}")
        return False


def get_next_id(expenses: list[Expense]) -> int:
    """Generate the next unique ID for a new expense."""
    if not expenses:
        return 1
    return max(e.expense_id for e in expenses if e.expense_id is not None) + 1


def create_backup() -> str:
    """
    Create a timestamped backup of the expenses CSV.

    Returns:
        str: Path to the backup file, or empty string on failure
    """
    ensure_directories()
    if not os.path.exists(EXPENSES_FILE):
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"expenses_backup_{timestamp}.csv")
    try:
        shutil.copy2(EXPENSES_FILE, backup_path)
        return backup_path
    except Exception as e:
        print(f"  ✗ Backup failed: {e}")
        return ""


def list_backups() -> list[str]:
    """
    List all available backup files.

    Returns:
        list[str]: List of backup file paths sorted by date (newest first)
    """
    ensure_directories()
    try:
        files = [
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
            if f.startswith("expenses_backup_") and f.endswith(".csv")
        ]
        return sorted(files, reverse=True)
    except Exception:
        return []


def restore_backup(backup_path: str) -> bool:
    """
    Restore expenses from a backup file.

    Args:
        backup_path: Full path to the backup file

    Returns:
        bool: True if successful
    """
    if not os.path.exists(backup_path):
        print(f"  ✗ Backup file not found: {backup_path}")
        return False
    try:
        # Create a safety backup of current data before restoring
        if os.path.exists(EXPENSES_FILE):
            safety_path = os.path.join(BACKUP_DIR, "pre_restore_safety.csv")
            shutil.copy2(EXPENSES_FILE, safety_path)
        shutil.copy2(backup_path, EXPENSES_FILE)
        return True
    except Exception as e:
        print(f"  ✗ Restore failed: {e}")
        return False


def save_report(content: str, report_name: str) -> str:
    """
    Save a report to the reports directory.

    Args:
        content: Report text content
        report_name: Base name for the report file

    Returns:
        str: Full path to saved report
    """
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_name}_{timestamp}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"  ✗ Could not save report: {e}")
        return ""


def get_file_stats() -> dict:
    """Get statistics about the data file."""
    stats = {
        "file_exists": os.path.exists(EXPENSES_FILE),
        "file_size": 0,
        "backup_count": len(list_backups()),
        "last_modified": "N/A"
    }
    if stats["file_exists"]:
        stats["file_size"] = os.path.getsize(EXPENSES_FILE)
        mtime = os.path.getmtime(EXPENSES_FILE)
        stats["last_modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    return stats
