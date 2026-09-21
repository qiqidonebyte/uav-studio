from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    settings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    last_seen_at: Mapped[str] = mapped_column(String(64), nullable=False)


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
    owner_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    assembly_instances_json: Mapped[list | None] = mapped_column(JSON, nullable=True)


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


class ClassroomRecord(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    teacher_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    academic_year: Mapped[str | None] = mapped_column(String(40), nullable=True)
    invite_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class ClassEnrollmentRecord(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("class_id", "student_user_id", name="uq_class_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    joined_at: Mapped[str] = mapped_column(String(64), nullable=False)


class AssignmentRecord(Base):
    __tablename__ = "training_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    teacher_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    start_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    requirements_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    score_weights_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class TrainingRunRecord(Base):
    __tablename__ = "training_runs"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_user_id", name="uq_assignment_student_run"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    aircraft_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    scenario_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    started_at: Mapped[str] = mapped_column(String(64), nullable=False)
    ended_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_progress", index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wrong_operations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_pass: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prearm_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flight_validation_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__ = {"version_id_col": version}


class TrainingEventRecord(Base):
    __tablename__ = "training_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    event_key: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class PX4SessionRecord(Base):
    __tablename__ = "px4_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    slot_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    last_seen_at: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    released_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
