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
    if "aircraft" not in inspector.get_table_names():
        return

    aircraft_columns = {
        column["name"] for column in inspector.get_columns("aircraft")
    }
    if "propeller_directions_json" not in aircraft_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE aircraft "
                    "ADD COLUMN propeller_directions_json JSON"
                )
            )
