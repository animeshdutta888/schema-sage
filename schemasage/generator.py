from dataclasses import dataclass
from functools import lru_cache
import json
import re
import urllib.error
import urllib.request

from schemasage.config import (
    GENERATOR_BACKEND,
    LORA_ADAPTER_PATH,
    LORA_BASE_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from schemasage.schema import serialize_schema_for_prompt
from schemasage.validator import validate_sql


@dataclass(frozen=True)
class GeneratedSql:
    sql: str
    explanation: str
    source: str = "rules"


def generate_sql(question: str) -> GeneratedSql:
    if GENERATOR_BACKEND == "ollama":
        return generate_sql_with_ollama(question)
    if GENERATOR_BACKEND == "lora":
        return generate_sql_with_lora(question)
    return generate_sql_with_rules(question)


def generate_sql_with_rules(question: str) -> GeneratedSql:
    normalized = " ".join(question.lower().split())
    if (
        any(term in normalized for term in ["compare", "breakdown", "by region"])
        and any(term in normalized for term in ["sales", "revenue"])
        and any(term in normalized for term in ["region", "regions"])
        and "monthly" not in normalized
    ):
        return GeneratedSql(
            sql="""
            SELECT
              customers.region,
              ROUND(SUM(orders.amount), 2) AS sales
            FROM orders
            JOIN customers ON customers.id = orders.customer_id
            GROUP BY customers.region
            ORDER BY sales DESC
            """,
            explanation=(
                "Compares total sales across all regions by summing orders.amount "
                "joined to customers.region."
            ),
            source="rules",
        )

    if all(term in normalized for term in ["compare", "europe", "north america", "revenue", "2024"]):
        return GeneratedSql(
            sql="""
            SELECT
              customers.region,
              ROUND(SUM(orders.amount), 2) AS revenue
            FROM orders
            JOIN customers ON customers.id = orders.customer_id
            WHERE orders.order_date >= '2024-01-01'
              AND orders.order_date < '2025-01-01'
              AND customers.region IN ('Europe', 'North America')
            GROUP BY customers.region
            ORDER BY revenue DESC
            """,
            explanation=(
                "Compares 2024 revenue at the region grain for Europe and North America, "
                "using orders.amount joined to customers.region."
            ),
            source="rules",
        )

    if all(term in normalized for term in ["monthly", "revenue", "region", "enterprise", "2024"]):
        return GeneratedSql(
            sql="""
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
            """,
            explanation=(
                "Uses orders.amount and orders.order_date joined to customers.region. "
                "Filters to enterprise customers and 2024 order dates, then groups by month and region."
            ),
            source="rules",
        )

    if "customers" in normalized:
        return GeneratedSql(
            sql="SELECT id, name, region, segment FROM customers ORDER BY id",
            explanation="Lists customers from the demo customer table.",
            source="rules",
        )

    return GeneratedSql(
        sql="SELECT id, customer_id, order_date, amount FROM orders ORDER BY order_date, id",
        explanation="Lists orders from the demo orders table.",
        source="rules",
    )


def generate_sql_with_ollama(question: str) -> GeneratedSql:
    prompt = build_text2sql_prompt(question)
    request_body = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 512},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=f"Ollama/Qwen unavailable, used deterministic fallback. {fallback.explanation}",
            source="rules_fallback",
        )

    sql = extract_sql(payload.get("response", ""))
    if not sql:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=f"Qwen did not return parseable SQL, used deterministic fallback. {fallback.explanation}",
            source="rules_fallback",
        )
    validation = validate_sql(sql)
    if not validation.valid:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=(
                "Qwen returned SQL that failed validation "
                f"({validation.reason}), so SchemaSage used the deterministic fallback. "
                f"{fallback.explanation}"
            ),
            source="rules_fallback",
        )
    quality_issue = semantic_quality_issue(question, sql)
    if quality_issue:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=(
                f"Qwen returned valid SQL, but SchemaSage detected a semantic issue ({quality_issue}), "
                f"so it used the deterministic fallback. {fallback.explanation}"
            ),
            source="rules_fallback",
        )
    return GeneratedSql(
        sql=sql,
        explanation="Generated by Qwen through Ollama using the live demo schema.",
        source=f"ollama:{OLLAMA_MODEL}",
    )


