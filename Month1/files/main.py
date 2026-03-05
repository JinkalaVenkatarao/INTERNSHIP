"""
main.py - Personal Finance Manager
===================================
Entry point of the application.
Run this file to start the program:  python main.py

Project Structure:
    main.py           ← You are here (entry point)
    src/              ← All source modules
    data/             ← CSV data storage
    reports/          ← Exported reports (auto-created)
    docs/             ← Documentation
    tests/            ← Unit tests
"""

import sys
import os

# ── Add src/ to path so all modules resolve correctly ──────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR  = os.path.join(ROOT_DIR, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, ROOT_DIR)

# Override the data/reports dirs so file_manager uses root-level folders
os.environ["PFM_ROOT"] = ROOT_DIR

# ── Imports (after path setup) ─────────────────────────────────────────────────
from file_manager import load_expenses, create_backup, initialize_csv
from menu import (
    show_main_menu,
    menu_add_expense,
    menu_view_expenses,
    menu_search_filter,
    menu_edit_expense,
    menu_delete_expense,
    menu_reports,
    menu_backup_restore,
    menu_system_info,
)
from utils import Colors, colored, clear_screen, print_success, print_info


# ── Startup ────────────────────────────────────────────────────────────────────

def startup_banner():
    """Show welcome screen on launch."""
    clear_screen()
    print(colored("""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║                                                                    ║
  ║        💰  PERSONAL FINANCE MANAGER  💰                            ║
  ║              Track • Analyse • Save Smarter                        ║
  ║                                                                    ║
  ╚══════════════════════════════════════════════════════════════════════╝
""", Colors.CYAN + Colors.BOLD))
    print(colored("  Initialising system...", Colors.DIM))


def main():
    """Main program loop — runs until user selects Exit."""
    startup_banner()

    initialize_csv()                          # Create data file if missing
    expenses = load_expenses()                # Load all records into memory
    print_success(f"Loaded {len(expenses)} expense record(s).")

    # ── Menu loop ──────────────────────────────────────────────────────────────
    MENU_ACTIONS = {
        "1": lambda: menu_add_expense(expenses),
        "2": lambda: menu_view_expenses(expenses),
        "3": lambda: menu_search_filter(expenses),
        "4": lambda: menu_edit_expense(expenses),
        "5": lambda: menu_delete_expense(expenses),
        "6": lambda: menu_reports(expenses),
        "7": lambda: menu_backup_restore(expenses),
        "8": lambda: menu_system_info(expenses),
    }

    while True:
        choice = show_main_menu()

        if choice in MENU_ACTIONS:
            MENU_ACTIONS[choice]()
        elif choice == "0":
            # Auto-backup before quit
            if expenses:
                print_info("Creating automatic backup before exit...")
                path = create_backup()
                if path:
                    print_success(f"Backup saved: {path}")
            print(colored("""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║   Thank you for using Personal Finance Manager! Stay frugal! 💸    ║
  ╚══════════════════════════════════════════════════════════════════════╝
""", Colors.CYAN))
            sys.exit(0)
        else:
            print(colored("  ✗ Invalid choice. Enter a number from 0 to 8.", Colors.RED))
            import time; time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n\n  Goodbye! (Ctrl+C pressed)\n", Colors.YELLOW))
        sys.exit(0)
