from schemasage.database import execute_readonly, initialize_demo_database


def test_initialize_demo_database_seeds_demoable_dataset() -> None:
    initialize_demo_database()

    assert execute_readonly("SELECT COUNT(*) AS count FROM customers").rows == [{"count": 80}]
    assert execute_readonly("SELECT COUNT(*) AS count FROM orders").rows == [{"count": 900}]
    assert execute_readonly("SELECT COUNT(*) AS count FROM products").rows == [{"count": 25}]
    assert execute_readonly("SELECT COUNT(*) AS count FROM employees").rows == [{"count": 16}]


def test_execute_readonly_returns_monthly_revenue() -> None:
    initialize_demo_database()
    result = execute_readonly(
        """
        SELECT
          strftime('%Y-%m', orders.order_date) AS month,
          customers.region,
          ROUND(SUM(orders.amount), 2) AS revenue
        FROM orders
        JOIN customers ON customers.id = orders.customer_id
        WHERE customers.segment = 'enterprise'
          AND orders.order_date >= '2024-01-01'
          AND orders.order_date < '2025-01-01'
          AND orders.status = 'completed'
        GROUP BY month, customers.region
        ORDER BY month, customers.region
        """
    )

    assert result.columns == ["month", "region", "revenue"]
    assert len(result.rows) > 12
    assert all(row["revenue"] > 0 for row in result.rows)


def test_execute_readonly_applies_outer_limit() -> None:
    result = execute_readonly("SELECT id FROM orders ORDER BY id", max_rows=2)
    assert result.rows == [{"id": 1}, {"id": 2}]
