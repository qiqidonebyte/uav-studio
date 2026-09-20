from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "uavstudio.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
DEFAULT_SIMULATIONS_DIR = PROJECT_ROOT / "data" / "simulations"


def build_engine(database_url: str = DEFAULT_DATABASE_URL) -> Engine:
    if database_url.endswith(":memory:"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )
    return create_engine(database_url)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ensure_schema_compatibility(engine: Engine) -> None:
    """Apply additive SQLite migrations needed by existing local databases."""

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    migrations: list[str] = []

    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "display_name" not in user_columns:
            migrations.append("ALTER TABLE users ADD COLUMN display_name VARCHAR(120)")
        if "role" not in user_columns:
            migrations.append("ALTER TABLE users ADD COLUMN role VARCHAR(32)")
        if "is_active" not in user_columns:
            migrations.append("ALTER TABLE users ADD COLUMN is_active INTEGER")
        if "created_at" not in user_columns:
            migrations.append("ALTER TABLE users ADD COLUMN created_at VARCHAR(64)")

    if "aircraft" in table_names:
        aircraft_columns = {
            column["name"] for column in inspector.get_columns("aircraft")
        }
        if "owner_user_id" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN owner_user_id INTEGER"
            )
        if "propeller_directions_json" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN propeller_directions_json JSON"
            )
        if "assembly_instances_json" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN assembly_instances_json JSON"
            )
        if "description" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN description VARCHAR(1000)"
            )
        if "created_at" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN created_at VARCHAR(64)"
            )
        if "updated_at" not in aircraft_columns:
            migrations.append(
                "ALTER TABLE aircraft ADD COLUMN updated_at VARCHAR(64)"
            )

    if migrations:
        with engine.begin() as connection:
            for statement in migrations:
                connection.execute(text(statement))

    # Indexes created by SQLAlchemy's model metadata are not retroactively added
    # when a column is introduced through ALTER TABLE, so create the important
    # ownership index explicitly for upgraded SQLite databases.
    if "aircraft" in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_aircraft_owner_user_id "
                    "ON aircraft (owner_user_id)"
                )
            )
