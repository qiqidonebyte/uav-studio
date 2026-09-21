from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.classroom_reliability import (  # noqa: E402
    recover_classroom_reliability,
    register_classroom_reliability_routes,
)
from backend.database import build_engine, build_session_factory  # noqa: E402
from backend.models import Base, PX4SessionRecord, TrainingRunRecord, UserRecord  # noqa: E402
from backend.px4.session_manager import session_manager  # noqa: E402
from backend.teacher_workbench import register_teacher_workbench_routes  # noqa: E402


def build_client(tmp_path: Path):
    engine = build_engine(f"sqlite:///{(tmp_path / 'classroom.db').as_posix()}")
    factory = build_session_factory(engine)
    Base.metadata.create_all(engine)
    with factory() as session:
        session.add(UserRecord(id=1, username="teacher", password_hash="x", role="teacher", is_active=1, settings_json={}))
        for index in range(35):
            user_id = 100 + index
            session.add(UserRecord(id=user_id, username=f"s{index+1:02d}", password_hash="x", role="student", is_active=1, settings_json={}))
            session.add(TrainingRunRecord(
                id=1000 + index,
                assignment_id=1,
                student_user_id=user_id,
                aircraft_id=None,
                scenario_id="F06_INTEGRATED",
                started_at="2026-09-21T00:00:00+00:00",
                status="awaiting_flight",
                score=70.0,
                elapsed_seconds=100,
                hints_used=0,
                wrong_operations=0,
                first_pass=1,
                prearm_passed=1,
                flight_validation_passed=0,
                result_json={"grading": {"diagnosis_passed": True, "stage": "awaiting_flight"}},
            ))
        session.commit()
        recover_classroom_reliability(session)

    app = FastAPI()

    def get_db():
        with factory() as session:
            yield session

    def get_current_user(request: Request, session: Session = Depends(get_db)) -> UserRecord:
        user_id = int(request.headers.get("x-user-id", "0"))
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="missing user")
        return user

    register_teacher_workbench_routes(app, get_db, get_current_user)
    register_classroom_reliability_routes(app, get_db, get_current_user)
    return TestClient(app), factory, engine


def headers(user_id: int):
    return {"x-user-id": str(user_id)}


def fake_px4(monkeypatch):
    session_manager.reset_runtime()
    monkeypatch.setattr(session_manager, "_ensure_started", lambda slot: None)

    def runtime_status(slot):
        session_manager.touch(slot)
        return {
            "dependency_available": True,
            "running": True,
            "connected": True,
            "connection_url": slot.connection_url,
            "heartbeat_age_s": 0.01,
            "system_id": slot.slot_id + 1,
            "component_id": 1,
            "mode": "POSCTL",
            "armed": False,
            "last_error": "",
            "uptime_s": 1.0,
            "slot_id": slot.slot_id,
            "slot_port": slot.port,
            "run_id": slot.run_id,
        }

    monkeypatch.setattr(session_manager, "runtime_status", runtime_status)


def test_35_students_get_exactly_12_slots_and_fifo_queue(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, factory, _ = build_client(tmp_path)

    def acquire(index: int):
        return client.post(
            f"/api/training/runs/{1000 + index}/px4/session",
            headers=headers(100 + index),
        )

    with ThreadPoolExecutor(max_workers=16) as executor:
        responses = list(executor.map(acquire, range(35)))

    assert all(item.status_code == 200 for item in responses)
    with factory() as session:
        active = session.query(PX4SessionRecord).filter(PX4SessionRecord.slot_id.is_not(None)).all()
        queued = session.query(PX4SessionRecord).filter(PX4SessionRecord.status == "queued").order_by(PX4SessionRecord.id).all()
        assert len(active) == 12
        assert len(queued) == 23
        assert len({item.slot_id for item in active}) == 12
        assert len({item.run_id for item in active}) == 12

    pool = client.get("/api/teacher/px4-pool", headers=headers(1))
    assert pool.status_code == 200
    assert pool.json()["pool_size"] == 12
    assert pool.json()["used"] == 12
    assert pool.json()["queued"] == 23


def test_release_promotes_first_waiting_run(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, factory, _ = build_client(tmp_path)
    for index in range(13):
        response = client.post(
            f"/api/training/runs/{1000 + index}/px4/session",
            headers=headers(100 + index),
        )
        assert response.status_code == 200

    with factory() as session:
        waiting = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1012).one()
        assert waiting.status == "queued"
        assert waiting.slot_id is None

    released = client.post("/api/training/runs/1000/px4/release", headers=headers(100))
    assert released.status_code == 200
    with factory() as session:
        promoted = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1012).one()
        assert promoted.slot_id is not None
        assert promoted.status in {"starting", "ready", "active"}


