"""
utils.py - Utility functions and validation helpers for Personal Finance Manager
"""

import os
import re
from datetime import datetime, date
from expense import Expense


# ─── Terminal Styling ──────────────────────────────────────────────────────────

class Colors:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"

def colored(text: str, color: str) -> str:
    """Wrap text in a color code."""
    return f"{color}{text}{Colors.RESET}"

def success(msg: str) -> str:
    return colored(f"  ✓ {msg}", Colors.GREEN)

def error(msg: str) -> str:
    return colored(f"  ✗ {msg}", Colors.RED)

def warning(msg: str) -> str:
    return colored(f"  ⚠ {msg}", Colors.YELLOW)

def info(msg: str) -> str:
    return colored(f"  ℹ {msg}", Colors.CYAN)

def print_success(msg: str): print(success(msg))
def print_error(msg: str):   print(error(msg))
def print_warning(msg: str): print(warning(msg))
def print_info(msg: str):    print(info(msg))


# ─── Display Helpers ──────────────────────────────────────────────────────────

def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_divider(char: str = "─", width: int = 70, color: str = Colors.DIM):
    """Print a horizontal divider line."""
    print(colored(char * width, color))


def print_header(title: str, width: int = 70):
    """Print a styled section header."""
    print()
    print(colored("╔" + "═" * (width - 2) + "╗", Colors.CYAN))
    print(colored("║" + title.center(width - 2) + "║", Colors.CYAN + Colors.BOLD))
    print(colored("╚" + "═" * (width - 2) + "╝", Colors.CYAN))


def print_subheader(title: str, width: int = 70):
    """Print a smaller sub-header."""
    print()
    print(colored(f"  {'─' * 4} {title} {'─' * max(0, width - len(title) - 8)}", Colors.BLUE + Colors.BOLD))


def press_enter_to_continue():
    """Pause and wait for the user to press Enter."""
    print()
    input(colored("  Press Enter to continue...", Colors.DIM))


# ─── Input Validation ─────────────────────────────────────────────────────────

def get_valid_float(prompt: str, min_val: float = 0.01, max_val: float = 10_000_000) -> float:
    """
    Prompt user for a valid float within range.

    Args:
        prompt: Display prompt
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value

    Returns:
        float: Validated float value
    """
    while True:
        try:
            raw = input(prompt).strip()
            if not raw:
                print_error("Input cannot be empty.")
                continue
            value = float(raw)
            if value < min_val:
                print_error(f"Value must be at least {min_val:.2f}.")
            elif value > max_val:
                print_error(f"Value cannot exceed {max_val:,.2f}.")
            else:
                return round(value, 2)
        except ValueError:
            print_error("Please enter a valid number (e.g., 250 or 1500.50).")


def get_valid_int(prompt: str, min_val: int = 1, max_val: int = 9999) -> int:
    """Prompt user for a valid integer within range."""
    while True:
        try:
            raw = input(prompt).strip()
            if not raw:
                print_error("Input cannot be empty.")
                continue
            value = int(raw)
            if min_val <= value <= max_val:
                return value
            print_error(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print_error("Please enter a whole number.")


def get_valid_date(prompt: str, allow_today: bool = True) -> str:
    """
    Prompt user for a valid date string.

    Returns:
        str: Date in YYYY-MM-DD format
    """
    today_str = date.today().strftime("%Y-%m-%d")
    while True:
        raw = input(prompt).strip()
        if not raw and allow_today:
            return today_str
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d")
            if parsed.date() > date.today():
                print_warning("Date is in the future. Are you sure? (y/n): ")
                if input("  → ").strip().lower() != "y":
                    continue
            return raw
        except ValueError:
            print_error("Invalid date. Use format YYYY-MM-DD (e.g., 2024-03-15).")


def get_valid_category(prompt: str) -> str:
    """Display category menu and return chosen category."""
    categories = Expense.VALID_CATEGORIES
    print()
    print(colored("  Select a category:", Colors.BOLD))
    for i, cat in enumerate(categories, 1):
        print(f"    {colored(str(i) + '.', Colors.CYAN)} {cat}")
    while True:
        choice = input(prompt).strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                return categories[idx]
            print_error(f"Enter a number between 1 and {len(categories)}.")
        except ValueError:
            # Allow typing the category name directly
            if choice in categories:
                return choice
            print_error("Please enter the number of your chosen category.")


def get_valid_description(prompt: str) -> str:
    """Prompt user for a non-empty description under 100 characters."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print_error("Description cannot be empty.")
        elif len(raw) > 100:
            print_error(f"Too long ({len(raw)} chars). Max 100 characters.")
        else:
            return raw


def get_yes_no(prompt: str) -> bool:
    """Ask a yes/no question and return True for yes."""
    while True:
        raw = input(f"{prompt} (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print_error("Please enter 'y' or 'n'.")


def get_date_range(prompt_start: str = None, prompt_end: str = None) -> tuple[str, str]:
    """
    Ask for a start and end date range.

    Returns:
        tuple: (start_date, end_date) both as YYYY-MM-DD strings
    """
    print_info("Leave blank to use default (start of year / today).")
    today = date.today()
    default_start = date(today.year, 1, 1).strftime("%Y-%m-%d")
    default_end = today.strftime("%Y-%m-%d")

    while True:
        start_raw = input(prompt_start or f"  Start date [{default_start}]: ").strip()
        start = start_raw if start_raw else default_start
        try:
            datetime.strptime(start, "%Y-%m-%d")
            break
        except ValueError:
            print_error("Invalid start date. Use YYYY-MM-DD.")

    while True:
        end_raw = input(prompt_end or f"  End date   [{default_end}]: ").strip()
        end = end_raw if end_raw else default_end
        try:
            datetime.strptime(end, "%Y-%m-%d")
            if end < start:
                print_error("End date cannot be before start date.")
                continue
            break
        except ValueError:
            print_error("Invalid end date. Use YYYY-MM-DD.")

    return start, end


# ─── Formatting ───────────────────────────────────────────────────────────────

def format_currency(amount: float, symbol: str = "₹") -> str:
    """Format a float as a currency string with commas."""
    return f"{symbol}{amount:>12,.2f}"


def format_percentage(value: float, total: float) -> str:
    """Return a percentage string, safe against division by zero."""
    if total == 0:
        return "   0.0%"
    pct = (value / total) * 100
    return f"{pct:>6.1f}%"


def truncate(text: str, max_len: int = 30) -> str:
    """Truncate a string to max_len with ellipsis."""
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def bar_chart(value: float, max_val: float, width: int = 20, fill: str = "█", empty: str = "░") -> str:
    """Generate a simple ASCII bar chart."""
    if max_val == 0:
        return empty * width
    filled = int((value / max_val) * width)
    return fill * filled + empty * (width - filled)
