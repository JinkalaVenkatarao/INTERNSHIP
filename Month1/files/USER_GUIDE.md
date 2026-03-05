# 📘 Personal Finance Manager — User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Main Menu Overview](#main-menu-overview)
3. [Adding an Expense](#adding-an-expense)
4. [Viewing Expenses](#viewing-expenses)
5. [Searching & Filtering](#searching--filtering)
6. [Editing an Expense](#editing-an-expense)
7. [Deleting an Expense](#deleting-an-expense)
8. [Reports & Analytics](#reports--analytics)
9. [Backup & Restore](#backup--restore)
10. [Categories Reference](#categories-reference)
11. [Data Files](#data-files)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

After installing and running the app (`python main.py`), you will see the welcome banner followed by the **Main Menu**.

```
  ╔══════════════════════════════════════════════════════════════════════╗
  ║        💰  PERSONAL FINANCE MANAGER  💰                            ║
  ║              Track • Analyse • Save Smarter                        ║
  ╚══════════════════════════════════════════════════════════════════════╝

  📅 Today: 15 Mar 2024

    [1] ➕  Add New Expense
    [2] 📋  View All Expenses
    [3] 🔍  Search & Filter Expenses
    [4] ✏️   Edit an Expense
    [5] 🗑️   Delete an Expense
    [6] 📊  Reports & Analytics
    [7] 💾  Backup & Restore Data
    [8] ℹ️   System Info
    [0] 🚪  Exit
```

Type the number and press **Enter** to navigate.

---

## Main Menu Overview

| Option | What it does |
|--------|-------------|
| `1` | Add a brand-new expense record |
| `2` | Browse all expenses (paginated, 15 per page) |
| `3` | Filter by date range, category, month, or keyword |
| `4` | Change the details of an existing expense |
| `5` | Permanently remove an expense |
| `6` | View summary, category, and monthly reports |
| `7` | Create/restore data backups |
| `8` | See file statistics and record counts |
| `0` | Exit (auto-backup runs before closing) |

---

## Adding an Expense

Select **[1]** from the main menu.

**Step-by-step:**

1. **Amount** — Enter a positive number (e.g., `450` or `1250.75`).
2. **Category** — A numbered list is shown. Type the number (1–11).
3. **Date** — Enter in `YYYY-MM-DD` format, or press **Enter** to use today's date.
4. **Description** — A brief note (max 100 characters).
5. **Confirm** — A preview is shown; type `y` to save or `n` to discard.

**Example session:**
```
  Amount (₹): 650
  Select a category:
    1. Food & Dining
    2. Transportation
    ...
  Category number: 1
  Date (YYYY-MM-DD): 2024-03-15
  Description: Team lunch at Cafe Coffee Day

  Preview:
    Amount      : ₹          650.00
    Category    : Food & Dining
    Date        : 2024-03-15
    Description : Team lunch at Cafe Coffee Day

  Save this expense? (y/n): y
  ✓ Expense #21 saved successfully!
```

**Validation rules:**
- Amount must be greater than `0`
- Date must be a real calendar date in `YYYY-MM-DD` format
- Description cannot be blank or exceed 100 characters
- You can press **Ctrl+C** at any point to cancel

---

## Viewing Expenses

Select **[2]** from the main menu.

Expenses are displayed newest-first in pages of 15. At the bottom of each page:
- `[N]` — Next page
- `[P]` — Previous page
- `[B]` — Back to main menu

The grand total across **all** expenses is shown at the bottom.

---

## Searching & Filtering

Select **[3]** from the main menu. Four filter modes are available:

### Filter by Date Range
Enter a start and end date (`YYYY-MM-DD`). Press **Enter** on either to use the default (Jan 1 of current year / today).

### Filter by Category
Shows the category list; select a number to see only that category's expenses.

### Filter by Month
Enter a year (e.g., `2024`) and a month number (`1`–`12`). All expenses for that month are shown.

### Search by Description Keyword
Type any word or phrase. The search is **case-insensitive** and matches partial words.
- Example: typing `lunch` finds "Team lunch", "Quick lunch", etc.

---

## Editing an Expense

Select **[4]** from the main menu.

1. First, view your expenses to find the **ID** of the record you want to change.
2. Enter that ID number.
3. For each field, either type a new value or press **Enter** to keep the existing one.
4. Confirm with `y` to save.

> **Tip:** The ID is shown in the leftmost column of the expense list.

---

## Deleting an Expense

Select **[5]** from the main menu.

1. Enter the **ID** of the expense to delete.
2. The record is shown for review.
3. Confirm with `y` — deletion is **permanent** and cannot be undone.

> **Safety tip:** Create a backup (option 7) before bulk-deleting records.

---

## Reports & Analytics

Select **[6]** from the main menu. Five report types are available:

### 1. Overall Summary Report
A full overview of all your data:
- Total, average, highest, and lowest expense
- Category breakdown with percentage share and bar chart
- Month-by-month trend chart

### 2. Category-wise Report
Drill into each category showing:
- Total and average for that category
- Number of transactions
- The highest single expense in that category

### 3. Monthly Summary
Pick a specific year and month to see a focused report for that period.

### 4. Custom Date Range Report
Choose any start and end date for a targeted analysis.

### 5. Export Full Report to File
Saves a `.txt` report to the `reports/` folder with a timestamped filename, e.g.:
```
reports/expense_report_20240315_142301.txt
```

---

## Backup & Restore

Select **[7]** from the main menu.

### Create Backup
Copies `data/expenses.csv` to `data/backups/` with a timestamp:
```
data/backups/expenses_backup_20240315_143000.csv
```

### List Backups
Shows all available backups, newest first.

### Restore from Backup
Select a backup number. Your current data is automatically saved as `pre_restore_safety.csv` before the restore happens.

> **Auto-backup:** Every time you exit the app via option `[0]`, a backup is created automatically.

---

## Categories Reference

| # | Category | Common uses |
|---|----------|-------------|
| 1 | Food & Dining | Restaurants, groceries, coffee |
| 2 | Transportation | Fuel, public transport, cab/ride-share |
| 3 | Shopping | Clothes, electronics, household items |
| 4 | Entertainment | Movies, games, subscriptions |
| 5 | Health & Medical | Doctor, pharmacy, gym |
| 6 | Housing & Utilities | Rent, electricity, internet, water |
| 7 | Education | Courses, books, tuition |
| 8 | Travel | Hotels, flights, weekend trips |
| 9 | Personal Care | Haircut, salon, skincare |
| 10 | Savings & Investment | SIP, FD, emergency fund |
| 11 | Other | Anything that doesn't fit above |

---

## Data Files

```
data/
├── expenses.csv          ← All your expense records
├── sample_data.csv       ← 20 sample records for demo/testing
└── backups/
    ├── expenses_backup_YYYYMMDD_HHMMSS.csv   ← Timestamped backups
    └── pre_restore_safety.csv                ← Auto-saved before restore

reports/
└── expense_report_YYYYMMDD_HHMMSS.txt       ← Exported text reports
```

### CSV Format
The `expenses.csv` file has these columns:
```
id, amount, category, date, description
```
You can open it in Excel or Google Sheets, but **do not change the column names** or the app may fail to load the data.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python: command not found` | Use `python3` instead of `python` |
| `ModuleNotFoundError` | Make sure you're running `python main.py` from the project root folder |
| App shows wrong currency symbol | The app uses `₹` (Indian Rupee) by default. Edit `format_currency()` in `src/utils.py` to change the symbol |
| Data file seems corrupted | Use Backup & Restore (option 7) to restore a previous backup |
| Colors not showing on Windows | Install Windows Terminal or use Git Bash for full ANSI color support |
| Date rejected | Always use `YYYY-MM-DD` format, e.g., `2024-03-15` not `15/03/2024` |

---

*Last updated: March 2024 | Version 1.0*
