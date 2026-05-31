from schemasage.database import readonly_connection
from schemasage.models import ColumnInfo, DatabaseSchema, TableInfo


def load_schema() -> DatabaseSchema:
    with readonly_connection() as conn:
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        tables: list[TableInfo] = []
        for table_row in table_rows:
            table_name = table_row["name"]
            column_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            columns = [
                ColumnInfo(
                    name=row["name"],
                    type=row["type"],
                    nullable=not bool(row["notnull"]),
                    primary_key=bool(row["pk"]),
                )
                for row in column_rows
            ]
            tables.append(TableInfo(name=table_name, columns=columns))
        return DatabaseSchema(tables=tables)


def known_table_names() -> set[str]:
    return {table.name for table in load_schema().tables}


def serialize_schema_for_prompt() -> str:
    table_lines = []
    for table in load_schema().tables:
        columns = ", ".join(f"{column.name} {column.type}" for column in table.columns)
        table_lines.append(f"Table {table.name}({columns})")
    return "\n".join(table_lines)
