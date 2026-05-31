````md
# agents.md — SchemaSage

## Project

SchemaSage is a schema-aware Text2SQL system that converts natural language business questions into safe, validated SQL over enterprise-style databases.

It is designed as a portfolio-ready AI/FDE project with:
- LoRA/PEFT fine-tuning
- Text2SQL optimization
- FastAPI backend
- TypeScript web layer
- MLflow experiment tracking
- Hugging Face hosted demo
- Recruiter-friendly public link

---

## Goal

Build a complete Text2SQL copilot that demonstrates how an AI engineer or Forward Deployed Engineer would solve a real enterprise data-access problem.

A user should be able to ask:

> Show monthly revenue by region for enterprise customers in 2024.

The system should return:
- Generated SQL
- SQL validation result
- Query output table
- Explanation of tables/columns used
- Optional before/after evaluation metrics

---

## Problem it solves

Enterprise teams often have data in SQL warehouses, but business users cannot always write SQL.

SchemaSage reduces dependency on analysts by allowing users to ask business questions in natural language and get safe, executable SQL.

The key challenge is not only generating SQL, but handling:
- Database schema understanding
- Table and column selection
- Join reasoning
- SQL correctness
- Query safety
- Evaluation against benchmark datasets

---

## Dataset

Use public Text2SQL datasets:

### Primary dataset
- **Spider**
  - Multi-table complex Text2SQL benchmark
  - Includes natural language questions, database schemas, and ground-truth SQL

### Optional advanced dataset
- **BIRD**
  - More realistic and challenging Text2SQL benchmark
  - Better for enterprise-style analytics use cases

Initial implementation can start with Spider, then add BIRD support later.

---

## Model strategy

Use a local-first development setup with:

### Local dev model
- Qwen via Ollama for local experimentation
- Used for prompt testing, schema-aware generation, and quick iteration

### Fine-tuning target
- Open-source Hugging Face model such as:
  - Qwen2.5-Coder
  - CodeLlama
  - Llama 3.1 8B
  - SQLCoder-style model if needed

LoRA/PEFT should be used to optimize the base model for Text2SQL.

---

## LoRA/PEFT usage

Use LoRA through PEFT for parameter-efficient fine-tuning.

Purpose:
- Adapt a general code/LLM model to Text2SQL
- Improve SQL structure generation
- Improve schema following
- Improve table/column grounding
- Reduce invalid SQL rate
- Compare base model vs fine-tuned model

Training data format:

```json
{
  "instruction": "Generate SQL for the given question and database schema.",
  "schema": "Table customers(id, name, region)... Table orders(id, customer_id, amount, order_date)...",
  "question": "Show monthly revenue by region in 2024.",
  "sql": "SELECT ..."
}
````

Track experiments with MLflow:

* Base model
* LoRA rank
* Learning rate
* Dataset version
* Exact match
* Execution accuracy
* Valid SQL rate
* Latency

---

## System architecture

```text
User Question
    ↓
TypeScript Web UI
    ↓
FastAPI Backend
    ↓
Schema Retriever / Serializer
    ↓
Text2SQL Model
    ↓
SQL Validator
    ↓
SQLite Demo DB / Benchmark DB
    ↓
Result Table + Explanation
```

---

## Backend

Use FastAPI.

Required endpoints:

```text
GET  /health
GET  /schemas
POST /generate
POST /execute
POST /evaluate
```

Responsibilities:

* Load model or call local Ollama/Qwen during dev
* Build schema-aware prompt
* Generate SQL
* Validate SQL
* Execute safe read-only queries
* Return SQL, result rows, and explanation

---

## Web layer

Use a TypeScript frontend.

Preferred stack:

* Svelte + TypeScript
* Vite
* Tailwind or clean CSS

UI sections:

* Question input
* Database/schema selector
* Generated SQL viewer
* Validation status
* Result table
* Explanation panel
* Evaluation metrics panel

The web app should look polished because recruiters should be able to open the hosted demo and understand the project quickly.

---

## Hosting

Host the public demo on **Hugging Face Spaces** so recruiters and interviewers can visit a live link.

Recommended deployment:

* Hugging Face Space with FastAPI + web app
* Lightweight demo mode using SQLite sample databases
* Optional model fallback if full fine-tuned model is too heavy
* README should include the live demo link clearly at the top

Example README line:

```md
Live Demo: https://huggingface.co/spaces/<username>/schemasage
```

---

## SQL safety

Never execute raw generated SQL directly.

Validation rules:

* Allow only `SELECT` and `WITH ... SELECT`
* Block `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `CREATE`
* Block multiple statements
* Add row limit
* Add query timeout
* Validate tables and columns where possible

