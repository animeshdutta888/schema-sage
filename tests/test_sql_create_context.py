from scripts.prepare_sql_create_context import convert_example


def test_convert_sql_create_context_example_to_training_format() -> None:
    converted = convert_example(
        {
            "question": "How many singers are from France?",
            "context": "CREATE TABLE singers (name TEXT, country TEXT)",
            "answer": "SELECT COUNT(*) FROM singers WHERE country = 'France'",
        }
    )

    assert converted == {
        "instruction": "Generate one safe SQL SELECT query for the question using only the provided schema.",
        "schema": "CREATE TABLE singers (name TEXT, country TEXT)",
        "question": "How many singers are from France?",
        "sql": "SELECT COUNT(*) FROM singers WHERE country = 'France'",
    }
