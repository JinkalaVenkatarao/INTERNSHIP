"""
reports.py - Report generation functions for Personal Finance Manager
"""

from datetime import datetime, date
from collections import defaultdict
from expense import Expense
from utils import (
    Colors, colored, print_header, print_subheader, print_divider,
    format_currency, format_percentage, bar_chart, truncate
)


# ─── Filtering ────────────────────────────────────────────────────────────────

def filter_by_date(expenses: list[Expense], start: str, end: str) -> list[Expense]:
    """Return expenses within a date range (inclusive)."""
    return [e for e in expenses if start <= e.date <= end]


def filter_by_category(expenses: list[Expense], category: str) -> list[Expense]:
    """Return expenses matching a category."""
    return [e for e in expenses if e.category == category]


def filter_by_month(expenses: list[Expense], year: int, month: int) -> list[Expense]:
    """Return expenses for a specific month."""
    prefix = f"{year:04d}-{month:02d}"
    return [e for e in expenses if e.date.startswith(prefix)]


# ─── Calculations ─────────────────────────────────────────────────────────────

def total_amount(expenses: list[Expense]) -> float:
    """Calculate total of all expenses."""
    return round(sum(e.amount for e in expenses), 2)


def average_amount(expenses: list[Expense]) -> float:
    """Calculate average expense amount."""
    if not expenses:
        return 0.0
    return round(total_amount(expenses) / len(expenses), 2)


def max_expense(expenses: list[Expense]) -> Expense | None:
    """Return the expense with the highest amount."""
    return max(expenses, key=lambda e: e.amount) if expenses else None


def min_expense(expenses: list[Expense]) -> Expense | None:
    """Return the expense with the lowest amount."""
    return min(expenses, key=lambda e: e.amount) if expenses else None


