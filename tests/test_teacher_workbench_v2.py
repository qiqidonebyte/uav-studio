from pathlib import Path
import csv
import io
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
            UserRecord(id=4, username="teacher2", password_hash="x", display_name="其他教师", role="teacher", is_active=1, settings_json={}),
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


def create_course(client: TestClient, *, flight_required: bool = True):
    classroom = client.post(
        "/api/teacher/classes",
        headers=headers(2),
        json={"name": "23无人机1班", "academic_year": "2026-2027-1"},
    ).json()
    assert client.post(
        "/api/training/classes/join",
        headers=headers(3),
        json={"invite_code": classroom["invite_code"]},
    ).status_code == 200
    assignment_response = client.post(
        "/api/teacher/assignments",
        headers=headers(2),
        json={
            "class_id": classroom["id"],
            "title": "综合故障诊断与飞行验证",
            "scenario_id": "F06_INTEGRATED",
            "description": "诊断、Pre-Arm并完成PX4飞行验证。",
            "requirements": {
                "diagnosis": True,
                "repair": True,
                "prearm": True,
                "flight_validation": flight_required,
            },
            "score_weights": {
                "case_score": 70,
                "flight_validation": 20,
                "operation_norm": 10,
            },
        },
    )
    assert assignment_response.status_code == 201
    return classroom, assignment_response.json()


def test_full_training_flow_gradebook_analytics_and_csv():
    client, _ = build_client()
    classroom, assignment = create_course(client, flight_required=True)

    started = client.post(
        f"/api/training/assignments/{assignment['id']}/start",
        headers=headers(3),
        json={"aircraft_id": 1},
    )
    assert started.status_code == 200
    run = started.json()
    assert run["stage"] == "diagnosis"

    too_early = client.post(
        f"/api/training/runs/{run['id']}/flight-validation",
        headers=headers(3),
        json={"passed": True, "detail": "should reject"},
    )
    assert too_early.status_code == 409

    progress = client.post(
        f"/api/training/runs/{run['id']}/progress",
        headers=headers(3),
        json={
            "passed": False,
            "score": 55,
            "elapsed_seconds": 300,
            "hints_used": 1,
            "wrong_operations": 1,
            "prearm_passed": False,
            "result": {
                "visited_sections": ["rc", "power"],
                "condition_state": {"rc_verified": True},
                "evaluation": {"score": 55},
            },
        },
    )
    assert progress.status_code == 200
    assert progress.json()["score"] == 55
    assert progress.json()["operation_score"] == 85.0

    submitted = client.post(
        f"/api/training/runs/{run['id']}/submit",
        headers=headers(3),
        json={
            "passed": True,
            "score": 88,
            "elapsed_seconds": 720,
            "hints_used": 1,
            "wrong_operations": 1,
            "prearm_passed": True,
            "flight_validation_passed": False,
            "result": {
                "visited_sections": ["rc", "power", "safety", "preflight"],
                "condition_state": {
                    "rc_verified": True,
                    "motors_verified": True,
                    "safety_verified": True,
                    "preflight_passed": True,
                },
                "evaluation": {"score": 88},
            },
        },
    )
    assert submitted.status_code == 200
    waiting = submitted.json()
    assert waiting["status"] == "awaiting_flight"
    assert waiting["stage"] == "awaiting_flight"
    assert waiting["prearm_passed"] is True
    assert waiting["flight_validation_passed"] is False
    assert waiting["case_score"] == 88.0
    assert waiting["operation_score"] == 85.0
    assert waiting["flight_score"] == 0.0
    assert waiting["score"] == 70.1

    gradebook_waiting = client.get(
        "/api/teacher/gradebook",
        headers=headers(2),
        params={"class_id": classroom["id"]},
    )
    assert gradebook_waiting.status_code == 200
    cell = gradebook_waiting.json()["students"][0]["cells"][0]
    assert cell["stage"] == "awaiting_flight"
    assert cell["status"] == "awaiting_flight"

    flight = client.post(
        f"/api/training/runs/{run['id']}/flight-validation",
        headers=headers(3),
        json={"passed": True, "detail": "PX4: Arm → Takeoff → Hover → Land"},
    )
    assert flight.status_code == 200
    completed = flight.json()
    assert completed["status"] == "completed"
    assert completed["stage"] == "completed"
    assert completed["flight_validation_passed"] is True
    assert completed["flight_score"] == 100.0
    assert completed["score"] == 90.1

    detail = client.get(f"/api/teacher/runs/{run['id']}", headers=headers(2)).json()
    event_types = [item["event_type"] for item in detail["events"]]
    assert "run_started" in event_types
    assert "section_visit" in event_types
    assert "hint" in event_types
    assert "wrong_operation" in event_types
    assert "submission" in event_types
    assert "flight_validation" in event_types

    gradebook = client.get(
        "/api/teacher/gradebook",
        headers=headers(2),
        params={"class_id": classroom["id"]},
    ).json()
    assert gradebook["completion_rate"] == 100.0
    assert gradebook["class_average"] == 90.1
    assert gradebook["students"][0]["average_score"] == 90.1

    analytics = client.get(
        "/api/teacher/analytics",
        headers=headers(2),
        params={"class_id": classroom["id"]},
    ).json()
    assert analytics["completion_rate"] == 100.0
    assert analytics["average_score"] == 90.1
    assert analytics["first_pass_rate"] == 100.0
    assert analytics["flight_validation_rate"] == 100.0
    assert analytics["average_hints"] == 1.0
    assert analytics["average_wrong_operations"] == 1.0

    csv_response = client.get(
        "/api/teacher/gradebook/export.csv",
        headers=headers(2),
        params={"class_id": classroom["id"]},
    )
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    text = csv_response.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0][0:2] == ["学生", "用户名"]
    assert "综合故障诊断与飞行验证" in rows[0]
    assert rows[1][0] == "学生A"
    assert "90.1" in rows[1]


