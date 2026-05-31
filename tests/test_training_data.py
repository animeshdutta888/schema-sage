import json
from pathlib import Path

from schemasage.validator import validate_sql


TRAINING_DATA = Path("data/training/demo_text2sql.jsonl")


def test_training_data_is_valid_jsonl_with_executable_sql() -> None:
    rows = [json.loads(line) for line in TRAINING_DATA.read_text().splitlines() if line.strip()]

    assert len(rows) >= 40
    assert any("DATE_TRUNC" in row["question"] for row in rows)
    assert any("regions table" in row["question"] for row in rows)

    for row in rows:
        assert row["instruction"]
        assert "customers" in row["schema"]
        assert "orders" in row["schema"]
        assert row["question"]
        validation = validate_sql(row["sql"])
        assert validation.valid is True, f"{row['question']}: {validation.reason}"
