def evaluation_summary() -> dict[str, object]:
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