---

## Evaluation

Compare:

1. Base model prompting
2. Schema-aware prompting
3. LoRA/PEFT fine-tuned model

Metrics:

* Exact match
* Execution accuracy
* Valid SQL rate
* Parse success rate
* Latency

Create:

```text
docs/eval_report.md
```

Include a table:

```md
| Model | Exact Match | Execution Accuracy | Valid SQL Rate | Avg Latency |
|---|---:|---:|---:|---:|
| Base model | TBD | TBD | TBD | TBD |
| Schema-aware prompt | TBD | TBD | TBD | TBD |
| LoRA fine-tuned model | TBD | TBD | TBD | TBD |
```

Do not invent metrics. Use `TBD` until real evaluation runs are complete.

---

## Repo structure

```text
schema-sage/
├── README.md
├── agents.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── api/
│   ├── main.py
│   ├── routes/
│   └── schemas/
├── schemasage/
│   ├── data/
│   ├── inference/
│   ├── training/
│   ├── validation/
│   ├── evaluation/
│   └── explainability/
├── web/
│   ├── package.json
│   └── src/
├── data/
│   ├── raw/
│   ├── processed/
│   └── demo/
├── scripts/
│   ├── prepare_data.sh
│   ├── train_lora.sh
│   ├── evaluate.sh
│   └── serve.sh
├── docs/
│   ├── architecture.md
│   ├── eval_report.md
│   └── demo_script.md
└── tests/
```

---

## Development phases

### Phase 1 — Demo app foundation

* Create repo structure
* Build FastAPI backend
* Build TypeScript web UI
* Add sample SQLite enterprise databases
* Add schema viewer and query input

### Phase 2 — Local Qwen/Ollama Text2SQL

* Use locally running Qwen through Ollama
* Build schema-aware prompt
* Generate SQL
* Validate and execute SQL safely
* Show results in UI

### Phase 3 — Dataset and evaluation

* Add Spider preprocessing
* Add evaluation scripts
* Compare generated SQL against ground truth
* Track exact match, execution accuracy, valid SQL rate

### Phase 4 — LoRA/PEFT fine-tuning

* Prepare instruction dataset
* Fine-tune model using LoRA
* Log runs in MLflow
* Save adapter
* Compare base vs fine-tuned model

### Phase 5 — Hugging Face demo

* Add model card
* Add Space deployment files
* Host demo on Hugging Face Spaces
* Add live demo link to README

---

## README positioning

The README should say:

```md
# SchemaSage

Schema-aware Text2SQL copilot for enterprise analytics.

SchemaSage converts natural language business questions into safe, validated SQL using schema-aware prompting, LoRA/PEFT fine-tuning, SQL validation, and execution-based evaluation.

Live Demo: <Hugging Face Space link>
```

Add a section:

```md
## Why this matters for Forward Deployed AI Engineering

SchemaSage demonstrates the full FDE workflow: understanding a customer data-access problem, adapting an open-source model, grounding it in database schemas, validating generated outputs, measuring quality, and shipping a usable full-stack demo.
```

---

## Resume bullet

Use after implementation:

```md
Built SchemaSage, a schema-aware Text2SQL copilot using Spider/BIRD datasets, LoRA/PEFT fine-tuning, FastAPI, TypeScript web UI, SQL validation, MLflow experiment tracking, and Hugging Face Spaces deployment; evaluated base vs fine-tuned models using exact match, execution accuracy, valid SQL rate, and latency.
```

---

## Success criteria

The project is complete when:

* Recruiters can open a Hugging Face demo link.
* A user can ask a business question and get SQL.
* The SQL is validated before execution.
* Results are shown in a web UI.
* Spider evaluation can run locally.
* LoRA/PEFT fine-tuning pipeline exists.
* MLflow tracks experiments.
* README clearly explains the FDE relevance.

```
```