def category_totals(expenses: list[Expense]) -> dict[str, float]:
    """Return a dict of {category: total_amount}, sorted descending."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))


def monthly_totals(expenses: list[Expense]) -> dict[str, float]:
    """Return a dict of {'YYYY-MM': total_amount}, sorted ascending."""
    totals = defaultdict(float)
    for e in expenses:
        month_key = e.date[:7]
        totals[month_key] += e.amount
    return dict(sorted(totals.items()))


# ─── Report Display ───────────────────────────────────────────────────────────

def report_summary(expenses: list[Expense], title: str = "Expense Summary") -> str:
    """Generate a summary report as a string."""
    lines = []
    WIDTH = 70

    lines.append("=" * WIDTH)
    lines.append(f"  {title}".center(WIDTH))
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(WIDTH))
    lines.append("=" * WIDTH)

    if not expenses:
        lines.append("\n  No expenses found for the selected criteria.\n")
        return "\n".join(lines)

    total = total_amount(expenses)
    avg   = average_amount(expenses)
    mx    = max_expense(expenses)
    mn    = min_expense(expenses)
    cat_t = category_totals(expenses)

    lines.append(f"\n  Total Expenses  : {format_currency(total)}")
    lines.append(f"  No. of Records  : {len(expenses)}")
    lines.append(f"  Average Expense : {format_currency(avg)}")
    lines.append(f"  Highest Expense : {format_currency(mx.amount)}  ({mx.description[:35]})")
    lines.append(f"  Lowest Expense  : {format_currency(mn.amount)}  ({mn.description[:35]})")

    lines.append("\n" + "-" * WIDTH)
    lines.append("  CATEGORY BREAKDOWN")
    lines.append("-" * WIDTH)
    lines.append(f"  {'Category':<24} {'Amount':>12}  {'Share':>7}  {'Chart'}")
    lines.append("  " + "─" * 66)
    for cat, amt in cat_t.items():
        pct = format_percentage(amt, total)
        bar = bar_chart(amt, max(cat_t.values()), width=16)
        lines.append(f"  {cat:<24} {format_currency(amt):>12}  {pct}  {bar}")

    lines.append("\n" + "-" * WIDTH)
    lines.append("  MONTHLY BREAKDOWN")
    lines.append("-" * WIDTH)
    m_totals = monthly_totals(expenses)
    if m_totals:
        max_m = max(m_totals.values())
        lines.append(f"  {'Month':<12} {'Amount':>12}  {'Chart'}")
        lines.append("  " + "─" * 50)
        for month, amt in m_totals.items():
            bar = bar_chart(amt, max_m, width=20)
            lines.append(f"  {month:<12} {format_currency(amt):>12}  {bar}")

    lines.append("\n" + "=" * WIDTH)
    return "\n".join(lines)


def print_summary_report(expenses: list[Expense], title: str = "Expense Summary"):
    """Print a formatted summary report to the terminal."""
    WIDTH = 70
    print_header(title)

    if not expenses:
        print(colored("\n  No expenses found for the selected criteria.\n", Colors.YELLOW))
        return

    total = total_amount(expenses)
    avg   = average_amount(expenses)
    mx    = max_expense(expenses)
    mn    = min_expense(expenses)

    print_subheader("OVERVIEW", WIDTH)
    print(f"    {'Total Expenses :':<22} {colored(format_currency(total), Colors.GREEN + Colors.BOLD)}")
    print(f"    {'Number of Records :':<22} {len(expenses)}")
    print(f"    {'Average Expense :':<22} {colored(format_currency(avg), Colors.CYAN)}")
    print(f"    {'Highest Expense :':<22} {colored(format_currency(mx.amount), Colors.MAGENTA)}  {truncate(mx.description, 28)}")
    print(f"    {'Lowest Expense :':<22} {colored(format_currency(mn.amount), Colors.BLUE)}  {truncate(mn.description, 28)}")

    cat_t = category_totals(expenses)
    print_subheader("CATEGORY BREAKDOWN", WIDTH)
    max_cat = max(cat_t.values()) if cat_t else 1
    print(f"  {'Category':<24} {'Amount':>12}  {'Share':>7}  Chart")
    print_divider()
    for cat, amt in cat_t.items():
        pct  = format_percentage(amt, total)
        bar  = colored(bar_chart(amt, max_cat, width=16, fill="█", empty="░"), Colors.CYAN)
        amts = colored(format_currency(amt), Colors.GREEN)
        print(f"  {cat:<24} {amts}  {pct}  {bar}")

    m_totals = monthly_totals(expenses)
    if m_totals:
        print_subheader("MONTHLY BREAKDOWN", WIDTH)
        max_m = max(m_totals.values())
        print(f"  {'Month':<12} {'Amount':>12}  Chart")
        print_divider()
        for month, amt in m_totals.items():
            bar  = colored(bar_chart(amt, max_m, width=20), Colors.BLUE)
            amts = colored(format_currency(amt), Colors.GREEN)
            print(f"  {month:<12} {amts}  {bar}")
    print()


def print_expense_list(expenses: list[Expense], title: str = "Expense List"):
    """Print a formatted table of expenses."""
    print_header(title)
    if not expenses:
        print(colored("\n  No expenses to display.\n", Colors.YELLOW))
        return

    print(colored(
        f"\n  {'ID':>4}  {'Date':<12} {'Category':<22} {'Amount':>12}  Description",
        Colors.BOLD
    ))
    print_divider()
    total = 0.0
    for e in sorted(expenses, key=lambda x: x.date, reverse=True):
        total += e.amount
        amt_str = colored(f"₹{e.amount:>10,.2f}", Colors.GREEN)
        date_str = colored(e.date, Colors.CYAN)
        cat_str = colored(f"{e.category:<22}", Colors.MAGENTA)
        print(f"  {e.expense_id:>4}  {date_str}  {cat_str} {amt_str}  {truncate(e.description, 35)}")

    print_divider()
    print(colored(
        f"  {'TOTAL':>40}  ₹{total:>10,.2f}  ({len(expenses)} records)",
        Colors.BOLD + Colors.GREEN
    ))
    print()


def print_category_report(expenses: list[Expense]):
    """Print a detailed per-category breakdown."""
    print_header("Category-wise Report")
    if not expenses:
        print(colored("\n  No data available.\n", Colors.YELLOW))
        return

    cat_t = category_totals(expenses)
    grand_total = total_amount(expenses)
    max_amt = max(cat_t.values()) if cat_t else 1

    for cat, amt in cat_t.items():
        cat_expenses = filter_by_category(expenses, cat)
        avg = average_amount(cat_expenses)
        mx  = max_expense(cat_expenses)
        bar = colored(bar_chart(amt, max_amt, width=24), Colors.CYAN)
        pct = format_percentage(amt, grand_total)

        print(f"\n  {colored(cat, Colors.BOLD + Colors.MAGENTA)}")
        print(f"    Total : {colored(format_currency(amt), Colors.GREEN)}  {pct}  {bar}")
        print(f"    Avg   : {format_currency(avg)}   Count: {len(cat_expenses)}")
        if mx:
            print(f"    Peak  : {format_currency(mx.amount)} on {mx.date}  – {truncate(mx.description, 30)}")
    print()


def report_to_text(expenses: list[Expense], title: str = "Full Expense Report") -> str:
    """Produce a plain-text report including all expense rows."""
    summary = report_summary(expenses, title)
    WIDTH = 70
    rows = [
        "\n" + "=" * WIDTH,
        "  FULL EXPENSE LIST",
        "=" * WIDTH,
        f"  {'ID':>4}  {'Date':<12} {'Category':<22} {'Amount':>12}  Description",
        "  " + "─" * 66,
    ]
    for e in sorted(expenses, key=lambda x: x.date):
        rows.append(
            f"  {e.expense_id:>4}  {e.date:<12} {e.category:<22} ₹{e.amount:>10,.2f}  {e.description}"
        )
    rows.append("=" * WIDTH)
    return summary + "\n".join(rows)
