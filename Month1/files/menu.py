"""
menu.py - Command-line interface and menu system for Personal Finance Manager
"""

from datetime import date
from expense import Expense
from file_manager import (
    load_expenses, save_expenses, add_expense, get_next_id,
    create_backup, list_backups, restore_backup, save_report, get_file_stats
)
from reports import (
    print_summary_report, print_expense_list, print_category_report,
    report_to_text, filter_by_date, filter_by_month, filter_by_category,
    category_totals, total_amount
)
from utils import (
    Colors, colored, clear_screen, print_header, print_subheader,
    print_divider, press_enter_to_continue, get_valid_float, get_valid_int,
    get_valid_date, get_valid_category, get_valid_description, get_yes_no,
    get_date_range, format_currency, print_success, print_error,
    print_warning, print_info, truncate
)


# ─── Main Menu ────────────────────────────────────────────────────────────────

def show_main_menu():
    """Display the main menu and return the user's choice."""
    clear_screen()
    today = date.today().strftime("%d %b %Y")
    print(colored("""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║          💰  PERSONAL FINANCE MANAGER  💰                           ║
  ║                 Your Smart Expense Tracker                          ║
  ╚══════════════════════════════════════════════════════════════════════╝""", Colors.CYAN + Colors.BOLD))
    print(colored(f"  📅 Today: {today}\n", Colors.DIM))

    menu_items = [
        ("1", "➕  Add New Expense",          Colors.GREEN),
        ("2", "📋  View All Expenses",         Colors.BLUE),
        ("3", "🔍  Search & Filter Expenses",  Colors.CYAN),
        ("4", "✏️   Edit an Expense",           Colors.YELLOW),
        ("5", "🗑️   Delete an Expense",         Colors.MAGENTA),
        ("6", "📊  Reports & Analytics",        Colors.GREEN),
        ("7", "💾  Backup & Restore Data",      Colors.BLUE),
        ("8", "ℹ️   System Info",               Colors.CYAN),
        ("0", "🚪  Exit",                       Colors.RED),
    ]
    for key, label, color in menu_items:
        print(f"    {colored(f'[{key}]', color + Colors.BOLD)} {label}")

    print()
    return input(colored("  ▶ Enter your choice: ", Colors.BOLD)).strip()


# ─── Add Expense ──────────────────────────────────────────────────────────────

def menu_add_expense(expenses: list[Expense]):
    """Handle adding a new expense."""
    print_header("Add New Expense")
    print(colored("  Fill in the details below (press Ctrl+C to cancel).\n", Colors.DIM))

    try:
        amount      = get_valid_float("  Amount (₹): ")
        category    = get_valid_category("  Category number: ")
        today_str   = date.today().strftime("%Y-%m-%d")
        print(f"\n  Date [leave blank for today: {today_str}]")
        expense_date = get_valid_date("  Date (YYYY-MM-DD): ")
        description = get_valid_description("  Description: ")

        expense = Expense(
            amount=amount,
            category=category,
            date=expense_date,
            description=description,
            expense_id=get_next_id(expenses)
        )

        print(f"\n  {colored('Preview:', Colors.BOLD)}")
        print(f"    Amount      : {colored(format_currency(amount), Colors.GREEN)}")
        print(f"    Category    : {colored(category, Colors.MAGENTA)}")
        print(f"    Date        : {expense_date}")
        print(f"    Description : {description}")
        print()

        if get_yes_no("  Save this expense?"):
            expenses.append(expense)
            if save_expenses(expenses):
                print_success(f"Expense #{expense.expense_id} saved successfully!")
            else:
                print_error("Failed to save. Please try again.")
        else:
            print_warning("Expense discarded.")

    except KeyboardInterrupt:
        print_warning("\nOperation cancelled.")
    except ValueError as e:
        print_error(str(e))

    press_enter_to_continue()


# ─── View Expenses ────────────────────────────────────────────────────────────

