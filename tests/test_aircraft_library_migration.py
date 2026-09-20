from __future__ import annotations

from sqlalchemy import inspect, text

from backend.database import build_engine, ensure_schema_compatibility


def test_aircraft_library_columns_are_added_to_existing_sqlite_database() -> None:
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
    assert {
        "propeller_directions_json",
        "assembly_instances_json",
        "description",
        "created_at",
        "updated_at",
    } <= columns
    engine.dispose()
