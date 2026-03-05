"""
tests/test_expense.py
=====================
Unit tests for the Expense class and file_manager module.

Run all tests:
    python -m pytest tests/ -v
    -- or --
    python tests/test_expense.py
"""

import sys
import os
import unittest
import tempfile
import shutil

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from expense import Expense


# ═══════════════════════════════════════════════════════════
#  Expense Class Tests
# ═══════════════════════════════════════════════════════════

class TestExpenseCreation(unittest.TestCase):
    """Tests for creating valid Expense objects."""

    def setUp(self):
        """Create a standard valid expense for reuse."""
        self.valid_expense = Expense(
            amount=500.0,
            category="Food & Dining",
            date="2024-03-15",
            description="Lunch at restaurant",
            expense_id=1
        )

    def test_valid_expense_creation(self):
        """A correctly formed expense should be created without errors."""
        self.assertEqual(self.valid_expense.amount, 500.0)
        self.assertEqual(self.valid_expense.category, "Food & Dining")
        self.assertEqual(self.valid_expense.date, "2024-03-15")
        self.assertEqual(self.valid_expense.description, "Lunch at restaurant")
        self.assertEqual(self.valid_expense.expense_id, 1)

    def test_amount_is_rounded_to_two_decimals(self):
        """Amounts with many decimal places should be rounded to 2."""
        e = Expense(99.9999, "Shopping", "2024-01-01", "Test item")
        self.assertEqual(e.amount, 100.0)

    def test_amount_with_string_input(self):
        """Amount passed as a string should be converted to float."""
        e = Expense("250.50", "Food & Dining", "2024-01-01", "String amount")
        self.assertEqual(e.amount, 250.50)

    def test_description_is_stripped(self):
        """Leading/trailing whitespace in description should be removed."""
        e = Expense(100, "Other", "2024-01-01", "   padded text   ")
        self.assertEqual(e.description, "padded text")

    def test_expense_id_is_optional(self):
        """expense_id should default to None when not provided."""
        e = Expense(100, "Other", "2024-01-01", "No ID")
        self.assertIsNone(e.expense_id)


class TestExpenseValidation(unittest.TestCase):
    """Tests for Expense input validation — all invalid inputs should raise ValueError."""

    # ── Amount ──────────────────────────────────────────────
    def test_negative_amount_raises(self):
        with self.assertRaises(ValueError):
            Expense(-100, "Food & Dining", "2024-01-01", "Negative")

    def test_zero_amount_raises(self):
        with self.assertRaises(ValueError):
            Expense(0, "Food & Dining", "2024-01-01", "Zero")

    def test_non_numeric_amount_raises(self):
        with self.assertRaises(ValueError):
            Expense("abc", "Food & Dining", "2024-01-01", "Bad amount")

    def test_none_amount_raises(self):
        with self.assertRaises(ValueError):
            Expense(None, "Food & Dining", "2024-01-01", "None amount")

    # ── Category ─────────────────────────────────────────────
    def test_invalid_category_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "InvalidCategory", "2024-01-01", "Bad cat")

    def test_empty_category_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "", "2024-01-01", "Empty cat")

    def test_case_sensitive_category(self):
        """Categories are case-sensitive; lowercase should fail."""
        with self.assertRaises(ValueError):
            Expense(100, "food & dining", "2024-01-01", "Lowercase")

    # ── Date ─────────────────────────────────────────────────
    def test_invalid_date_format_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "15-03-2024", "Wrong date format")

    def test_invalid_date_value_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "2024-13-01", "Month 13")

    def test_non_date_string_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "not-a-date", "Not a date")

    # ── Description ──────────────────────────────────────────
    def test_empty_description_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "2024-01-01", "")

    def test_whitespace_only_description_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "2024-01-01", "   ")

    def test_description_over_100_chars_raises(self):
        with self.assertRaises(ValueError):
            Expense(100, "Food & Dining", "2024-01-01", "x" * 101)

    def test_description_exactly_100_chars_is_valid(self):
        """Descriptions of exactly 100 characters should be allowed."""
        e = Expense(100, "Food & Dining", "2024-01-01", "x" * 100)
        self.assertEqual(len(e.description), 100)