def menu_view_expenses(expenses: list[Expense]):
    """Show all expenses or paginated view."""
    if not expenses:
        print_header("View All Expenses")
        print(colored("\n  No expenses recorded yet. Add your first expense!\n", Colors.YELLOW))
        press_enter_to_continue()
        return

    sorted_exp = sorted(expenses, key=lambda e: e.date, reverse=True)
    PAGE_SIZE = 15
    total_pages = (len(sorted_exp) + PAGE_SIZE - 1) // PAGE_SIZE
    page = 0

    while True:
        clear_screen()
        start = page * PAGE_SIZE
        page_exp = sorted_exp[start:start + PAGE_SIZE]
        print_expense_list(page_exp, f"All Expenses  (Page {page + 1}/{total_pages})")
        print(colored(f"  Total across all expenses: {format_currency(total_amount(expenses))}", Colors.BOLD))
        print()

        nav = []
        if page > 0:
            nav.append("[P] Previous page")
        if page < total_pages - 1:
            nav.append("[N] Next page")
        nav.append("[B] Back to menu")

        print("  " + "   ".join(colored(n, Colors.CYAN) for n in nav))
        choice = input("\n  ▶ Choice: ").strip().upper()

        if choice == "N" and page < total_pages - 1:
            page += 1
        elif choice == "P" and page > 0:
            page -= 1
        elif choice == "B" or choice == "":
            break


# ─── Search & Filter ──────────────────────────────────────────────────────────

def menu_search_filter(expenses: list[Expense]):
    """Sub-menu for searching and filtering expenses."""
    while True:
        clear_screen()
        print_header("Search & Filter Expenses")
        options = [
            ("1", "Filter by Date Range"),
            ("2", "Filter by Category"),
            ("3", "Filter by Month"),
            ("4", "Search by Description keyword"),
            ("0", "Back"),
        ]
        for key, label in options:
            print(f"    {colored(f'[{key}]', Colors.CYAN + Colors.BOLD)} {label}")
        print()
        choice = input("  ▶ Choice: ").strip()

        if choice == "1":
            _filter_by_date_range(expenses)
        elif choice == "2":
            _filter_by_category_menu(expenses)
        elif choice == "3":
            _filter_by_month_menu(expenses)
        elif choice == "4":
            _search_by_keyword(expenses)
        elif choice == "0":
            break
        else:
            print_error("Invalid choice.")
            press_enter_to_continue()


def _filter_by_date_range(expenses: list[Expense]):
    print_header("Filter by Date Range")
    start, end = get_date_range()
    result = filter_by_date(expenses, start, end)
    print_expense_list(result, f"Expenses: {start} to {end}")
    if result:
        print(colored(f"  Total: {format_currency(total_amount(result))}", Colors.GREEN + Colors.BOLD))
    press_enter_to_continue()


def _filter_by_category_menu(expenses: list[Expense]):
    print_header("Filter by Category")
    category = get_valid_category("  Category number: ")
    result = filter_by_category(expenses, category)
    print_expense_list(result, f"Category: {category}")
    if result:
        print(colored(f"  Total: {format_currency(total_amount(result))}", Colors.GREEN + Colors.BOLD))
    press_enter_to_continue()


def _filter_by_month_menu(expenses: list[Expense]):
    print_header("Filter by Month")
    year  = get_valid_int("  Year  (e.g. 2024): ", min_val=2000, max_val=2100)
    month = get_valid_int("  Month (1-12)     : ", min_val=1, max_val=12)
    result = filter_by_month(expenses, year, month)
    import calendar
    month_name = calendar.month_name[month]
    print_expense_list(result, f"{month_name} {year}")
    if result:
        print(colored(f"  Total: {format_currency(total_amount(result))}", Colors.GREEN + Colors.BOLD))
    press_enter_to_continue()


def _search_by_keyword(expenses: list[Expense]):
    print_header("Search by Description")
    keyword = input("  Enter keyword: ").strip().lower()
    if not keyword:
        print_warning("No keyword entered.")
        press_enter_to_continue()
        return
    result = [e for e in expenses if keyword in e.description.lower()]
    print_expense_list(result, f"Search: \"{keyword}\"")
    press_enter_to_continue()


# ─── Edit Expense ─────────────────────────────────────────────────────────────

