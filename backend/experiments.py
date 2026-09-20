from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.constants import FLIGHT_BOUNDARY_M
from backend.models import AircraftRecord, SimulationRecord
from backend.schemas import (
    AircraftDefinition,
    Component,
    ExperimentReplay,
    ExperimentSummary,
    Vector3,
)
from backend.seed import build_seed_catalog
from backend.simulation_manager import SimulationSession


def save_experiment(
    session: SimulationSession,
    aircraft: AircraftDefinition,
    database: Session,
    simulations_dir: Path,
) -> ExperimentSummary:
    simulations_dir.mkdir(parents=True, exist_ok=True)
    frames = session.frames or [session.simulator.telemetry_frame()]
    started_at = session.started_at or datetime.now(timezone.utc)
    ended_at = datetime.now(timezone.utc)
    duration_s = max(frame.t for frame in frames)
    max_altitude_m = max(frame.position.z for frame in frames)
    summary = ExperimentSummary(
        id=session.id,
        aircraft_id=aircraft.id or 1,
        aircraft_name=aircraft.name,
        started_at=started_at,
        ended_at=ended_at,
        duration_s=duration_s,
        max_altitude_m=max_altitude_m,
        status="COMPLETED",
        frame_count=len(frames),
    )
    target_position = Vector3(
        x=session.target_position[0],
        y=session.target_position[1],
        z=session.target_position[2],
    )
    waypoints = [
        Vector3(x=point[0], y=point[1], z=point[2])
        for point in session.waypoints
    ]
    replay = ExperimentReplay(
        experiment=summary,
        aircraft=aircraft,
        components=list(session.simulator.catalog.values()),
        frames=frames,
        target_position=target_position,
        waypoints=waypoints,
        boundary_m=FLIGHT_BOUNDARY_M,
    )

    telemetry_path = simulations_dir / f"{session.id}.json"
    telemetry_path.write_text(
        replay.model_dump_json(indent=2),
        encoding="utf-8",
    )

    record = database.get(SimulationRecord, session.id)
    if record is None:
        record = SimulationRecord(id=session.id)
        database.add(record)
    record.aircraft_id = summary.aircraft_id
    record.aircraft_name = summary.aircraft_name
    record.started_at = summary.started_at.isoformat()
    record.ended_at = summary.ended_at.isoformat()
    record.duration_s = summary.duration_s
    record.max_altitude_m = summary.max_altitude_m
    record.status = summary.status
    record.frame_count = summary.frame_count
    record.target_position_json = target_position.model_dump()
    record.waypoints_json = [point.model_dump() for point in waypoints]
    record.telemetry_file = str(telemetry_path)
    database.commit()
    return summary


def list_experiments(
    database: Session,
    *,
    owner_user_id: int | None = None,
) -> list[ExperimentSummary]:
    statement = select(SimulationRecord)
    if owner_user_id is not None:
        statement = (
            statement.join(
                AircraftRecord,
                AircraftRecord.id == SimulationRecord.aircraft_id,
            )
            .where(AircraftRecord.owner_user_id == owner_user_id)
        )
    records = database.scalars(
        statement.order_by(SimulationRecord.started_at.desc())
    ).all()
    return [_summary_from_record(record) for record in records]


def _enrich_legacy_visuals(components: list[Component]) -> list[Component]:
    """Keep old Replay JSON compatible with the new Component.visual contract.

    Historical engineering parameters remain untouched. Only missing presentation
    metadata is copied from the current asset manifest-backed seed catalog.
    """

    current_catalog = build_seed_catalog()
    enriched: list[Component] = []
    for component in components:
        if component.visual is not None:
            enriched.append(component)
            continue
        current = current_catalog.get(component.id)
        if current is None or current.visual is None:
            enriched.append(component)
            continue
        enriched.append(component.model_copy(update={"visual": current.visual}))
    return enriched


def load_replay(
    database: Session,
    simulation_id: int,
    *,
    owner_user_id: int | None = None,
) -> ExperimentReplay:
    if owner_user_id is None:
        record = database.get(SimulationRecord, simulation_id)
    else:
        record = database.scalar(
            select(SimulationRecord)
            .join(
                AircraftRecord,
                AircraftRecord.id == SimulationRecord.aircraft_id,
            )
            .where(
                SimulationRecord.id == simulation_id,
                AircraftRecord.owner_user_id == owner_user_id,
            )
        )
    if record is None:
        raise FileNotFoundError(simulation_id)
    path = Path(record.telemetry_file)
    if not path.exists():
        raise FileNotFoundError(simulation_id)
    replay = ExperimentReplay.model_validate_json(path.read_text(encoding="utf-8"))
    return replay.model_copy(
        update={"components": _enrich_legacy_visuals(replay.components)}
    )


def _summary_from_record(record: SimulationRecord) -> ExperimentSummary:
    return ExperimentSummary(
        id=record.id,
        aircraft_id=record.aircraft_id,
        aircraft_name=record.aircraft_name,
        started_at=datetime.fromisoformat(record.started_at),
        ended_at=datetime.fromisoformat(record.ended_at),
        duration_s=record.duration_s,
        max_altitude_m=record.max_altitude_m,
        status=record.status,
        frame_count=record.frame_count,
    )
