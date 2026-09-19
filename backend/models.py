from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    settings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)



class ComponentRecord(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    mass_kg: Mapped[float] = mapped_column(Float, nullable=False)
    parameters_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class AircraftRecord(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    frame_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    motor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    esc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    propeller_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    propeller_directions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    battery_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_module_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flight_controller_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gnss_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gnss_position_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    payload_position_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SimulationRecord(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aircraft_id: Mapped[int] = mapped_column(Integer, nullable=False)
    aircraft_name: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[str] = mapped_column(String(64), nullable=False)
    ended_at: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, nullable=False)
    max_altitude_m: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    frame_count: Mapped[int] = mapped_column(Integer, nullable=False)
    target_position_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    waypoints_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    telemetry_file: Mapped[str] = mapped_column(String(500), nullable=False)