def menu_edit_expense(expenses: list[Expense]):
    """Edit an existing expense by ID."""
    print_header("Edit an Expense")
    if not expenses:
        print_warning("No expenses to edit.")
        press_enter_to_continue()
        return

    try:
        exp_id = get_valid_int("  Enter Expense ID to edit: ", min_val=1, max_val=999999)
        target = next((e for e in expenses if e.expense_id == exp_id), None)
        if not target:
            print_error(f"Expense ID #{exp_id} not found.")
            press_enter_to_continue()
            return

        print(f"\n  Current: {target}")
        print(colored("\n  Leave blank to keep current value.\n", Colors.DIM))

        # Amount
        raw = input(f"  New Amount (current ₹{target.amount:,.2f}): ").strip()
        new_amount = float(raw) if raw else target.amount

        # Category
        print(f"\n  Current category: {colored(target.category, Colors.MAGENTA)}")
        if get_yes_no("  Change category?"):
            new_category = get_valid_category("  New category number: ")
        else:
            new_category = target.category

        # Date
        raw = input(f"\n  New Date (current {target.date}, YYYY-MM-DD or blank): ").strip()
        new_date = raw if raw else target.date

        # Description
        raw = input(f"  New Description (current: {truncate(target.description, 40)}): ").strip()
        new_desc = raw if raw else target.description

        # Apply changes
        new_expense = Expense(new_amount, new_category, new_date, new_desc, target.expense_id)

        print(f"\n  Updated: {new_expense}")
        if get_yes_no("\n  Save changes?"):
            idx = next(i for i, e in enumerate(expenses) if e.expense_id == exp_id)
            expenses[idx] = new_expense
            if save_expenses(expenses):
                print_success("Expense updated successfully!")
            else:
                print_error("Save failed.")
        else:
            print_warning("Edit cancelled.")

    except KeyboardInterrupt:
        print_warning("\nOperation cancelled.")
    except ValueError as e:
        print_error(str(e))

    press_enter_to_continue()


# ─── Delete Expense ───────────────────────────────────────────────────────────

def menu_delete_expense(expenses: list[Expense]):
    """Delete an expense by ID."""
    print_header("Delete an Expense")
    if not expenses:
        print_warning("No expenses to delete.")
        press_enter_to_continue()
        return

    try:
        exp_id = get_valid_int("  Enter Expense ID to delete: ", min_val=1, max_val=999999)
        target = next((e for e in expenses if e.expense_id == exp_id), None)
        if not target:
            print_error(f"Expense ID #{exp_id} not found.")
            press_enter_to_continue()
            return

        print(f"\n  {colored('To delete:', Colors.RED)}  {target}")
        if get_yes_no("\n  ⚠ This action cannot be undone. Confirm delete?"):
            expenses[:] = [e for e in expenses if e.expense_id != exp_id]
            if save_expenses(expenses):
                print_success(f"Expense #{exp_id} deleted.")
            else:
                print_error("Delete failed.")
        else:
            print_warning("Delete cancelled.")

    except KeyboardInterrupt:
        print_warning("\nOperation cancelled.")

    press_enter_to_continue()


# ─── Reports Menu ─────────────────────────────────────────────────────────────

def menu_reports(expenses: list[Expense]):
    """Reports and analytics sub-menu."""
    while True:
        clear_screen()
        print_header("Reports & Analytics")
        options = [
            ("1", "📊 Overall Summary Report"),
            ("2", "📁 Category-wise Report"),
            ("3", "📅 Monthly Summary"),
            ("4", "📆 Custom Date Range Report"),
            ("5", "💾 Export Full Report to File"),
            ("0", "🔙 Back"),
        ]
        for key, label in options:
            print(f"    {colored(f'[{key}]', Colors.GREEN + Colors.BOLD)} {label}")
        print()
        choice = input("  ▶ Choice: ").strip()

        if choice == "1":
            clear_screen()
            print_summary_report(expenses, "Overall Expense Summary")
            press_enter_to_continue()
        elif choice == "2":
            clear_screen()
            print_category_report(expenses)
            press_enter_to_continue()
        elif choice == "3":
            _monthly_summary_menu(expenses)
        elif choice == "4":
            _custom_date_report(expenses)
        elif choice == "5":
            _export_report(expenses)
        elif choice == "0":
            break
        else:
            print_error("Invalid choice.")
            press_enter_to_continue()


def _monthly_summary_menu(expenses: list[Expense]):
    clear_screen()
    print_header("Monthly Summary")
    year = get_valid_int("  Year (e.g. 2024): ", min_val=2000, max_val=2100)
    month = get_valid_int("  Month (1-12)    : ", min_val=1, max_val=12)
    import calendar
    month_name = calendar.month_name[month]
    result = filter_by_month(expenses, year, month)
    print_summary_report(result, f"Report for {month_name} {year}")
    press_enter_to_continue()