def generate_sql_with_lora(question: str) -> GeneratedSql:
    try:
        generator = load_lora_generator()
    except ImportError:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=f"LoRA dependencies are not installed, used deterministic fallback. {fallback.explanation}",
            source="rules_fallback",
        )
    except OSError as exc:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=f"LoRA adapter/model could not be loaded ({exc}), used deterministic fallback. {fallback.explanation}",
            source="rules_fallback",
        )

    prompt = build_lora_prompt(question)
    result = generator(
        prompt,
        max_new_tokens=180,
        do_sample=False,
        return_full_text=False,
        pad_token_id=generator.tokenizer.eos_token_id,
    )[0]
    output = result.get("generated_text", "")
    sql = extract_sql(output)
    if not sql:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=f"LoRA model did not return parseable SQL, used deterministic fallback. {fallback.explanation}",
            source="rules_fallback",
        )
    validation = validate_sql(sql)
    if not validation.valid:
        fallback = generate_sql_with_rules(question)
        return GeneratedSql(
            sql=fallback.sql,
            explanation=(
                "LoRA model returned SQL that failed validation "
                f"({validation.reason}), so SchemaSage used the deterministic fallback. "
                f"{fallback.explanation}"
            ),
            source="rules_fallback",
        )
    return GeneratedSql(
        sql=sql,
        explanation="Generated by the configured Qwen LoRA/PEFT adapter using the live demo schema.",
        source=f"lora:{LORA_ADAPTER_PATH}",
    )


@lru_cache(maxsize=1)
def load_lora_generator():
    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError as exc:
        raise ImportError("Install LoRA dependencies with python3 -m pip install '.[lora]'") from exc

    tokenizer = AutoTokenizer.from_pretrained(LORA_BASE_MODEL)
    base_model = AutoModelForCausalLM.from_pretrained(LORA_BASE_MODEL, device_map="auto")
    model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_PATH)
    return pipeline("text-generation", model=model, tokenizer=tokenizer)


def build_text2sql_prompt(question: str) -> str:
    return f"""You are SchemaSage, a Text2SQL assistant.
Generate one safe SQLite SELECT query for the user's question.
Use only the provided schema. Do not include comments, markdown, or explanations.
Do not reference aliases, tables, or columns that are not present in the SQL.
If you create a subquery alias, select columns from that alias, not from the original table name.
The customers table has region; there is no regions table.

Schema:
{serialize_schema_for_prompt()}

Question:
{question}

SQL:
"""


def build_lora_prompt(question: str) -> str:
    return f"""### Instruction
Generate one SQLite SELECT query for the given question and schema. Return SQL only.

### Schema
{serialize_schema_for_prompt()}

### Question
{question}

### SQL
"""


def extract_sql(text: str) -> str:
    fenced_match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    candidate = fenced_match.group(1) if fenced_match else text
    candidate = re.split(r"\n\s*###\s+", candidate, maxsplit=1)[0]
    select_match = re.search(r"\b(with|select)\b.*", candidate, flags=re.IGNORECASE | re.DOTALL)
    if not select_match:
        return ""
    sql = select_match.group(0).strip()
    sql = sql.split(";")[0].strip()
    return sql


def semantic_quality_issue(question: str, sql: str) -> str | None:
    normalized_question = " ".join(question.lower().split())
    normalized_sql = " ".join(sql.lower().split())

    if all(term in normalized_question for term in ["compare", "europe", "north america", "revenue"]):
        select_clause = _select_clause(normalized_sql)
        group_clause = _group_by_clause(normalized_sql)
        if "region" not in select_clause:
            return "region comparison must include region in SELECT"
        if "name" in select_clause or "customer" in select_clause:
            return "region comparison should not be grouped at customer grain"
        if "region" not in group_clause:
            return "region comparison must group by region"

    if "monthly" in normalized_question and "revenue" in normalized_question:
        select_clause = _select_clause(normalized_sql)
        if "strftime('%y-%m'" not in select_clause and "strftime('%Y-%m'".lower() not in select_clause:
            return "monthly revenue must include a visible month column"

    return None


def _select_clause(normalized_sql: str) -> str:
    match = re.search(r"\bselect\b(.*?)\bfrom\b", normalized_sql, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def _group_by_clause(normalized_sql: str) -> str:
    match = re.search(
        r"\bgroup\s+by\b(.*?)(?:\border\s+by\b|\bhaving\b|\blimit\b|$)",
        normalized_sql,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else ""
