from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models import PX4SessionRecord, TrainingRunRecord, UserRecord
from backend.px4 import Px4BridgeError
from backend.px4.session_manager import Px4Slot, session_manager


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TakeoffRequest(StrictModel):
    altitude_m: float = Field(default=2.0, gt=0.0, le=30.0)


class MotorTestRequest(StrictModel):
    value: float = Field(default=0.20, ge=0.0, le=0.35)
    timeout_s: float = Field(default=1.5, ge=0.2, le=3.0)


class ParameterWriteRequest(StrictModel):
    value: float


class SessionView(StrictModel):
    id: int
    run_id: int
    student_user_id: int
    slot_id: int | None
    status: str
    queue_position: int
    created_at: str
    last_seen_at: str
    released_at: str | None
    error_message: str


_QUEUE_LOCK = threading.RLock()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _role(user: UserRecord) -> str:
    return user.role or "student"


def _run_or_404(session: Session, current_user: UserRecord, run_id: int) -> TrainingRunRecord:
    run = session.get(TrainingRunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="实训记录不存在")
    if run.student_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能访问自己的 PX4 实训会话")
    return run


def _row_for_run(session: Session, run_id: int) -> PX4SessionRecord | None:
    return session.scalar(select(PX4SessionRecord).where(PX4SessionRecord.run_id == run_id))


def _queue_position(session: Session, row: PX4SessionRecord) -> int:
    if row.status != "queued":
        return 0
    count = session.scalar(
        select(func.count(PX4SessionRecord.id)).where(
            PX4SessionRecord.status == "queued",
            PX4SessionRecord.id < row.id,
        )
    ) or 0
    return int(count) + 1


def _session_view(session: Session, row: PX4SessionRecord) -> SessionView:
    return SessionView(
        id=row.id,
        run_id=row.run_id,
        student_user_id=row.student_user_id,
        slot_id=row.slot_id,
        status=row.status,
        queue_position=_queue_position(session, row),
        created_at=row.created_at,
        last_seen_at=row.last_seen_at,
        released_at=row.released_at,
        error_message=row.error_message or "",
    )


def _blank_status(message: str = "", *, queue_position: int = 0) -> dict[str, Any]:
    return {
        "dependency_available": True,
        "running": False,
        "connected": False,
        "connection_url": "classroom-pool",
        "heartbeat_age_s": None,
        "system_id": None,
        "component_id": None,
        "mode": "WAITING",
        "armed": False,
        "last_error": message,
        "uptime_s": 0.0,
        "session_status": "queued" if queue_position else "unassigned",
        "queue_position": queue_position,
        "slot_id": None,
    }


def _blank_telemetry(message: str = "", *, queue_position: int = 0) -> dict[str, Any]:
    return {
        **_blank_status(message, queue_position=queue_position),
        "landed_state": None,
        "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
        "local_position": {"x": 0.0, "y": 0.0, "z": 0.0, "vx": 0.0, "vy": 0.0, "vz": 0.0},
        "global_position": {"lat_deg": None, "lon_deg": None, "relative_alt_m": None, "alt_amsl_m": None},
        "gps": {"fix_type": None, "satellites": None, "eph": None},
        "battery": {"voltage_v": None, "current_a": None, "remaining": None},
        "motors": {"outputs": [0.0, 0.0, 0.0, 0.0]},
        "estimator": {"flags": None, "ok": None},
        "statustext": "",
        "prearm_ok": False,
    }


def _release_row(session: Session, row: PX4SessionRecord, reason: str) -> None:
    session_manager.release_runtime(row.run_id)
    row.slot_id = None
    row.status = "released"
    row.released_at = utc_now_iso()
    row.last_seen_at = row.released_at
    row.error_message = reason


