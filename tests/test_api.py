from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_recruiter_demo_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SchemaSage" in response.text
    assert "Generate SQL" in response.text


def test_schemas_lists_demo_tables() -> None:
    response = client.get("/schemas")
    assert response.status_code == 200
    table_names = {table["name"] for table in response.json()["tables"]["tables"]}
    assert table_names == {"customers", "orders"}


def test_generate_returns_valid_sql_for_core_demo_question() -> None:
    response = client.post(
        "/generate",
        json={"question": "Show monthly revenue by region for enterprise customers in 2024."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["valid"] is True
    assert "GROUP BY month, customers.region" in payload["sql"]


def test_execute_rejects_mutation() -> None:
    response = client.post("/execute", json={"sql": "DROP TABLE customers"})
    assert response.status_code == 400
    assert response.json()["detail"]["valid"] is False
