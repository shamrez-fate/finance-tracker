"""
database.py — SQLite persistence layer for Finance Tracker.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path.home() / ".finance_tracker" / "finance.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection with row_factory set for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    """Create tables and seed default categories if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL UNIQUE,
                type    TEXT    NOT NULL CHECK(type IN ('income','expense')),
                color   TEXT    NOT NULL DEFAULT '#6C63FF'
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT    NOT NULL CHECK(type IN ('income','expense')),
                amount      REAL    NOT NULL CHECK(amount > 0),
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                description TEXT,
                date        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Seed default categories
        default_income = [
            ("Salary", "income", "#2ECC71"),
            ("Freelance", "income", "#27AE60"),
            ("Investment", "income", "#1ABC9C"),
            ("Business", "income", "#16A085"),
            ("Gift", "income", "#52BE80"),
            ("Other Income", "income", "#58D68D"),
        ]
        default_expense = [
            ("Food & Dining", "expense", "#E74C3C"),
            ("Housing", "expense", "#C0392B"),
            ("Transport", "expense", "#E67E22"),
            ("Healthcare", "expense", "#D35400"),
            ("Shopping", "expense", "#9B59B6"),
            ("Entertainment", "expense", "#8E44AD"),
            ("Education", "expense", "#2980B9"),
            ("Utilities", "expense", "#1F618D"),
            ("Travel", "expense", "#F39C12"),
            ("Other Expense", "expense", "#7F8C8D"),
        ]
        for row in default_income + default_expense:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, type, color) VALUES (?, ?, ?)",
                row,
            )


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------

def fetch_categories(type_filter: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if type_filter:
            rows = conn.execute(
                "SELECT * FROM categories WHERE type = ? ORDER BY name", (type_filter,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM categories ORDER BY type, name").fetchall()
    return [dict(r) for r in rows]


def add_category(name: str, type_: str, color: str = "#6C63FF") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, type, color) VALUES (?, ?, ?)",
            (name, type_, color),
        )
        return cur.lastrowid


def delete_category(category_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# ---------------------------------------------------------------------------
# Transaction helpers
# ---------------------------------------------------------------------------

def add_transaction(
    type_: str,
    amount: float,
    category_id: int | None,
    description: str,
    date: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions (type, amount, category_id, description, date)
               VALUES (?, ?, ?, ?, ?)""",
            (type_, amount, category_id, description, date),
        )
        return cur.lastrowid


def update_transaction(
    tx_id: int,
    type_: str,
    amount: float,
    category_id: int | None,
    description: str,
    date: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE transactions
               SET type=?, amount=?, category_id=?, description=?, date=?
               WHERE id=?""",
            (type_, amount, category_id, description, date, tx_id),
        )


def delete_transaction(tx_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))


def fetch_transactions(
    type_filter: str | None = None,
    category_id: int | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 500,
) -> list[dict]:
    query = """
        SELECT t.id, t.type, t.amount, t.description, t.date,
               c.name AS category, c.color
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE 1=1
    """
    params: list = []

    if type_filter:
        query += " AND t.type = ?"
        params.append(type_filter)
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (t.description LIKE ? OR c.name LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)

    query += " ORDER BY t.date DESC, t.id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def monthly_summary(year: int, month: int) -> dict:
    """Return income, expense, net, and per-category breakdown for a month."""
    month_str = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        totals = conn.execute(
            """SELECT type, SUM(amount) AS total
               FROM transactions
               WHERE strftime('%Y-%m', date) = ?
               GROUP BY type""",
            (month_str,),
        ).fetchall()

        by_category = conn.execute(
            """SELECT c.name, c.color, t.type, SUM(t.amount) AS total
               FROM transactions t
               LEFT JOIN categories c ON c.id = t.category_id
               WHERE strftime('%Y-%m', t.date) = ?
               GROUP BY t.category_id, t.type
               ORDER BY total DESC""",
            (month_str,),
        ).fetchall()

    income = next((r["total"] for r in totals if r["type"] == "income"), 0.0)
    expense = next((r["total"] for r in totals if r["type"] == "expense"), 0.0)
    return {
        "income": income,
        "expense": expense,
        "net": income - expense,
        "by_category": [dict(r) for r in by_category],
    }


def monthly_trend(months: int = 12) -> list[dict]:
    """Return income/expense per month for the last N months."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', date) AS month,
                      type, SUM(amount) AS total
               FROM transactions
               GROUP BY month, type
               ORDER BY month DESC
               LIMIT ?""",
            (months * 2,),
        ).fetchall()
    return [dict(r) for r in rows]