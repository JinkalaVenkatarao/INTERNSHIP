"""
expense.py - Expense class definition for Personal Finance Manager
"""

from datetime import datetime


class Expense:
    """Represents a single financial expense."""

    VALID_CATEGORIES = [
        "Food & Dining",
        "Transportation",
        "Shopping",
        "Entertainment",
        "Health & Medical",
        "Housing & Utilities",
        "Education",
        "Travel",
        "Personal Care",
        "Savings & Investment",
        "Other"
    ]

    def __init__(self, amount: float, category: str, date: str, description: str, expense_id: int = None):
        """
        Initialize an Expense object.

        Args:
            amount (float): The expense amount (must be positive)
            category (str): The expense category
            date (str): The date in YYYY-MM-DD format
            description (str): A brief description of the expense
            expense_id (int, optional): Unique identifier for the expense
        """
        self.expense_id = expense_id
        self.amount = self._validate_amount(amount)
        self.category = self._validate_category(category)
        self.date = self._validate_date(date)
        self.description = self._validate_description(description)

    def _validate_amount(self, amount) -> float:
        """Validate and return the amount."""
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            return round(amount, 2)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid amount: '{amount}'. Please enter a positive number.")

    def _validate_category(self, category: str) -> str:
        """Validate and return the category."""
        category = str(category).strip()
        if category not in self.VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category: '{category}'.\n"
                f"Valid categories: {', '.join(self.VALID_CATEGORIES)}"
            )
        return category

    def _validate_date(self, date: str) -> str:
        """Validate and return the date string."""
        date = str(date).strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
            return date
        except ValueError:
            raise ValueError(f"Invalid date: '{date}'. Use format YYYY-MM-DD (e.g., 2024-01-15).")

    def _validate_description(self, description: str) -> str:
        """Validate and return the description."""
        description = str(description).strip()
        if not description:
            raise ValueError("Description cannot be empty.")
        if len(description) > 100:
            raise ValueError("Description cannot exceed 100 characters.")
        return description

    def to_dict(self) -> dict:
        """Convert expense to a dictionary (for CSV storage)."""
        return {
            "id": self.expense_id,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Create an Expense object from a dictionary (from CSV row)."""
        return cls(
            amount=float(data["amount"]),
            category=data["category"],
            date=data["date"],
            description=data["description"],
            expense_id=int(data["id"]) if data.get("id") else None
        )

    def __str__(self) -> str:
        return (
            f"[ID: {self.expense_id:>4}] "
            f"{self.date} | "
            f"{self.category:<22} | "
            f"₹{self.amount:>10,.2f} | "
            f"{self.description}"
        )

    def __repr__(self) -> str:
        return f"Expense(id={self.expense_id}, amount={self.amount}, category='{self.category}', date='{self.date}')"
