from __future__ import annotations

from sqlalchemy import inspect, text

from backend.database import build_engine, ensure_schema_compatibility


def test_existing_sqlite_aircraft_table_gets_assembly_instances_column() -> None:
    engine = build_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE aircraft ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR(120) NOT NULL"
                ")"
            )
        )

    ensure_schema_compatibility(engine)

    columns = {
        column["name"]
        for column in inspect(engine).get_columns("aircraft")
    }
    assert "propeller_directions_json" in columns
    assert "assembly_instances_json" in columns
    engine.dispose()
