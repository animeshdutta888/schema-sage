from __future__ import annotations

import json
from pathlib import Path


LATEST_EVAL = Path("artifacts/eval/latest.json")


def evaluation_summary() -> dict[str, object]:
    if LATEST_EVAL.exists():
        payload = json.loads(LATEST_EVAL.read_text())
        return {
            "status": "complete",
            "backend": payload.get("backend", "unknown"),
            "eval_file": payload.get("eval_file", "unknown"),
            "example_count": payload.get("example_count", 0),
            "metrics": {
                "exact_match": payload.get("exact_match"),
                "execution_accuracy": payload.get("execution_accuracy"),
                "valid_sql_rate": payload.get("valid_sql_rate"),
                "avg_latency_ms": payload.get("avg_latency_ms"),
            },
        }

    return {
        "status": "not_run",
        "metrics": [
            {
                "model": "Base model",
                "exact_match": "TBD",
                "execution_accuracy": "TBD",
                "valid_sql_rate": "TBD",
                "avg_latency": "TBD",
            },
            {
                "model": "Schema-aware prompt",
                "exact_match": "TBD",
                "execution_accuracy": "TBD",
                "valid_sql_rate": "TBD",
                "avg_latency": "TBD",
            },
            {
                "model": "LoRA fine-tuned model",
                "exact_match": "TBD",
                "execution_accuracy": "TBD",
                "valid_sql_rate": "TBD",
                "avg_latency": "TBD",
            },
        ],
    }
