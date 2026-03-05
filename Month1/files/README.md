# 💰 Personal Finance Manager

> A comprehensive command-line personal finance tracker built with Python.  
> Track expenses, analyse spending patterns, and generate detailed reports — all from your terminal.

---

## 📸 Preview

```
  ╔══════════════════════════════════════════════════════════════════════╗
  ║          💰  PERSONAL FINANCE MANAGER  💰                           ║
  ║                 Your Smart Expense Tracker                          ║
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

---

## ✨ Features

| Feature | Details |
|---------|---------|
| ➕ **Add Expenses** | Amount, category, date, description with full validation |
| 📋 **View Expenses** | Paginated colour table sorted by date |
| 🔍 **Search & Filter** | By date range, category, month, or description keyword |
| ✏️ **Edit Records** | Update any field of an existing expense |
| 🗑️ **Delete Records** | Safe deletion with confirmation prompt |
| 📊 **Reports** | Summary, category-wise, monthly, custom date range |
| 📈 **Analytics** | Totals, averages, min/max, ASCII bar charts |
| 💾 **Export Reports** | Save reports as `.txt` files |
| 🔒 **Backup & Restore** | Timestamped CSV backups + auto-backup on exit |
| ✅ **Error Handling** | Robust validation on every user input — never crashes |

---

## 📁 Project Structure

```
personal-finance-manager/
│
├── main.py                  ← Entry point — run this to start the app
├── requirements.txt         ← No third-party packages needed
├── .gitignore
│
├── src/                     ← All source code modules
│   ├── expense.py           ← Expense class with validation
│   ├── file_manager.py      ← CSV read/write, backup, restore
│   ├── reports.py           ← Report generation & analytics
│   ├── menu.py              ← Interactive CLI menus
│   └── utils.py             ← Input helpers, colours, formatting
│
├── data/                    ← Data storage
│   ├── expenses.csv         ← Your expense records (auto-created)
│   ├── sample_data.csv      ← 20 sample records for demo
│   └── backups/             ← Auto/manual backups go here
│
├── reports/                 ← Exported text reports (auto-created)
│
├── docs/                    ← Documentation
│   ├── USER_GUIDE.md        ← Full user guide with examples
│   └── TECHNICAL.md         ← Architecture & developer reference
│
├── tests/                   ← Unit tests
│   └── test_expense.py      ← 40+ tests for all modules
│
└── screenshots/             ← Application screenshots
```

---

## 🚀 How to Run — Step by Step

### ✅ Prerequisites

You only need **Python 3.10 or higher**. No extra packages to install.

**Check your Python version:**
```bash
# On Windows
python --version

# On Mac / Linux
python3 --version
```

If you see `Python 3.10.x` or higher, you're ready to go.  
If Python is not installed, download it from **https://www.python.org/downloads/**

---

### 📥 Step 1 — Get the Project Files

**Option A — Download ZIP (easiest):**
1. Click the green **`Code`** button on GitHub
2. Select **`Download ZIP`**
3. Extract the ZIP to a folder of your choice (e.g., `Desktop/personal-finance-manager`)

**Option B — Clone with Git:**
```bash
git clone https://github.com/YOUR_USERNAME/personal-finance-manager.git
cd personal-finance-manager
```

---

### 📂 Step 2 — Open Terminal in the Project Folder

**Windows:**
1. Open File Explorer and navigate to the project folder
2. Click the address bar at the top, type `cmd`, press **Enter**  
   *(Or right-click inside the folder → "Open in Terminal")*

**Mac:**
1. Open **Finder** and navigate to the project folder
2. Right-click the folder → **"New Terminal at Folder"**  
   *(Or open Terminal and type `cd ~/Desktop/personal-finance-manager`)*

**Linux:**
```bash
cd /path/to/personal-finance-manager
```

---

### ▶️ Step 3 — Run the Application

```bash
# Windows
python main.py

# Mac / Linux
python3 main.py
```

The app will launch immediately — no installation or setup required!

---

### 🎯 Step 4 — Try It with Sample Data (Optional)

To load the 20 included sample expense records:

```bash
# Windows
copy data\sample_data.csv data\expenses.csv

# Mac / Linux
cp data/sample_data.csv data/expenses.csv
```

Then run `python main.py` (or `python3 main.py`) and you'll see 20 pre-loaded records to explore.

---

### 🧪 Step 5 — Run Unit Tests (Optional)

```bash
# Run all tests with detailed output
python -m pytest tests/ -v

# Or run without pytest (built-in runner)
python tests/test_expense.py
```

---

## 🗺️ Quick Usage Guide

### Adding your first expense
1. Start the app: `python main.py`
2. Press `1` → Add New Expense
3. Enter amount: `500`
4. Select category: `1` (Food & Dining)
5. Press **Enter** for today's date
6. Enter description: `Lunch`
7. Press `y` to save

### Viewing a report
1. Press `6` → Reports & Analytics
2. Press `1` → Overall Summary Report
3. See totals, category breakdown, and monthly chart

### Exporting a report to file
1. Press `6` → Reports & Analytics
2. Press `5` → Export Full Report to File
3. Press **Enter** twice to use default date range
4. Find the `.txt` file in the `reports/` folder

---

## 🏗️ Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data storage | CSV (standard library `csv` module) |
| UI | Terminal / CLI with ANSI colours |
| Testing | `unittest` (standard library) |
| Dependencies | **Zero** — pure standard library |

---

## 📋 Expense Categories

```
1.  Food & Dining          7.  Education
2.  Transportation         8.  Travel
3.  Shopping               9.  Personal Care
4.  Entertainment         10.  Savings & Investment
5.  Health & Medical      11.  Other
6.  Housing & Utilities
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete walkthrough of every feature with examples |
| [Technical Docs](docs/TECHNICAL.md) | Module reference, data flow, and how to extend the app |

---

## 🧩 Error Handling

The app handles all common errors gracefully:
- **Invalid amount** (letters, negative numbers, zero) → re-prompts with clear message
- **Invalid date format** → re-prompts with example
- **Invalid category** → shows list and re-prompts
- **Empty description** → re-prompts
- **Corrupted CSV rows** → skipped with warning, rest of file loads normally
- **Missing data file** → auto-created on first run
- **Ctrl+C at any prompt** → returns cleanly to the main menu

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

*Built with ❤️ using Python | No external dependencies*