def test_student_cannot_operate_another_students_slot(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, _, _ = build_client(tmp_path)
    assert client.post("/api/training/runs/1000/px4/session", headers=headers(100)).status_code == 200
    forbidden = client.get("/api/training/runs/1000/px4/status", headers=headers(101))
    assert forbidden.status_code == 403


def test_backend_restart_requeues_runtime_sessions_without_losing_run(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, factory, _ = build_client(tmp_path)
    assert client.post("/api/training/runs/1000/px4/session", headers=headers(100)).status_code == 200
    with factory() as session:
        before = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1000).one()
        assert before.slot_id is not None
        recover_classroom_reliability(session)
        run = session.get(TrainingRunRecord, 1000)
        row = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1000).one()
        assert run is not None
        assert run.status == "awaiting_flight"
        assert row.status == "queued"
        assert row.slot_id is None


def test_completed_run_is_swept_and_slot_reused(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, factory, _ = build_client(tmp_path)
    for index in range(13):
        client.post(f"/api/training/runs/{1000 + index}/px4/session", headers=headers(100 + index))
    with factory() as session:
        run = session.get(TrainingRunRecord, 1000)
        run.status = "completed"
        run.flight_validation_passed = 1
        session.commit()

    # A pool/status request performs opportunistic sweep and promotes the FIFO queue.
    pool = client.get("/api/teacher/px4-pool", headers=headers(1))
    assert pool.status_code == 200
    with factory() as session:
        completed_session = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1000).one()
        promoted = session.query(PX4SessionRecord).filter(PX4SessionRecord.run_id == 1012).one()
        assert completed_session.status == "released"
        assert completed_session.slot_id is None
        assert promoted.slot_id is not None


def test_training_event_event_key_is_idempotent(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    client, factory, _ = build_client(tmp_path)
    payload = {
        "event_type": "operation",
        "title": "PX4 Arm",
        "detail": "network retry test",
        "event_key": "run-1000-arm-001",
        "payload": {"accepted": True},
    }
    first = client.post("/api/training/runs/1000/events", headers=headers(100), json=payload)
    second = client.post("/api/training/runs/1000/events", headers=headers(100), json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    with factory() as session:
        from backend.models import TrainingEventRecord
        count = session.scalar(select(func.count(TrainingEventRecord.id)).where(
            TrainingEventRecord.run_id == 1000,
            TrainingEventRecord.event_key == "run-1000-arm-001",
        ))
        assert count == 1


def test_training_run_optimistic_version_rejects_stale_writer(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    _, factory, _ = build_client(tmp_path)
    session_a = factory()
    session_b = factory()
    try:
        run_a = session_a.get(TrainingRunRecord, 1000)
        run_b = session_b.get(TrainingRunRecord, 1000)
        assert run_a is not None and run_b is not None
        version = run_a.version
        run_a.elapsed_seconds = 200
        session_a.commit()
        assert run_a.version == version + 1
        run_b.elapsed_seconds = 300
        with pytest.raises(StaleDataError):
            session_b.commit()
    finally:
        session_a.close()
        session_b.close()


def test_file_sqlite_uses_wal_and_busy_timeout(tmp_path, monkeypatch):
    fake_px4(monkeypatch)
    _, _, engine = build_client(tmp_path)
    with engine.connect() as connection:
        journal = str(connection.execute(text("PRAGMA journal_mode")).scalar()).lower()
        busy_timeout = int(connection.execute(text("PRAGMA busy_timeout")).scalar() or 0)
    assert journal == "wal"
    assert busy_timeout >= 5000
