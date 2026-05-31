import re

from schemasage.models import ValidationResult

FORBIDDEN_KEYWORDS = {
    "alter",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "pragma",
    "replace",
    "truncate",
    "update",
    "vacuum",
}

TABLE_REFERENCE_PATTERN = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", re.IGNORECASE)
CTE_NAME_PATTERN = re.compile(r"(?:\bwith|,)\s+([a-zA-Z_][\w]*)\s+as\s*\(", re.IGNORECASE)


def normalize_sql(sql: str) -> str:
    normalized = sql.strip()
    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()
    return normalized


def validate_sql(sql: str) -> ValidationResult:
    from schemasage.database import compile_sql
    from schemasage.schema import known_table_names

    normalized = normalize_sql(sql)
    if not normalized:
        return ValidationResult(valid=False, reason="SQL is empty.")

    if "--" in normalized or "/*" in normalized or "*/" in normalized:
        return ValidationResult(valid=False, reason="SQL comments are not allowed.")

    if ";" in normalized:
        return ValidationResult(valid=False, reason="Multiple SQL statements are not allowed.")

    first_token = normalized.split(None, 1)[0].lower()
    if first_token not in {"select", "with"}:
        return ValidationResult(valid=False, reason="Only SELECT and WITH queries are allowed.")

    tokens = {token.lower() for token in re.findall(r"\b[a-zA-Z_][\w]*\b", normalized)}
    blocked = sorted(tokens & FORBIDDEN_KEYWORDS)
    if blocked:
        return ValidationResult(valid=False, reason=f"Forbidden SQL keyword: {blocked[0]}.")

    cte_names = {match.group(1) for match in CTE_NAME_PATTERN.finditer(normalized)}
    table_names = [match.group(1) for match in TABLE_REFERENCE_PATTERN.finditer(normalized)]
    known_tables = known_table_names()
    unknown_tables = sorted({table for table in table_names if table not in known_tables and table not in cte_names})
    if unknown_tables:
        return ValidationResult(valid=False, reason=f"Unknown table: {unknown_tables[0]}.")

    try:
        compile_sql(normalized)
    except Exception as exc:
        return ValidationResult(valid=False, reason=f"SQL does not compile: {exc}")

    return ValidationResult(
        valid=True,
        reason="SQL is safe to execute.",
        normalized_sql=normalized,
        tables=sorted({table for table in table_names if table in known_tables}),
    )