def _sweep(session: Session) -> None:
    cutoff = utc_now() - timedelta(seconds=session_manager.idle_timeout_s)
    rows = session.scalars(
        select(PX4SessionRecord).where(
            PX4SessionRecord.status.in_(["queued", "starting", "ready", "active"])
        )
    ).all()
    changed = False
    for row in rows:
        run = session.get(TrainingRunRecord, row.run_id)
        if run is None or run.status == "completed":
            _release_row(session, row, "TrainingRun 已完成或不存在")
            changed = True
            continue
        seen = _parse_iso(row.last_seen_at)
        if seen is not None and seen < cutoff:
            _release_row(session, row, "PX4 会话空闲超时，资源已回收")
            changed = True
    if changed:
        session.commit()


def _promote_queue(session: Session) -> None:
    with _QUEUE_LOCK:
        _sweep(session)
        queued = session.scalars(
            select(PX4SessionRecord)
            .where(PX4SessionRecord.status == "queued")
            .order_by(PX4SessionRecord.id)
        ).all()
        changed = False
        for row in queued:
            slot = session_manager.acquire_runtime(row.run_id, row.student_user_id)
            if slot is None:
                break
            row.slot_id = slot.slot_id
            row.status = "starting"
            row.last_seen_at = utc_now_iso()
            row.error_message = ""
            changed = True
        if changed:
            session.commit()


def _touch_row(session: Session, row: PX4SessionRecord, *, force: bool = False) -> None:
    # FlightLab polls telemetry at 10 Hz. Persisting last_seen on every frame would
    # create needless SQLite write pressure, so runtime heartbeat stays in memory
    # and the durable timestamp is refreshed at most once every five seconds.
    now = utc_now()
    previous = _parse_iso(row.last_seen_at)
    if not force and previous is not None and (now - previous).total_seconds() < 5.0:
        return
    row.last_seen_at = now.isoformat()
    session.commit()


def _sync_runtime_status(session: Session, row: PX4SessionRecord) -> tuple[PX4SessionRecord, Px4Slot | None, dict[str, Any]]:
    if row.status == "queued":
        _promote_queue(session)
        session.refresh(row)
    if row.slot_id is None:
        pos = _queue_position(session, row)
        return row, None, _blank_status(f"PX4资源排队中，当前第 {pos} 位", queue_position=pos)
    slot = session_manager.slot_for_run(row.run_id)
    if slot is None:
        row.slot_id = None
        row.status = "queued"
        row.error_message = "服务重启后正在重新分配 PX4 Slot"
        row.last_seen_at = utc_now_iso()
        session.commit()
        _promote_queue(session)
        session.refresh(row)
        if row.slot_id is None:
            pos = _queue_position(session, row)
            return row, None, _blank_status(f"PX4资源排队中，当前第 {pos} 位", queue_position=pos)
        slot = session_manager.slot_for_run(row.run_id)
    if slot is None:
        return row, None, _blank_status("PX4 Slot 正在恢复")

    payload = session_manager.runtime_status(slot)
    old_status = row.status
    old_error = row.error_message or ""
    if payload.get("connected"):
        row.status = "ready" if row.status != "active" else "active"
        row.error_message = ""
    else:
        row.status = "starting"
        row.error_message = str(payload.get("last_error") or f"Slot {slot.slot_id} 等待 PX4 Heartbeat")
    status_changed = row.status != old_status or (row.error_message or "") != old_error
    _touch_row(session, row, force=status_changed)
    payload.update(
        {
            "session_status": row.status,
            "queue_position": 0,
            "slot_id": slot.slot_id,
        }
    )
    return row, slot, payload


def _require_slot(session: Session, row: PX4SessionRecord) -> Px4Slot:
    row, slot, payload = _sync_runtime_status(session, row)
    if slot is None:
        raise HTTPException(status_code=409, detail=payload.get("last_error") or "PX4资源排队中")
    if not payload.get("connected"):
        raise HTTPException(status_code=409, detail=payload.get("last_error") or "PX4尚未就绪")
    row.status = "active"
    row.last_seen_at = utc_now_iso()
    session.commit()
    return slot


