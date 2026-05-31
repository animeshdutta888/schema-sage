from schemasage.database import execute_readonly, initialize_demo_database


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
        GROUP BY month, customers.region
        ORDER BY month, customers.region
        """
    )

    assert result.columns == ["month", "region", "revenue"]
    assert result.rows == [
        {"month": "2024-01", "region": "Europe", "revenue": 7000.0},
        {"month": "2024-01", "region": "North America", "revenue": 20000.0},
        {"month": "2024-02", "region": "North America", "revenue": 9000.0},
        {"month": "2024-03", "region": "Europe", "revenue": 15000.0},
    ]


def test_execute_readonly_applies_outer_limit() -> None:
    result = execute_readonly("SELECT id FROM orders ORDER BY id", max_rows=2)
    assert result.rows == [{"id": 1}, {"id": 2}]

