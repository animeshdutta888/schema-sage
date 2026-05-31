from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemasage.database import execute_readonly, initialize_demo_database
from schemasage.evaluation import evaluation_summary
from schemasage.generator import generate_sql
from schemasage.models import ExecuteRequest, ExecuteResponse, GenerateRequest, GenerateResponse
from schemasage.schema import load_schema
from schemasage.validator import validate_sql

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_demo_database()
    yield


app = FastAPI(title="SchemaSage", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def demo_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/schemas")
def schemas() -> dict[str, object]:
    initialize_demo_database()
    return {"database": "demo", "tables": load_schema().model_dump()}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    initialize_demo_database()
    generated = generate_sql(request.question)
    validation = validate_sql(generated.sql)
    return GenerateResponse(
        question=request.question,
        sql=generated.sql,
        explanation=generated.explanation,
        validation=validation,
        source=generated.source,
    )


@app.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest) -> ExecuteResponse:
    initialize_demo_database()
    validation = validate_sql(request.sql)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.model_dump())

    result = execute_readonly(request.sql, max_rows=request.max_rows)
    return ExecuteResponse(
        sql=request.sql,
        validation=validation,
        columns=result.columns,
        rows=result.rows,
        row_count=len(result.rows),
    )


@app.post("/evaluate")
def evaluate() -> dict[str, object]:
    return evaluation_summary()
