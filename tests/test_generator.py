import json

import schemasage.generator as generator
from schemasage.generator import generate_sql
from schemasage.validator import validate_sql


def test_core_question_generates_valid_schema_grounded_sql() -> None:
    generated = generate_sql("Show monthly revenue by region for enterprise customers in 2024.")
    validation = validate_sql(generated.sql)

    assert validation.valid is True
    assert validation.tables == ["customers", "orders"]
    assert "orders.amount" in generated.sql


def test_extract_sql_from_markdown_fence() -> None:
    sql = generator.extract_sql("```sql\nSELECT id FROM customers;\n```")
    assert sql == "SELECT id FROM customers"


def test_extract_sql_stops_before_extra_training_sections() -> None:
    sql = generator.extract_sql(
        "SELECT id FROM customers;\n\n### Question\nList all orders\n### SQL\nSELECT id FROM orders"
    )
    assert sql == "SELECT id FROM customers"


def test_lora_prompt_matches_training_format() -> None:
    prompt = generator.build_lora_prompt("List customers.")

    assert "### Instruction" in prompt
    assert "### Schema" in prompt
    assert "### Question" in prompt
    assert prompt.endswith("### SQL\n")


def test_generate_sql_can_use_ollama_backend(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"response": "SELECT id, name FROM customers"}).encode("utf-8")

    def fake_urlopen(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(generator, "GENERATOR_BACKEND", "ollama")
    monkeypatch.setattr(generator.urllib.request, "urlopen", fake_urlopen)

    generated = generate_sql("List customers")

    assert generated.source.startswith("ollama:")
    assert generated.sql == "SELECT id, name FROM customers"


def test_ollama_invalid_sql_falls_back_to_executable_rules(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "response": (
                        "SELECT strftime('%Y-%m', orders.order_date), regions.region "
                        "FROM orders JOIN customers ON customers.id = orders.customer_id "
                        "GROUP BY strftime('%Y-%m', orders.order_date), regions.region"
                    )
                }
            ).encode("utf-8")

    def fake_urlopen(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(generator, "GENERATOR_BACKEND", "ollama")
    monkeypatch.setattr(generator.urllib.request, "urlopen", fake_urlopen)

    generated = generate_sql("Show monthly revenue by region for enterprise customers in 2024.")
    validation = validate_sql(generated.sql)

    assert generated.source == "rules_fallback"
    assert validation.valid is True
    assert "customers.region" in generated.sql


def test_region_comparison_rule_groups_by_region() -> None:
    generated = generator.generate_sql_with_rules("Compare Europe and North America revenue in 2024.")
    validation = validate_sql(generated.sql)

    assert validation.valid is True
    assert "customers.region" in generated.sql
    assert "customers.name" not in generated.sql
    assert "GROUP BY customers.region" in generated.sql


def test_all_region_sales_comparison_rule_groups_by_region() -> None:
    generated = generator.generate_sql_with_rules("compare sales in all regions")
    validation = validate_sql(generated.sql)

    assert validation.valid is True
    assert "customers.region" in generated.sql
    assert "SUM(orders.amount)" in generated.sql
    assert "GROUP BY customers.region" in generated.sql
    assert "ORDER BY sales DESC" in generated.sql


def test_top_products_rule_uses_product_schema() -> None:
    generated = generator.generate_sql_with_rules("List the top 5 products by order count")
    validation = validate_sql(generated.sql)

    assert validation.valid is True
    assert validation.tables == ["orders", "products"]
    assert "COUNT(orders.id) AS order_count" in generated.sql
    assert "LIMIT 5" in generated.sql


def test_frequent_customers_rule_counts_orders() -> None:
    generated = generator.generate_sql_with_rules("Which customers placed more than 3 orders?")
    validation = validate_sql(generated.sql)

    assert validation.valid is True
    assert validation.tables == ["customers", "orders"]
    assert "HAVING COUNT(orders.id) > 3" in generated.sql


def test_lora_generation_accepts_valid_sql_without_semantic_hardcoded_fallback(monkeypatch) -> None:
    class FakeLoraGenerator:
        tokenizer = type("Tokenizer", (), {"eos_token_id": 0})()

        def __call__(self, *args: object, **kwargs: object) -> list[dict[str, str]]:
            return [
                {
                    "generated_text": (
                        "SELECT customers.region, ROUND(SUM(orders.amount), 2) AS revenue "
                        "FROM orders JOIN customers ON customers.id = orders.customer_id "
                        "WHERE orders.order_date >= '2024-01-01' "
                        "AND orders.order_date < '2025-01-01' "
                        "AND customers.region IN ('Europe', 'North America') "
                        "GROUP BY customers.region ORDER BY revenue DESC"
                    )
                }
            ]

    monkeypatch.setattr(generator, "load_lora_generator", lambda: FakeLoraGenerator())

    generated = generator.generate_sql_with_lora("Compare Europe and North America revenue in 2024.")

    assert generated.source.startswith("lora:")
    assert "customers.region" in generated.sql


def test_lora_generation_falls_back_for_monthly_revenue_semantic_issue(monkeypatch) -> None:
    class FakeLoraGenerator:
        tokenizer = type("Tokenizer", (), {"eos_token_id": 0})()

        def __call__(self, *args: object, **kwargs: object) -> list[dict[str, str]]:
            return [
                {
                    "generated_text": (
                        'SELECT SUM(amount), T1.region FROM customers AS T1 '
                        'JOIN orders AS T2 ON T1.id = T2.customer_id '
                        'WHERE T1.segment = "Enterprise" AND T2.order_date LIKE "%2024-%" '
                        "GROUP BY T1.region ORDER BY SUM(amount) DESC LIMIT 10"
                    )
                }
            ]

    monkeypatch.setattr(generator, "load_lora_generator", lambda: FakeLoraGenerator())

    generated = generator.generate_sql_with_lora(
        "Show monthly revenue by region for enterprise customers in 2024."
    )

    assert generated.source == "rules_fallback"
    assert "strftime('%Y-%m', orders.order_date) AS month" in generated.sql
    assert "customers.segment = 'enterprise'" in generated.sql
