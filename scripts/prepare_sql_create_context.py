from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INSTRUCTION = (
    "Generate one safe SQL SELECT query for the question using only the provided schema."
)


def convert_example(example: dict[str, Any], instruction: str = DEFAULT_INSTRUCTION) -> dict[str, str]:
    return {
        "instruction": instruction,
        "schema": str(example["context"]).strip(),
        "question": str(example["question"]).strip(),
        "sql": str(example["answer"]).strip(),
    }


def write_jsonl(examples: list[dict[str, str]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert b-mc2/sql-create-context into SchemaSage JSONL training format."
    )
    parser.add_argument("--dataset", default="b-mc2/sql-create-context")
    parser.add_argument("--split", default="train")
    parser.add_argument("--output-file", default="data/training/sql_create_context_10k.jsonl")
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    args = parser.parse_args()

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install dataset dependencies with python3 -m pip install -e '.[lora]'.") from exc

    dataset = load_dataset(args.dataset, split=args.split)
    if args.limit:
        dataset = dataset.shuffle(seed=args.seed).select(range(min(args.limit, len(dataset))))

    examples = [convert_example(dict(example), instruction=args.instruction) for example in dataset]
    write_jsonl(examples, Path(args.output_file))
    print(f"Wrote {len(examples)} examples to {args.output_file}")


if __name__ == "__main__":
    main()
