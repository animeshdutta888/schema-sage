from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    valid: bool
    reason: str
    normalized_sql: str | None = None
    tables: list[str] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class GenerateResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    validation: ValidationResult
    source: str = "rules"


class ExecuteRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)
    max_rows: int = Field(default=100, ge=1, le=500)


class ExecuteResponse(BaseModel):
    sql: str
    validation: ValidationResult
    columns: list[str]
    rows: list[dict[str, object]]
    row_count: int


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]


class DatabaseSchema(BaseModel):
    tables: list[TableInfo]