class TestExpenseSerialization(unittest.TestCase):
    """Tests for to_dict() and from_dict() round-trips."""

    def setUp(self):
        self.expense = Expense(
            amount=1500.75,
            category="Shopping",
            date="2024-06-20",
            description="New headphones",
            expense_id=42
        )

    def test_to_dict_keys(self):
        d = self.expense.to_dict()
        self.assertIn("id", d)
        self.assertIn("amount", d)
        self.assertIn("category", d)
        self.assertIn("date", d)
        self.assertIn("description", d)

    def test_to_dict_values(self):
        d = self.expense.to_dict()
        self.assertEqual(d["amount"], 1500.75)
        self.assertEqual(d["category"], "Shopping")
        self.assertEqual(d["date"], "2024-06-20")
        self.assertEqual(d["id"], 42)

    def test_from_dict_round_trip(self):
        """Converting to dict and back should produce an identical expense."""
        d = self.expense.to_dict()
        restored = Expense.from_dict(d)
        self.assertEqual(restored.amount, self.expense.amount)
        self.assertEqual(restored.category, self.expense.category)
        self.assertEqual(restored.date, self.expense.date)
        self.assertEqual(restored.description, self.expense.description)
        self.assertEqual(restored.expense_id, self.expense.expense_id)

    def test_str_representation(self):
        """__str__ should include ID, date, category, amount, and description."""
        s = str(self.expense)
        self.assertIn("42", s)
        self.assertIn("2024-06-20", s)
        self.assertIn("Shopping", s)
        self.assertIn("New headphones", s)


class TestExpenseCategories(unittest.TestCase):
    """Tests for the VALID_CATEGORIES class attribute."""

    def test_valid_categories_is_list(self):
        self.assertIsInstance(Expense.VALID_CATEGORIES, list)

    def test_valid_categories_not_empty(self):
        self.assertGreater(len(Expense.VALID_CATEGORIES), 0)

    def test_all_valid_categories_accepted(self):
        """Every category in VALID_CATEGORIES should be accepted."""
        for cat in Expense.VALID_CATEGORIES:
            e = Expense(100, cat, "2024-01-01", f"Test {cat}")
            self.assertEqual(e.category, cat)


# ═══════════════════════════════════════════════════════════
#  File Manager Tests
# ═══════════════════════════════════════════════════════════

class TestFileManager(unittest.TestCase):
    """Integration tests for file_manager operations using a temp directory."""

    def setUp(self):
        """Create a fresh temp directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        os.environ["PFM_ROOT"] = self.test_dir
        # Re-import to pick up new env var
        import importlib
        import file_manager
        importlib.reload(file_manager)
        self.fm = file_manager

    def tearDown(self):
        """Remove temp directory after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_expense(self, eid=1, amount=100.0, desc="Test"):
        return Expense(amount, "Food & Dining", "2024-01-01", desc, eid)

    def test_initialize_creates_csv(self):
        self.fm.initialize_csv()
        self.assertTrue(os.path.exists(self.fm.EXPENSES_FILE))

    def test_save_and_load_round_trip(self):
        expenses = [
            self._make_expense(1, 200, "Coffee"),
            self._make_expense(2, 500, "Lunch"),
        ]
        self.fm.save_expenses(expenses)
        loaded = self.fm.load_expenses()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].amount, 200.0)
        self.assertEqual(loaded[1].description, "Lunch")

    def test_load_returns_empty_list_when_no_file(self):
        loaded = self.fm.load_expenses()
        self.assertEqual(loaded, [])

    def test_get_next_id_empty(self):
        self.assertEqual(self.fm.get_next_id([]), 1)

    def test_get_next_id_with_expenses(self):
        expenses = [self._make_expense(5), self._make_expense(12)]
        self.assertEqual(self.fm.get_next_id(expenses), 13)

    def test_create_backup_returns_path(self):
        expenses = [self._make_expense()]
        self.fm.save_expenses(expenses)
        path = self.fm.create_backup()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".csv"))

    def test_create_backup_no_file_returns_empty(self):
        path = self.fm.create_backup()
        self.assertEqual(path, "")

    def test_list_backups_returns_sorted_newest_first(self):
        import time
        expenses = [self._make_expense()]
        self.fm.save_expenses(expenses)
        self.fm.create_backup()
        time.sleep(1)
        self.fm.create_backup()
        backups = self.fm.list_backups()
        self.assertEqual(len(backups), 2)
        self.assertGreater(backups[0], backups[1])  # Newest first

    def test_restore_backup(self):
        expenses = [self._make_expense(1, 999, "Original")]
        self.fm.save_expenses(expenses)
        backup = self.fm.create_backup()
        # Overwrite with different data
        self.fm.save_expenses([self._make_expense(2, 1, "Overwritten")])
        # Restore
        result = self.fm.restore_backup(backup)
        self.assertTrue(result)
        restored = self.fm.load_expenses()
        self.assertEqual(restored[0].description, "Original")