def _custom_date_report(expenses: list[Expense]):
    clear_screen()
    print_header("Custom Date Range Report")
    start, end = get_date_range()
    result = filter_by_date(expenses, start, end)
    print_summary_report(result, f"Report: {start} to {end}")
    press_enter_to_continue()


def _export_report(expenses: list[Expense]):
    clear_screen()
    print_header("Export Report to File")
    print_info("This will save a full text report to the 'reports/' folder.\n")
    start, end = get_date_range()
    result = filter_by_date(expenses, start, end)
    content = report_to_text(result, f"Expense Report {start} to {end}")
    path = save_report(content, "expense_report")
    if path:
        print_success(f"Report saved to:\n    {path}")
    else:
        print_error("Could not save report.")
    press_enter_to_continue()


# ─── Backup & Restore ─────────────────────────────────────────────────────────

def menu_backup_restore(expenses: list[Expense]):
    """Backup and restore sub-menu."""
    while True:
        clear_screen()
        print_header("Backup & Restore Data")
        options = [
            ("1", "💾 Create Backup Now"),
            ("2", "📂 List Available Backups"),
            ("3", "♻️  Restore from Backup"),
            ("0", "🔙 Back"),
        ]
        for key, label in options:
            print(f"    {colored(f'[{key}]', Colors.BLUE + Colors.BOLD)} {label}")
        print()
        choice = input("  ▶ Choice: ").strip()

        if choice == "1":
            path = create_backup()
            if path:
                print_success(f"Backup created:\n    {path}")
            else:
                print_warning("No data to back up, or backup failed.")
            press_enter_to_continue()
        elif choice == "2":
            _list_backups()
        elif choice == "3":
            result = _restore_backup_menu()
            if result:
                # Reload expenses in-place
                fresh = load_expenses()
                expenses.clear()
                expenses.extend(fresh)
            press_enter_to_continue()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice.")
            press_enter_to_continue()


def _list_backups():
    clear_screen()
    print_header("Available Backups")
    backups = list_backups()
    if not backups:
        print_warning("No backups found.")
    else:
        for i, path in enumerate(backups, 1):
            import os
            name = os.path.basename(path)
            size = os.path.getsize(path)
            print(f"    {colored(str(i) + '.', Colors.CYAN)} {name}  ({size} bytes)")
    press_enter_to_continue()


def _restore_backup_menu() -> bool:
    clear_screen()
    print_header("Restore from Backup")
    backups = list_backups()
    if not backups:
        print_warning("No backups available.")
        return False

    for i, path in enumerate(backups, 1):
        import os
        print(f"    {colored(str(i) + '.', Colors.CYAN)} {os.path.basename(path)}")
    print()
    choice = get_valid_int("  Select backup number: ", min_val=1, max_val=len(backups))
    selected = backups[choice - 1]

    print_warning("This will OVERWRITE your current data!")
    if get_yes_no("  Are you absolutely sure?"):
        if restore_backup(selected):
            print_success("Data restored successfully!")
            return True
        else:
            print_error("Restore failed.")
    else:
        print_warning("Restore cancelled.")
    return False


# ─── System Info ──────────────────────────────────────────────────────────────

def menu_system_info(expenses: list[Expense]):
    """Show system and data file information."""
    print_header("System Information")
    stats = get_file_stats()
    cat_t = category_totals(expenses) if expenses else {}
    total = total_amount(expenses) if expenses else 0

    print(f"  {'Data File Exists :':<26} {colored(str(stats['file_exists']), Colors.GREEN)}")
    print(f"  {'File Size :':<26} {stats['file_size']} bytes")
    print(f"  {'Last Modified :':<26} {stats['last_modified']}")
    print(f"  {'Backup Count :':<26} {stats['backup_count']}")
    print()
    print(f"  {'Total Records :':<26} {len(expenses)}")
    print(f"  {'Total Spent :':<26} {colored(format_currency(total), Colors.GREEN + Colors.BOLD)}")
    print(f"  {'Categories Used :':<26} {len(cat_t)}")
    if expenses:
        dates = sorted(e.date for e in expenses)
        print(f"  {'Earliest Expense :':<26} {dates[0]}")
        print(f"  {'Latest Expense :':<26} {dates[-1]}")
    print()
    press_enter_to_continue()
