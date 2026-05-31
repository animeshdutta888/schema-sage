# Evaluation Report

Metrics are produced by `scripts/evaluate_text2sql.py` against `data/training/demo_text2sql.jsonl`.
The runner reports exact SQL string match after normalization, execution-result match against the demo SQLite database, valid SQL rate, and average generation latency.

| Model | Exact Match | Execution Accuracy | Valid SQL Rate | Avg Latency |
|---|---:|---:|---:|---:|
| Deterministic rules baseline | 3.9% | 7.8% | 100.0% | 0.00 ms |
| LoRA fine-tuned model | Adapter trained; final eval pending | Adapter trained; final eval pending | Adapter trained; final eval pending | Adapter trained; final eval pending |

The 2026-06-01 local LoRA run used `Qwen/Qwen2.5-Coder-0.5B-Instruct`, rank 8, 1 epoch, 51 training examples, and `max_seq_length=512`. Training completed in 579.5 seconds with final training loss 1.0288.

Run:

```bash
python3 scripts/evaluate_text2sql.py --backend rules --output-file artifacts/eval/rules.json
SCHEMASAGE_GENERATOR_BACKEND=lora python3 scripts/evaluate_text2sql.py --backend lora --output-file artifacts/eval/lora.json --mlflow
```