# ═══════════════════════════════════════════════════════════
#  Reports Tests
# ═══════════════════════════════════════════════════════════

class TestReports(unittest.TestCase):
    """Tests for report calculation functions."""

    def setUp(self):
        self.expenses = [
            Expense(100, "Food & Dining",   "2024-01-10", "Lunch",       1),
            Expense(200, "Transportation",  "2024-01-15", "Bus pass",    2),
            Expense(300, "Shopping",        "2024-02-05", "Shirt",       3),
            Expense(400, "Food & Dining",   "2024-02-20", "Dinner",      4),
            Expense(500, "Entertainment",   "2024-03-01", "Concert",     5),
        ]

    def test_total_amount(self):
        from reports import total_amount
        self.assertEqual(total_amount(self.expenses), 1500.0)

    def test_total_amount_empty(self):
        from reports import total_amount
        self.assertEqual(total_amount([]), 0.0)

    def test_average_amount(self):
        from reports import average_amount
        self.assertEqual(average_amount(self.expenses), 300.0)

    def test_average_amount_empty(self):
        from reports import average_amount
        self.assertEqual(average_amount([]), 0.0)

    def test_max_expense(self):
        from reports import max_expense
        mx = max_expense(self.expenses)
        self.assertEqual(mx.amount, 500.0)

    def test_min_expense(self):
        from reports import min_expense
        mn = min_expense(self.expenses)
        self.assertEqual(mn.amount, 100.0)

    def test_category_totals(self):
        from reports import category_totals
        totals = category_totals(self.expenses)
        self.assertEqual(totals["Food & Dining"], 500.0)   # 100 + 400
        self.assertEqual(totals["Transportation"], 200.0)
        self.assertEqual(totals["Shopping"], 300.0)

    def test_category_totals_sorted_descending(self):
        from reports import category_totals
        totals = category_totals(self.expenses)
        values = list(totals.values())
        self.assertEqual(values, sorted(values, reverse=True))

    def test_monthly_totals(self):
        from reports import monthly_totals
        m = monthly_totals(self.expenses)
        self.assertAlmostEqual(m["2024-01"], 300.0)
        self.assertAlmostEqual(m["2024-02"], 700.0)
        self.assertAlmostEqual(m["2024-03"], 500.0)

    def test_filter_by_date(self):
        from reports import filter_by_date
        result = filter_by_date(self.expenses, "2024-01-01", "2024-01-31")
        self.assertEqual(len(result), 2)

    def test_filter_by_category(self):
        from reports import filter_by_category
        result = filter_by_category(self.expenses, "Food & Dining")
        self.assertEqual(len(result), 2)

    def test_filter_by_month(self):
        from reports import filter_by_month
        result = filter_by_month(self.expenses, 2024, 2)
        self.assertEqual(len(result), 2)


# ═══════════════════════════════════════════════════════════
#  Utils Tests
# ═══════════════════════════════════════════════════════════

class TestUtils(unittest.TestCase):
    """Tests for utility/formatting functions."""

    def test_format_currency(self):
        from utils import format_currency
        result = format_currency(1234.5)
        self.assertIn("1,234.50", result)

    def test_format_percentage_normal(self):
        from utils import format_percentage
        result = format_percentage(50, 200)
        self.assertIn("25.0", result)

    def test_format_percentage_zero_total(self):
        from utils import format_percentage
        result = format_percentage(50, 0)
        self.assertIn("0.0", result)

    def test_truncate_short_string(self):
        from utils import truncate
        self.assertEqual(truncate("hello", 10), "hello")

    def test_truncate_long_string(self):
        from utils import truncate
        result = truncate("a" * 40, 10)
        self.assertEqual(len(result), 10)
        self.assertTrue(result.endswith("..."))

    def test_bar_chart_full(self):
        from utils import bar_chart
        result = bar_chart(100, 100, width=10)
        self.assertEqual(result, "█" * 10)

    def test_bar_chart_empty(self):
        from utils import bar_chart
        result = bar_chart(0, 100, width=10)
        self.assertEqual(result, "░" * 10)

    def test_bar_chart_zero_max(self):
        from utils import bar_chart
        result = bar_chart(50, 0, width=10)
        self.assertEqual(result, "░" * 10)


# ── Run tests ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