def recover_classroom_reliability(session: Session) -> None:
    """Called during backend startup; persistent runs survive, runtime PX4 does not."""
    session_manager.reset_runtime()
    rows = session.scalars(
        select(PX4SessionRecord).where(
            PX4SessionRecord.status.in_(["starting", "ready", "active"])
        )
    ).all()
    for row in rows:
        row.slot_id = None
        row.status = "queued"
        row.error_message = "服务重启，PX4资源等待重新分配"
        row.last_seen_at = utc_now_iso()
    if rows:
        session.commit()


def shutdown_classroom_reliability() -> None:
    session_manager.shutdown()


def release_px4_for_run(session: Session, run_id: int, reason: str = "实训结束") -> None:
    row = _row_for_run(session, run_id)
    if row is None or row.status == "released":
        return
    _release_row(session, row, reason)
    session.commit()
    _promote_queue(session)


def register_classroom_reliability_routes(
    app: FastAPI,
    get_db: Callable[..., Iterator[Session]],
    get_current_user: Callable[..., UserRecord],
) -> None:
    @app.post("/api/training/runs/{run_id}/px4/session", response_model=SessionView)
    def acquire_session(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SessionView:
        run = _run_or_404(session, current_user, run_id)
        if run.status == "completed":
            raise HTTPException(status_code=409, detail="实训已完成，无需再次申请 PX4 资源")
        row = _row_for_run(session, run_id)
        if row is None:
            now = utc_now_iso()
            row = PX4SessionRecord(
                run_id=run.id,
                student_user_id=current_user.id,
                slot_id=None,
                status="queued",
                created_at=now,
                last_seen_at=now,
                released_at=None,
                failure_count=0,
                error_message="",
            )
            session.add(row)
            try:
                session.commit()
                session.refresh(row)
            except IntegrityError:
                # A double click/retry may race the first INSERT. run_id is unique,
                # so reuse the row that won instead of failing the classroom flow.
                session.rollback()
                row = _row_for_run(session, run_id)
                if row is None:
                    raise
        elif row.status in {"released", "failed"}:
            row.slot_id = None
            row.status = "queued"
            row.released_at = None
            row.last_seen_at = utc_now_iso()
            row.error_message = ""
            session.commit()
        else:
            _touch_row(session, row)
        _promote_queue(session)
        session.refresh(row)
        return _session_view(session, row)

    @app.get("/api/training/runs/{run_id}/px4/session", response_model=SessionView)
    def get_session(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SessionView:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="尚未申请 PX4 资源")
        _touch_row(session, row)
        _promote_queue(session)
        session.refresh(row)
        return _session_view(session, row)

    @app.post("/api/training/runs/{run_id}/px4/release", response_model=SessionView)
    def release_session(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SessionView:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="PX4会话不存在")
        _release_row(session, row, "学生主动释放 PX4 资源")
        session.commit()
        _promote_queue(session)
        session.refresh(row)
        return _session_view(session, row)

    @app.get("/api/training/runs/{run_id}/px4/status")
    def px4_status(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> dict[str, Any]:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is None:
            return _blank_status("尚未申请 PX4 资源")
        _, _, payload = _sync_runtime_status(session, row)
        return payload

    @app.get("/api/training/runs/{run_id}/px4/telemetry")
    def px4_telemetry(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> dict[str, Any]:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is None:
            return _blank_telemetry("尚未申请 PX4 资源")
        row, slot, payload = _sync_runtime_status(session, row)
        if slot is None or not payload.get("connected"):
            waiting = _blank_telemetry(
                str(payload.get("last_error") or "PX4资源准备中"),
                queue_position=int(payload.get("queue_position") or 0),
            )
            waiting.update(
                {
                    "session_status": payload.get("session_status", waiting["session_status"]),
                    "queue_position": int(payload.get("queue_position") or 0),
                    "slot_id": payload.get("slot_id"),
                    "slot_port": payload.get("slot_port"),
                    "run_id": payload.get("run_id"),
                }
            )
            return waiting
        telemetry = session_manager.telemetry(slot)
        telemetry.update({"session_status": row.status, "queue_position": 0, "slot_id": slot.slot_id})
        return telemetry

    @app.post("/api/training/runs/{run_id}/px4/connect")
    def px4_connect(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> dict[str, Any]:
        run = _run_or_404(session, current_user, run_id)
        if run.status == "completed":
            return _blank_status("实训已完成")
        row = _row_for_run(session, run_id)
        if row is None or row.status in {"released", "failed"}:
            acquire_session(run_id, session, current_user)
            row = _row_for_run(session, run_id)
        assert row is not None
        _, _, payload = _sync_runtime_status(session, row)
        return payload

    @app.post("/api/training/runs/{run_id}/px4/disconnect")
    def px4_disconnect(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> dict[str, Any]:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is not None:
            _release_row(session, row, "学生断开 PX4")
            session.commit()
            _promote_queue(session)
        return _blank_status("PX4资源已释放")

    def action_slot(run_id: int, session: Session, current_user: UserRecord) -> Px4Slot:
        _run_or_404(session, current_user, run_id)
        row = _row_for_run(session, run_id)
        if row is None:
            raise HTTPException(status_code=409, detail="请先连接 PX4")
        return _require_slot(session, row)

    def bridge_action(action: Callable[[], Any]) -> Any:
        try:
            return action()
        except Px4BridgeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PX4 Slot 内部错误：{exc}") from exc

    @app.post("/api/training/runs/{run_id}/px4/request-streams")
    def request_streams(run_id: int, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> dict[str, bool]:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(lambda: (slot.bridge.request_streams(10.0) or {"ok": True}))

    @app.post("/api/training/runs/{run_id}/px4/arm")
    def arm(run_id: int, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(slot.bridge.arm)

    @app.post("/api/training/runs/{run_id}/px4/disarm")
    def disarm(run_id: int, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(slot.bridge.disarm)

    @app.post("/api/training/runs/{run_id}/px4/takeoff")
    def takeoff(run_id: int, command: TakeoffRequest, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(lambda: slot.bridge.takeoff(command.altitude_m))

    @app.post("/api/training/runs/{run_id}/px4/land")
    def land(run_id: int, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(slot.bridge.land)

    @app.post("/api/training/runs/{run_id}/px4/prearm-check")
    def prearm(run_id: int, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(slot.bridge.prearm_check)

    @app.post("/api/training/runs/{run_id}/px4/sensors/{sensor_name}/calibrate")
    def calibrate(run_id: int, sensor_name: str, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(lambda: slot.bridge.calibrate_sensor(sensor_name))

    @app.post("/api/training/runs/{run_id}/px4/motors/{motor}/test")
    def motor_test(run_id: int, motor: str, command: MotorTestRequest, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        motor_name = motor.strip().upper()
        if motor_name not in {"M1", "M2", "M3", "M4"}:
            raise HTTPException(status_code=422, detail="motor 必须为 M1-M4")
        return bridge_action(lambda: slot.bridge.test_motor(int(motor_name[1]), command.value, command.timeout_s))

    @app.get("/api/training/runs/{run_id}/px4/parameters/{name}")
    def read_parameter(run_id: int, name: str, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(lambda: slot.bridge.get_parameter(name))

    @app.put("/api/training/runs/{run_id}/px4/parameters/{name}")
    def write_parameter(run_id: int, name: str, command: ParameterWriteRequest, session: Session = Depends(get_db), current_user: UserRecord = Depends(get_current_user)) -> Any:
        slot = action_slot(run_id, session, current_user)
        return bridge_action(lambda: slot.bridge.set_parameter(name, command.value))

    @app.get("/api/teacher/px4-pool")
    def pool_status(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> dict[str, Any]:
        if _role(current_user) not in {"teacher", "admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要教师权限")
        _promote_queue(session)
        queued = int(session.scalar(select(func.count(PX4SessionRecord.id)).where(PX4SessionRecord.status == "queued")) or 0)
        snapshot = session_manager.snapshot()
        snapshot["queued"] = queued
        return snapshot
