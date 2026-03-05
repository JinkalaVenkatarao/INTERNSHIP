# 🔧 Technical Documentation

## Architecture Overview

The application follows a **modular MVC-like design** where each concern is separated into its own module:

```
main.py                ← Controller: orchestrates startup and menu loop
src/
├── expense.py         ← Model: Expense data class + validation
├── file_manager.py    ← Data layer: CSV persistence, backup/restore
├── reports.py         ← Analytics: filtering, calculations, formatting
├── menu.py            ← View: all CLI menus and user interaction
└── utils.py           ← Helpers: input validation, colors, formatting
```

---

## Module Reference

### `src/expense.py` — The Expense Model

**Class: `Expense`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `expense_id` | `int \| None` | Unique auto-assigned identifier |
| `amount` | `float` | Positive value, rounded to 2 decimals |
| `category` | `str` | Must be one of `VALID_CATEGORIES` |
| `date` | `str` | ISO format: `YYYY-MM-DD` |
| `description` | `str` | 1–100 characters |

**Key methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `dict` | Serialise to CSV-writable dict |
| `from_dict(data)` | `Expense` | Deserialise from a CSV row dict |
| `__str__()` | `str` | Human-readable one-line summary |

**Validation** is performed in the constructor via private `_validate_*` methods. Any invalid input raises `ValueError` with a descriptive message.

---

### `src/file_manager.py` — Data Persistence

All file paths are determined from the `PFM_ROOT` environment variable (set by `main.py`).

| Function | Returns | Description |
|----------|---------|-------------|
| `initialize_csv()` | `None` | Creates CSV + all dirs if missing |
| `load_expenses()` | `list[Expense]` | Reads and parses the CSV |
| `save_expenses(expenses)` | `bool` | Overwrites CSV with full list |
| `add_expense(expense)` | `bool` | Appends single row to CSV |
| `get_next_id(expenses)` | `int` | Returns `max_id + 1` |
| `create_backup()` | `str` | Timestamped copy → `data/backups/` |
| `list_backups()` | `list[str]` | Sorted paths, newest first |
| `restore_backup(path)` | `bool` | Copies backup → `data/expenses.csv` |
| `save_report(content, name)` | `str` | Writes `.txt` to `reports/` |
| `get_file_stats()` | `dict` | Size, modified date, backup count |

---

### `src/reports.py` — Analytics & Reporting

**Filtering functions:**

| Function | Description |
|----------|-------------|
| `filter_by_date(expenses, start, end)` | Inclusive date range filter |
| `filter_by_category(expenses, cat)` | Exact category match |
| `filter_by_month(expenses, year, month)` | Year + month filter |

**Calculation functions:**

| Function | Description |
|----------|-------------|
| `total_amount(expenses)` | Sum of all amounts |
| `average_amount(expenses)` | Mean expense value |
| `max_expense(expenses)` | Highest-amount Expense object |
| `min_expense(expenses)` | Lowest-amount Expense object |
| `category_totals(expenses)` | `{category: total}` sorted descending |
| `monthly_totals(expenses)` | `{"YYYY-MM": total}` sorted ascending |

**Display functions:**

| Function | Description |
|----------|-------------|
| `print_summary_report(expenses, title)` | Colour terminal summary |
| `print_expense_list(expenses, title)` | Colour table of expenses |
| `print_category_report(expenses)` | Per-category breakdown |
| `report_summary(expenses, title)` | Plain-text summary string |
| `report_to_text(expenses, title)` | Full plain-text report string |

---

### `src/utils.py` — Utilities

**Input helpers** (all loop until valid input is received):

| Function | Description |
|----------|-------------|
| `get_valid_float(prompt, min, max)` | Validated float input |
| `get_valid_int(prompt, min, max)` | Validated integer input |
| `get_valid_date(prompt)` | `YYYY-MM-DD` date input |
| `get_valid_category(prompt)` | Numbered category picker |
| `get_valid_description(prompt)` | Non-empty, ≤100 char string |
| `get_yes_no(prompt)` | Returns `True`/`False` |
| `get_date_range(...)` | Returns `(start, end)` tuple |

**Formatting helpers:**

| Function | Description |
|----------|-------------|
| `format_currency(amount, symbol)` | e.g., `₹   1,500.00` |
| `format_percentage(value, total)` | e.g., `  25.0%` |
| `truncate(text, max_len)` | Clips with `...` |
| `bar_chart(value, max, width)` | ASCII `█░` bar |

---

## Data Flow

```
User Input
    │
    ▼
menu.py  ──validates via──▶  utils.py
    │
    │  creates
    ▼
Expense object (expense.py)  ──validates all fields──▶  ValueError if bad
    │
    │  passed to
    ▼
file_manager.py  ──writes──▶  data/expenses.csv
    │
    │  reads
    ▼
reports.py  ──calculates──▶  terminal / .txt file
```

---

## Error Handling Strategy

1. **Input validation** — All user inputs go through `utils.py` helpers that loop until valid data is received. They never crash; they prompt again.
2. **Model validation** — `Expense.__init__` validates every field and raises `ValueError` with a clear message.
3. **File I/O** — All file operations are wrapped in `try/except`. Failures print a message and return `False`/`""` rather than crashing.
4. **Menu-level catch** — `menu.py` catches `KeyboardInterrupt` (Ctrl+C) and `ValueError` on every form-entry flow, so the app always returns cleanly to the menu.
5. **Corrupted CSV rows** — `load_expenses()` skips individual bad rows with a warning rather than refusing to load the file.

---

## Extending the Application

### Add a new category
Edit `VALID_CATEGORIES` in `src/expense.py`:
```python
VALID_CATEGORIES = [
    ...
    "Gifts & Donations",   # ← add here
]
```

### Change the currency symbol
Edit `format_currency()` in `src/utils.py`:
```python
def format_currency(amount: float, symbol: str = "$") -> str:
```

### Add a new report type
1. Add a calculation or filter function in `src/reports.py`
2. Add a display function that calls `print_header()` etc.
3. Add a menu option in `menu_reports()` inside `src/menu.py`
