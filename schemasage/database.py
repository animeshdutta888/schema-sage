import sqlite3
import time
from dataclasses import dataclass

from schemasage.config import DEMO_DB_PATH
from schemasage.validator import normalize_sql, validate_sql


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, object]]


def initialize_demo_database() -> None:
    DEMO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                segment TEXT NOT NULL CHECK (segment IN ('enterprise', 'mid_market', 'smb'))
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                order_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0)
            );
            """
        )
        customer_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if customer_count:
            return
        conn.executemany(
            "INSERT INTO customers (id, name, region, segment) VALUES (?, ?, ?, ?)",
            [
                (1, "Northwind Health", "North America", "enterprise"),
                (2, "Alpine Retail", "Europe", "enterprise"),
                (3, "Sundial Labs", "Asia Pacific", "mid_market"),
                (4, "Canopy Foods", "North America", "smb"),
            ],
        )
        conn.executemany(
            "INSERT INTO orders (id, customer_id, order_date, amount) VALUES (?, ?, ?, ?)",
            [
                (1, 1, "2024-01-15", 12000.00),
                (2, 1, "2024-01-30", 8000.00),
                (3, 1, "2024-02-14", 9000.00),
                (4, 2, "2024-01-21", 7000.00),
                (5, 2, "2024-03-05", 15000.00),
                (6, 3, "2024-01-17", 3000.00),
                (7, 4, "2024-02-10", 1500.00),
                (8, 1, "2023-12-10", 4000.00),
            ],
        )


def readonly_connection() -> sqlite3.Connection:
    initialize_demo_database()
    uri = f"file:{DEMO_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def compile_sql(sql: str) -> None:
    with readonly_connection() as conn:
        conn.execute(f"EXPLAIN QUERY PLAN {normalize_sql(sql)}")


def execute_readonly(sql: str, *, max_rows: int = 100, timeout_seconds: float = 2.0) -> QueryResult:
    validation = validate_sql(sql)
    if not validation.valid:
        raise ValueError(validation.reason)

    bounded_max_rows = max(1, min(max_rows, 500))
    wrapped_sql = f"SELECT * FROM ({normalize_sql(sql)}) LIMIT ?"
    deadline = time.monotonic() + timeout_seconds

    with readonly_connection() as conn:
        def stop_when_expired() -> int:
            return int(time.monotonic() > deadline)

        conn.set_progress_handler(stop_when_expired, 1000)
        cursor = conn.execute(wrapped_sql, (bounded_max_rows,))
        columns = [description[0] for description in cursor.description or []]
        rows = [dict(row) for row in cursor.fetchall()]
        return QueryResult(columns=columns, rows=rows)

