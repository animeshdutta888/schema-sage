import pytest

from schemasage.database import execute_readonly, initialize_demo_database
from schemasage.validator import normalize_sql, validate_sql


@pytest.mark.parametrize(
    "sql, reason",
    [
        ("", "SQL is empty."),
        ("DELETE FROM customers", "Only SELECT and WITH queries are allowed."),
        ("SELECT * FROM customers; SELECT * FROM orders", "Multiple SQL statements are not allowed."),
        ("SELECT * FROM customers -- hide", "SQL comments are not allowed."),
        ("SELECT * FROM missing_table", "Unknown table: missing_table."),
        ("SELECT missing_column FROM customers", "SQL does not compile: no such column: missing_column"),
        ("WITH deleted AS (DELETE FROM customers RETURNING *) SELECT * FROM deleted", "Forbidden SQL keyword: delete."),
    ],
)
def test_validate_sql_rejects_unsafe_or_invalid_sql(sql: str, reason: str) -> None:
    initialize_demo_database()
    result = validate_sql(sql)
    assert result.valid is False
    assert result.reason == reason


def test_validate_sql_accepts_select_with_join() -> None:
    result = validate_sql(
        """
        SELECT customers.region, SUM(orders.amount) AS revenue
        FROM orders
        JOIN customers ON customers.id = orders.customer_id
        GROUP BY customers.region
        """
    )

    assert result.valid is True
    assert result.tables == ["customers", "orders"]


def test_validate_sql_accepts_cte_names() -> None:
    result = validate_sql(
        """
        WITH enterprise_customers AS (
          SELECT id, region
          FROM customers
          WHERE segment = 'enterprise'
        )
        SELECT enterprise_customers.region, SUM(orders.amount) AS revenue
        FROM enterprise_customers
        JOIN orders ON orders.customer_id = enterprise_customers.id
        GROUP BY enterprise_customers.region
        """
    )

    assert result.valid is True
    assert result.tables == ["customers", "orders"]


def test_normalize_sql_removes_single_trailing_semicolon() -> None:
    assert normalize_sql("SELECT * FROM customers;") == "SELECT * FROM customers"


def test_execute_readonly_revalidates_sql() -> None:
    with pytest.raises(ValueError, match="Only SELECT"):
        execute_readonly("UPDATE customers SET name = 'bad'")
