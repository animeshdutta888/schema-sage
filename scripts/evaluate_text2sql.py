from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemasage.database import execute_readonly
from schemasage.generator import GeneratedSql, generate_sql_with_lora, generate_sql_with_rules
from schemasage.validator import normalize_sql, validate_sql


def load_examples(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def rows_match(candidate_sql: str, expected_sql: str) -> bool:
    try:
        candidate = execute_readonly(candidate_sql).rows
        expected = execute_readonly(expected_sql).rows
    except Exception:
        return False
    return candidate == expected


def evaluate(
    examples: list[dict[str, str]],
    generate: Callable[[str], GeneratedSql],
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    start = time.perf_counter()

    for example in examples:
        row_start = time.perf_counter()
        generated = generate(example["question"])
        latency_ms = (time.perf_counter() - row_start) * 1000
        validation = validate_sql(generated.sql)
        exact_match = normalize_sql(generated.sql) == normalize_sql(example["sql"])
        execution_match = validation.valid and rows_match(generated.sql, example["sql"])
        results.append(
            {
                "question": example["question"],
                "expected_sql": normalize_sql(example["sql"]),
                "generated_sql": normalize_sql(generated.sql),
                "source": generated.source,
                "valid": validation.valid,
                "validation_reason": validation.reason,
                "exact_match": exact_match,
                "execution_match": execution_match,
                "latency_ms": round(latency_ms, 2),
            }
        )

    total = len(results)
    elapsed = time.perf_counter() - start
    return {
        "example_count": total,
        "exact_match": sum(row["exact_match"] for row in results) / total,
        "execution_accuracy": sum(row["execution_match"] for row in results) / total,
        "valid_sql_rate": sum(row["valid"] for row in results) / total,
        "avg_latency_ms": round(sum(row["latency_ms"] for row in results) / total, 2),
        "total_runtime_seconds": round(elapsed, 2),
        "results": results,
    }


def log_to_mlflow(run_name: str, metrics: dict[str, object], artifact_path: Path) -> None:
    try:
        import mlflow
    except ImportError as exc:
        raise SystemExit("MLflow logging requested but mlflow is not installed. Install with .[lora].") from exc

    mlflow.set_experiment("schemasage-text2sql")
    with mlflow.start_run(run_name=run_name):
        for key in ["exact_match", "execution_accuracy", "valid_sql_rate", "avg_latency_ms"]:
            mlflow.log_metric(key, float(metrics[key]))
        mlflow.log_param("example_count", int(metrics["example_count"]))
        mlflow.log_artifact(str(artifact_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SchemaSage Text2SQL exact and execution match.")
    parser.add_argument("--eval-file", default="data/training/demo_text2sql.jsonl")
    parser.add_argument("--backend", choices=["rules", "lora"], default=os.getenv("SCHEMASAGE_GENERATOR_BACKEND", "rules"))
    parser.add_argument("--output-file", default="artifacts/eval/latest.json")
    parser.add_argument("--mlflow", action="store_true", help="Log aggregate metrics and output artifact to MLflow.")
    args = parser.parse_args()

    examples = load_examples(Path(args.eval_file))
    generator = generate_sql_with_lora if args.backend == "lora" else generate_sql_with_rules
    metrics = evaluate(examples, generator)
    metrics["backend"] = args.backend
    metrics["eval_file"] = args.eval_file

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n")

    print(
        f"{args.backend}: exact_match={metrics['exact_match']:.3f} "
        f"execution_accuracy={metrics['execution_accuracy']:.3f} "
        f"valid_sql_rate={metrics['valid_sql_rate']:.3f} "
        f"avg_latency_ms={metrics['avg_latency_ms']:.2f}"
    )
    print(f"Wrote {output_path}")

    if args.mlflow:
        log_to_mlflow(f"{args.backend}-eval", metrics, output_path)


if __name__ == "__main__":
    main()