def test_assignment_without_flight_finishes_on_diagnosis_and_permissions_are_scoped():
    client, _ = build_client()
    classroom, assignment = create_course(client, flight_required=False)
    run = client.post(
        f"/api/training/assignments/{assignment['id']}/start",
        headers=headers(3),
        json={"aircraft_id": 1},
    ).json()
    submitted = client.post(
        f"/api/training/runs/{run['id']}/submit",
        headers=headers(3),
        json={
            "passed": True,
            "score": 80,
            "elapsed_seconds": 500,
            "hints_used": 0,
            "wrong_operations": 0,
            "prearm_passed": True,
            "result": {"visited_sections": ["preflight"], "evaluation": {"score": 80}},
        },
    )
    assert submitted.status_code == 200
    result = submitted.json()
    assert result["status"] == "completed"
    # Flight component is excluded and remaining active weights normalize to 100.
    assert result["score"] == 82.5
    assert result["flight_score"] is None

    student_gradebook = client.get(
        "/api/teacher/gradebook",
        headers=headers(3),
        params={"class_id": classroom["id"]},
    )
    assert student_gradebook.status_code == 403

    other_teacher = client.get(
        "/api/teacher/gradebook",
        headers=headers(4),
        params={"class_id": classroom["id"]},
    )
    assert other_teacher.status_code == 403


def test_prearm_gate_advances_to_flight_on_progress_without_resubmitting_diagnosis():
    client, _ = build_client()
    _, assignment = create_course(client, flight_required=True)
    run = client.post(
        f"/api/training/assignments/{assignment['id']}/start",
        headers=headers(3),
        json={"aircraft_id": 1},
    ).json()
    submitted = client.post(
        f"/api/training/runs/{run['id']}/submit",
        headers=headers(3),
        json={
            "passed": True,
            "score": 86,
            "elapsed_seconds": 400,
            "hints_used": 0,
            "wrong_operations": 0,
            "prearm_passed": False,
            "result": {"visited_sections": ["rc", "power", "safety"], "evaluation": {"score": 86}},
        },
    ).json()
    assert submitted["status"] == "awaiting_prearm"
    assert submitted["stage"] == "awaiting_prearm"

    progressed = client.post(
        f"/api/training/runs/{run['id']}/progress",
        headers=headers(3),
        json={
            "score": 86,
            "elapsed_seconds": 460,
            "hints_used": 0,
            "wrong_operations": 0,
            "prearm_passed": True,
            "result": {"visited_sections": ["rc", "power", "safety", "preflight"], "evaluation": {"score": 86}},
        },
    )
    assert progressed.status_code == 200
    assert progressed.json()["status"] == "awaiting_flight"
    assert progressed.json()["stage"] == "awaiting_flight"


def test_completed_grade_is_idempotent_and_cannot_be_overwritten_by_progress():
    client, _ = build_client()
    _, assignment = create_course(client, flight_required=False)
    run = client.post(
        f"/api/training/assignments/{assignment['id']}/start",
        headers=headers(3), json={"aircraft_id": 1},
    ).json()
    completed = client.post(
        f"/api/training/runs/{run['id']}/submit",
        headers=headers(3),
        json={"passed": True, "score": 90, "elapsed_seconds": 400, "hints_used": 0, "wrong_operations": 0, "prearm_passed": True, "result": {"evaluation": {"score": 90}}},
    ).json()
    locked_score = completed["score"]
    assert completed["status"] == "completed"

    later = client.post(
        f"/api/training/runs/{run['id']}/progress",
        headers=headers(3),
        json={"score": 10, "elapsed_seconds": 999, "hints_used": 9, "wrong_operations": 9, "prearm_passed": False, "result": {"evaluation": {"score": 10}}},
    ).json()
    assert later["status"] == "completed"
    assert later["score"] == locked_score
    assert later["elapsed_seconds"] == 400
