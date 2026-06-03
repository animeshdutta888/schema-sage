import sqlite3
import time
from dataclasses import dataclass
from random import Random

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
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS customers;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS employees;

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                segment TEXT NOT NULL CHECK (segment IN ('enterprise', 'mid_market', 'smb')),
                signup_date TEXT NOT NULL
            );

            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL CHECK (unit_price >= 0)
            );

            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                order_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                status TEXT NOT NULL CHECK (status IN ('completed', 'processing', 'cancelled', 'refunded'))
            );
            """
        )
        conn.executemany(
            "INSERT INTO customers (id, name, region, segment, signup_date) VALUES (?, ?, ?, ?, ?)",
            build_customers(),
        )
        conn.executemany(
            "INSERT INTO products (id, name, category, unit_price) VALUES (?, ?, ?, ?)",
            build_products(),
        )
        conn.executemany(
            "INSERT INTO employees (id, name, region, role) VALUES (?, ?, ?, ?)",
            build_employees(),
        )
        conn.executemany(
            """
            INSERT INTO orders (id, customer_id, product_id, employee_id, order_date, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            build_orders(),
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


def build_customers() -> list[tuple[int, str, str, str, str]]:
    prefixes = [
        "Northwind", "Alpine", "Sundial", "Canopy", "Vertex", "Harbor", "Summit",
        "Cedar", "Bluebird", "Pioneer", "Evergreen", "Keystone", "Nimbus", "Atlas",
        "Radiant", "Oakline", "Meridian", "Silverline", "Aster", "Brightpath",
    ]
    suffixes = ["Health", "Retail", "Labs", "Foods", "Systems", "Logistics", "Finance", "Media"]
    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
    segments = ["enterprise", "mid_market", "smb"]

    customers = []
    for customer_id in range(1, 81):
        region = regions[(customer_id - 1) % len(regions)]
        segment = segments[(customer_id + (customer_id // 5)) % len(segments)]
        year = 2021 + ((customer_id * 7) % 3)
        month = ((customer_id * 5) % 12) + 1
        day = ((customer_id * 3) % 27) + 1
        customers.append(
            (
                customer_id,
                f"{prefixes[(customer_id - 1) % len(prefixes)]} {suffixes[(customer_id - 1) % len(suffixes)]}",
                region,
                segment,
                f"{year}-{month:02d}-{day:02d}",
            )
        )
    return customers


def build_products() -> list[tuple[int, str, str, float]]:
    catalog = [
        ("Analytics Suite", "Software", 2400.0),
        ("Forecast Engine", "Software", 1850.0),
        ("Data Quality Pack", "Software", 1250.0),
        ("Workflow Automator", "Software", 980.0),
        ("Executive Dashboard", "Software", 3200.0),
        ("API Gateway", "Infrastructure", 2100.0),
        ("Cloud Connector", "Infrastructure", 760.0),
        ("Secure Storage", "Infrastructure", 1450.0),
        ("Observability Kit", "Infrastructure", 1100.0),
        ("Migration Package", "Services", 4200.0),
        ("Onboarding Sprint", "Services", 2800.0),
        ("Premium Support", "Services", 3600.0),
        ("Training Workshop", "Services", 1600.0),
        ("Compliance Review", "Services", 3900.0),
        ("CRM Adapter", "Integrations", 650.0),
        ("ERP Adapter", "Integrations", 900.0),
        ("Warehouse Sync", "Integrations", 1150.0),
        ("Marketing Sync", "Integrations", 720.0),
        ("Mobile Insights", "Analytics", 1350.0),
        ("Revenue Monitor", "Analytics", 1750.0),
        ("Churn Predictor", "Analytics", 2050.0),
        ("Territory Planner", "Analytics", 1550.0),
        ("Security Audit", "Governance", 2600.0),
        ("Access Manager", "Governance", 1700.0),
        ("Policy Center", "Governance", 1500.0),
    ]
    return [(index, name, category, price) for index, (name, category, price) in enumerate(catalog, start=1)]


def build_employees() -> list[tuple[int, str, str, str]]:
    names = [
        "Maya Chen", "Aarav Mehta", "Sofia Rossi", "Liam Carter", "Nora Haddad",
        "Mateo Silva", "Priya Raman", "Ethan Brooks", "Amara Okafor", "Jonas Weber",
        "Iris Kim", "Diego Alvarez", "Leah Morgan", "Samir Khan", "Clara Novak", "Theo Martin",
    ]
    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
    roles = ["Account Executive", "Solutions Consultant", "Customer Success"]
    return [
        (employee_id, name, regions[(employee_id - 1) % len(regions)], roles[(employee_id - 1) % len(roles)])
        for employee_id, name in enumerate(names, start=1)
    ]


def build_orders() -> list[tuple[int, int, int, int, str, float, str]]:
    rng = Random(20240601)
    statuses = ["completed"] * 17 + ["processing"] * 2 + ["refunded"] + ["cancelled"]
    orders = []
    for order_id in range(1, 901):
        customer_id = ((order_id * 37) % 80) + 1
        product_id = ((order_id * 17) % 25) + 1
        employee_id = ((customer_id + product_id + order_id) % 16) + 1
        year = 2023 if order_id <= 150 else 2024
        month = ((order_id * 5) % 12) + 1
        day = ((order_id * 11) % 28) + 1
        base_amount = 450 + (product_id * 185) + ((customer_id % 9) * 130)
        seasonal_lift = 1.08 if month in {3, 6, 9, 12} else 1.0
        amount = round((base_amount * seasonal_lift) + rng.uniform(0, 950), 2)
        status = statuses[(order_id + customer_id + product_id) % len(statuses)]
        orders.append((order_id, customer_id, product_id, employee_id, f"{year}-{month:02d}-{day:02d}", amount, status))
    return orders
