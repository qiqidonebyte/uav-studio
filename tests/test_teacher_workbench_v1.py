from pathlib import Path
import sys

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.models import AircraftRecord, Base, UserRecord  # noqa: E402
from backend.teacher_workbench import register_teacher_workbench_routes  # noqa: E402


def build_client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory() as session:
        session.add_all([
            UserRecord(id=1, username="admin", password_hash="x", display_name="Admin", role="admin", is_active=1, settings_json={}),
            UserRecord(id=2, username="teacher", password_hash="x", display_name="邱老师", role="teacher", is_active=1, settings_json={}),
            UserRecord(id=3, username="student", password_hash="x", display_name="学生A", role="student", is_active=1, settings_json={}),
            UserRecord(id=4, username="student2", password_hash="x", display_name="学生B", role="student", is_active=1, settings_json={}),
            AircraftRecord(id=1, owner_user_id=3, name="Student Quad"),
        ])
        session.commit()

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
    return TestClient(app), factory


def headers(user_id: int):
    return {"x-user-id": str(user_id)}


def test_teacher_assignment_training_run_and_events_roundtrip():
    client, _ = build_client()

    denied = client.get("/api/teacher/overview", headers=headers(3))
    assert denied.status_code == 403

    created_class = client.post(
        "/api/teacher/classes",
        headers=headers(2),
        json={"name": "23无人机1班", "academic_year": "2026-2027-1"},
    )
    assert created_class.status_code == 201
    classroom = created_class.json()
    assert classroom["invite_code"].startswith("UAV-")

    joined = client.post(
        "/api/training/classes/join",
        headers=headers(3),
        json={"invite_code": classroom["invite_code"]},
    )
    assert joined.status_code == 200

    created_assignment = client.post(
        "/api/teacher/assignments",
        headers=headers(2),
        json={
            "class_id": classroom["id"],
            "title": "动力系统映射故障实训",
            "scenario_id": "F04_MOTOR_MAPPING",
            "description": "定位、修复并复测。",
            "requirements": {"prearm": True},
        },
    )
    assert created_assignment.status_code == 201
    assignment = created_assignment.json()
    assert assignment["assigned_count"] == 1

    student_tasks = client.get("/api/training/assignments", headers=headers(3)).json()
    assert len(student_tasks) == 1
    assert student_tasks[0]["run_status"] == "not_started"

    started = client.post(
        f"/api/training/assignments/{assignment['id']}/start",
        headers=headers(3),
        json={"aircraft_id": 1},
    )
    assert started.status_code == 200
    run = started.json()
    assert run["status"] == "in_progress"
    assert run["scenario_id"] == "F04_MOTOR_MAPPING"

    progress = client.post(
        f"/api/training/runs/{run['id']}/progress",
        headers=headers(3),
        json={
            "passed": False,
            "score": 45,
            "elapsed_seconds": 180,
            "hints_used": 0,
            "wrong_operations": 1,
            "prearm_passed": False,
            "flight_validation_passed": False,
            "result": {"visited_sections": ["power"], "evaluation": {"score": 45}},
        },
    )
    assert progress.status_code == 200
    assert progress.json()["score"] == 45

    submitted = client.post(
        f"/api/training/runs/{run['id']}/submit",
        headers=headers(3),
        json={
            "passed": True,
            "score": 88,
            "elapsed_seconds": 420,
            "hints_used": 1,
            "wrong_operations": 1,
            "prearm_passed": True,
            "flight_validation_passed": False,
            "result": {"visited_sections": ["power", "preflight"], "evaluation": {"score": 88}},
        },
    )
    assert submitted.status_code == 200
    result = submitted.json()
    assert result["status"] == "completed"
    assert result["score"] == 88
    assert result["first_pass"] is True

    detail = client.get(f"/api/teacher/runs/{run['id']}", headers=headers(2))
    assert detail.status_code == 200
    event_types = [item["event_type"] for item in detail.json()["events"]]
    assert "run_started" in event_types
    assert "section_visit" in event_types
    assert "submission" in event_types

    overview = client.get("/api/teacher/overview", headers=headers(2)).json()
    assert overview["student_count"] == 1
    assert overview["completed_run_count"] == 1
    assert overview["average_score"] == 88.0


def test_admin_can_promote_teacher_but_teacher_cannot_use_admin_api():
    client, factory = build_client()

    forbidden = client.get("/api/admin/users", headers=headers(2))
    assert forbidden.status_code == 403

    promoted = client.patch(
        "/api/admin/users/4/role",
        headers=headers(1),
        json={"role": "teacher"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "teacher"

    with factory() as session:
        assert session.get(UserRecord, 4).role == "teacher"
