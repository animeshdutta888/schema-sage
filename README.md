# SchemaSage

SchemaSage is a schema-aware Text2SQL demo service. It turns natural-language analytics questions into SQLite `SELECT` queries, validates the generated SQL, and executes it through a read-only database connection.

The default backend is deterministic and requires no model downloads, so the API and demo UI start quickly. Optional Ollama/Qwen and LoRA/PEFT paths are available for local model-backed demos.

## Features

- FastAPI service with health, schema, generation, execution, and evaluation endpoints.
- Static browser UI served from the API root.
- Strict SQL validation before execution.
- Read-only SQLite execution with row limits and query timeout protection.
- Deterministic fallback generation for reliable demos.
- Optional Ollama/Qwen backend.
- Optional LoRA/PEFT training and inference flow.
- Pytest coverage for API, validator, generation, training data, and database behavior.

## Project Layout

```text
api/                 FastAPI application
schemasage/          Core generation, validation, schema, and database modules
static/              Demo UI assets
data/training/       Small versioned training examples
docs/                Evaluation notes and supporting docs
scripts/             Run, training, model, and repository safety helpers
tests/               Automated tests
```

Generated files are intentionally ignored, including `data/demo/*.sqlite3`, `artifacts/`, `build/`, and `*.egg-info/`.

## Quickstart

```bash
cd schema-sage
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[dev]'
python3 -m pytest
python3 -m uvicorn api.main:app --reload
```

Open:

- Demo UI: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Configuration

Copy `.env.example` to `.env` for local overrides. Do not commit `.env`.

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `8000` | Server port used by `scripts/serve.sh` and Docker. |
| `SCHEMASAGE_GENERATOR_BACKEND` | `rules` | Generation backend: `rules`, `ollama`, or `lora`. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL. |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Ollama model name. |
| `LORA_BASE_MODEL` | `Qwen/Qwen2.5-Coder-0.5B-Instruct` | Hugging Face base model for LoRA inference/training. |
| `LORA_ADAPTER_PATH` | `artifacts/lora/schemasage-qwen-0.5b-adapter` | Local adapter path. Keep this out of Git. |

## API Example

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'content-type: application/json' \
  -d '{"question":"Show monthly revenue by region for enterprise customers in 2024."}'
```

Run validated SQL:

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'content-type: application/json' \
  -d '{"sql":"SELECT id, name, region, segment FROM customers ORDER BY id","max_rows":50}'
```

## Docker

Build and run the deterministic demo image:

```bash
docker build -t schemasage .
docker run --rm -p 8000:8000 --env-file .env schemasage
```

The container creates the demo SQLite database at runtime. Model adapters and checkpoints are not copied into the image.

## Deployment

SchemaSage can be deployed anywhere that runs a Python web process.

1. Set the start command to `sh scripts/serve.sh`.
2. Set `PORT` if your platform provides a required port.
3. Keep `SCHEMASAGE_GENERATOR_BACKEND=rules` for the lightest deployment.
4. Use the Dockerfile when the platform supports container deploys.
5. Mount or download model artifacts at runtime if using `lora`; do not bake private or large artifacts into the Git repo.

For production-style exposure, put the app behind HTTPS and an auth layer before connecting it to non-demo data.

## Optional Model Backends

Use Qwen through Ollama locally:

```bash
ollama pull qwen2.5-coder:7b
SCHEMASAGE_GENERATOR_BACKEND=ollama OLLAMA_MODEL=qwen2.5-coder:7b \
  python3 -m uvicorn api.main:app --reload
```

Train a LoRA/PEFT adapter:

```bash
python3 -m pip install -e '.[lora]'
python3 scripts/train_lora.py \
  --base-model Qwen/Qwen2.5-Coder-0.5B-Instruct \
  --train-file data/training/demo_text2sql.jsonl \
  --output-dir artifacts/lora/schemasage-qwen-0.5b-adapter
```

Run with a local adapter:

```bash
SCHEMASAGE_GENERATOR_BACKEND=lora \
LORA_BASE_MODEL=Qwen/Qwen2.5-Coder-0.5B-Instruct \
LORA_ADAPTER_PATH=artifacts/lora/schemasage-qwen-0.5b-adapter \
  python3 -m uvicorn api.main:app --reload
```

If Ollama, model dependencies, or adapter artifacts are unavailable, SchemaSage falls back to deterministic SQL and reports the fallback in the response `source` and `explanation`.

## Safety Model

SchemaSage only executes SQL after validation. The validator:

- Allows only `SELECT` and `WITH ... SELECT`.
- Rejects comments, multiple statements, and mutating DDL/DML keywords.
- Verifies referenced tables against the known schema.
- Compiles SQL with SQLite before execution.
- Executes through a read-only connection with `PRAGMA query_only = ON`.
- Wraps every query in an outer `LIMIT`.
- Installs a SQLite progress handler to stop long-running queries.

## Repository Safety

Before committing:

```bash
sh scripts/scan_secrets.sh
python3 -m pytest
git status --short
```

Expected ignored/generated paths include:

- `.env` and other local environment files
- `data/demo/*.sqlite3`
- `artifacts/`
- `build/`, `dist/`, and `*.egg-info/`
- Python caches and virtual environments

If a real secret has ever been committed, rotate it immediately and remove it from Git history before publishing.

## Status

This is a compact foundation implementation for demos and evaluation. Spider/BIRD preprocessing, MLflow tracking, auth, rate limiting, and larger benchmark runs are intentionally left as future production phases rather than placeholder scaffolding.
