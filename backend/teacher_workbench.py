from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Callable, Iterator, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import (
    AircraftRecord,
    AssignmentRecord,
    ClassEnrollmentRecord,
    ClassroomRecord,
    TrainingEventRecord,
    TrainingRunRecord,
    UserRecord,
)
from backend.training.catalog import FaultTrainingCase, load_training_cases


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _role(record: UserRecord) -> str:
    return record.role or "student"


def _require_teacher(record: UserRecord) -> None:
    if _role(record) not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要教师权限")


def _require_admin(record: UserRecord) -> None:
    if _role(record) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


def _can_manage_class(user: UserRecord, classroom: ClassroomRecord) -> bool:
    return _role(user) == "admin" or classroom.teacher_user_id == user.id


def _class_or_404(session: Session, class_id: int) -> ClassroomRecord:
    record = session.get(ClassroomRecord, class_id)
    if record is None or record.is_active == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="班级不存在")
    return record


def _managed_class_or_404(
    session: Session,
    current_user: UserRecord,
    class_id: int,
) -> ClassroomRecord:
    classroom = _class_or_404(session, class_id)
    if not _can_manage_class(current_user, classroom):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理该班级")
    return classroom


def _assignment_or_404(session: Session, assignment_id: int) -> AssignmentRecord:
    record = session.get(AssignmentRecord, assignment_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实训任务不存在")
    return record


def _training_case_map() -> dict[str, FaultTrainingCase]:
    try:
        return {item.id: item for item in load_training_cases()}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"实训案例库不可用：{error}",
        ) from error


def _invite_code(session: Session) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(20):
        code = "UAV-" + "".join(secrets.choice(alphabet) for _ in range(6))
        exists = session.scalar(
            select(ClassroomRecord.id).where(ClassroomRecord.invite_code == code)
        )
        if exists is None:
            return code
    raise RuntimeError("unable to allocate unique classroom invite code")


class ClassroomCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    academic_year: str = Field(default="", max_length=40)

    @field_validator("name", "academic_year")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ClassroomView(StrictModel):
    id: int
    name: str
    academic_year: str
    teacher_user_id: int
    teacher_name: str
    invite_code: str
    student_count: int
    assignment_count: int
    created_at: str


class JoinClassRequest(StrictModel):
    invite_code: str = Field(min_length=4, max_length=32)

    @field_validator("invite_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class EnrollmentView(StrictModel):
    class_id: int
    class_name: str
    teacher_name: str
    joined_at: str


class AssignmentCreate(StrictModel):
    class_id: int
    title: str = Field(min_length=2, max_length=160)
    scenario_id: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=1200)
    start_at: str | None = None
    due_at: str | None = None
    requirements: dict = Field(default_factory=dict)
    score_weights: dict = Field(default_factory=lambda: {
        "case_score": 70,
        "flight_validation": 20,
        "operation_norm": 10,
    })

    @field_validator("title", "scenario_id", "description")
    @classmethod
    def strip_assignment_text(cls, value: str) -> str:
        return value.strip()


class AssignmentView(StrictModel):
    id: int
    class_id: int
    class_name: str
    title: str
    scenario_id: str
    scenario_title: str
    description: str
    start_at: str | None
    due_at: str | None
    status: str
    assigned_count: int
    started_count: int
    completed_count: int
    average_score: float | None
    created_at: str


class StudentAssignmentView(StrictModel):
    id: int
    class_id: int
    class_name: str
    teacher_name: str
    title: str
    scenario_id: str
    scenario_title: str
    description: str
    difficulty: int
    recommended_minutes: int
    due_at: str | None
    assignment_status: str
    run_id: int | None
    run_status: str
    score: float | None
    elapsed_seconds: int


class StartRunRequest(StrictModel):
    aircraft_id: int | None = None


class TrainingRunView(StrictModel):
    id: int
    assignment_id: int
    assignment_title: str
    class_id: int
    class_name: str
    student_user_id: int
    student_name: str
    scenario_id: str
    scenario_title: str
    aircraft_id: int | None
    started_at: str
    ended_at: str | None
    status: str
    score: float | None
    elapsed_seconds: int
    hints_used: int
    wrong_operations: int
    first_pass: bool | None
    prearm_passed: bool
    flight_validation_passed: bool
    result: dict


class TrainingEventCreate(StrictModel):
    event_type: str = Field(default="operation", min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=180)
    detail: str = Field(default="", max_length=1200)
    payload: dict = Field(default_factory=dict)


class TrainingEventView(StrictModel):
    id: int
    created_at: str
    event_type: str
    title: str
    detail: str
    payload: dict


class TrainingRunDetail(StrictModel):
    run: TrainingRunView
    events: list[TrainingEventView]


class TrainingSubmitRequest(StrictModel):
    passed: bool
    score: float = Field(ge=0, le=100)
    elapsed_seconds: int = Field(ge=0, le=24 * 60 * 60)
    hints_used: int = Field(default=0, ge=0, le=100)
    wrong_operations: int = Field(default=0, ge=0, le=1000)
    prearm_passed: bool = False
    flight_validation_passed: bool = False
    result: dict = Field(default_factory=dict)


class TrainingProgressRequest(StrictModel):
    passed: bool = False
    score: float = Field(ge=0, le=100)
    elapsed_seconds: int = Field(ge=0, le=24 * 60 * 60)
    hints_used: int = Field(default=0, ge=0, le=100)
    wrong_operations: int = Field(default=0, ge=0, le=1000)
    prearm_passed: bool = False
    flight_validation_passed: bool = False
    result: dict = Field(default_factory=dict)


class FlightValidationRequest(StrictModel):
    passed: bool = True
    detail: str = Field(default="", max_length=1000)


class TeacherOverview(StrictModel):
    class_count: int
    student_count: int
    assignment_count: int
    active_assignment_count: int
    completed_run_count: int
    average_score: float | None
    recent_assignments: list[AssignmentView]


class StudentSummary(StrictModel):
    user_id: int
    display_name: str
    username: str
    class_id: int
    class_name: str
    completed_runs: int
    average_score: float | None
    average_elapsed_seconds: float | None
    total_hints: int
    total_wrong_operations: int
    first_pass_rate: float | None


class AdminUserView(StrictModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str


class AdminRoleUpdate(StrictModel):
    role: Literal["student", "teacher"]


def _class_view(session: Session, classroom: ClassroomRecord) -> ClassroomView:
    teacher = session.get(UserRecord, classroom.teacher_user_id)
    student_count = int(
        session.scalar(
            select(func.count(ClassEnrollmentRecord.id)).where(
                ClassEnrollmentRecord.class_id == classroom.id
            )
        )
        or 0
    )
    assignment_count = int(
        session.scalar(
            select(func.count(AssignmentRecord.id)).where(
                AssignmentRecord.class_id == classroom.id
            )
        )
        or 0
    )
    return ClassroomView(
        id=classroom.id,
        name=classroom.name,
        academic_year=classroom.academic_year or "",
        teacher_user_id=classroom.teacher_user_id,
        teacher_name=(teacher.display_name or teacher.username) if teacher else "未知教师",
        invite_code=classroom.invite_code,
        student_count=student_count,
        assignment_count=assignment_count,
        created_at=classroom.created_at,
    )


def _assignment_view(
    session: Session,
    record: AssignmentRecord,
    case_map: dict[str, FaultTrainingCase] | None = None,
) -> AssignmentView:
    classroom = session.get(ClassroomRecord, record.class_id)
    cases = case_map or _training_case_map()
    training_case = cases.get(record.scenario_id)
    assigned_count = int(
        session.scalar(
            select(func.count(ClassEnrollmentRecord.id)).where(
                ClassEnrollmentRecord.class_id == record.class_id
            )
        )
        or 0
    )
    started_count = int(
        session.scalar(
            select(func.count(TrainingRunRecord.id)).where(
                TrainingRunRecord.assignment_id == record.id
            )
        )
        or 0
    )
    completed_count = int(
        session.scalar(
            select(func.count(TrainingRunRecord.id)).where(
                TrainingRunRecord.assignment_id == record.id,
                TrainingRunRecord.status == "completed",
            )
        )
        or 0
    )
    average_score = session.scalar(
        select(func.avg(TrainingRunRecord.score)).where(
            TrainingRunRecord.assignment_id == record.id,
            TrainingRunRecord.status == "completed",
            TrainingRunRecord.score.is_not(None),
        )
    )
    return AssignmentView(
        id=record.id,
        class_id=record.class_id,
        class_name=classroom.name if classroom else "未知班级",
        title=record.title,
        scenario_id=record.scenario_id,
        scenario_title=training_case.title if training_case else record.scenario_id,
        description=record.description or "",
        start_at=record.start_at,
        due_at=record.due_at,
        status=record.status,
        assigned_count=assigned_count,
        started_count=started_count,
        completed_count=completed_count,
        average_score=round(float(average_score), 1) if average_score is not None else None,
        created_at=record.created_at,
    )


def _run_view(
    session: Session,
    record: TrainingRunRecord,
    case_map: dict[str, FaultTrainingCase] | None = None,
) -> TrainingRunView:
    assignment = session.get(AssignmentRecord, record.assignment_id)
    classroom = session.get(ClassroomRecord, assignment.class_id) if assignment else None
    student = session.get(UserRecord, record.student_user_id)
    cases = case_map or _training_case_map()
    training_case = cases.get(record.scenario_id)
    return TrainingRunView(
        id=record.id,
        assignment_id=record.assignment_id,
        assignment_title=assignment.title if assignment else "未知任务",
        class_id=assignment.class_id if assignment else 0,
        class_name=classroom.name if classroom else "未知班级",
        student_user_id=record.student_user_id,
        student_name=(student.display_name or student.username) if student else "未知学生",
        scenario_id=record.scenario_id,
        scenario_title=training_case.title if training_case else record.scenario_id,
        aircraft_id=record.aircraft_id,
        started_at=record.started_at,
        ended_at=record.ended_at,
        status=record.status,
        score=round(float(record.score), 1) if record.score is not None else None,
        elapsed_seconds=int(record.elapsed_seconds or 0),
        hints_used=int(record.hints_used or 0),
        wrong_operations=int(record.wrong_operations or 0),
        first_pass=None if record.first_pass is None else bool(record.first_pass),
        prearm_passed=bool(record.prearm_passed),
        flight_validation_passed=bool(record.flight_validation_passed),
        result=record.result_json or {},
    )


def _event_view(record: TrainingEventRecord) -> TrainingEventView:
    return TrainingEventView(
        id=record.id,
        created_at=record.created_at,
        event_type=record.event_type,
        title=record.title,
        detail=record.detail or "",
        payload=record.payload_json or {},
    )


def _run_access_or_404(
    session: Session,
    current_user: UserRecord,
    run_id: int,
) -> TrainingRunRecord:
    run = session.get(TrainingRunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="实训记录不存在")
    if run.student_user_id == current_user.id:
        return run
    assignment = session.get(AssignmentRecord, run.assignment_id)
    if assignment:
        classroom = session.get(ClassroomRecord, assignment.class_id)
        if classroom and _can_manage_class(current_user, classroom):
            return run
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该实训记录")


def _append_event(
    session: Session,
    run: TrainingRunRecord,
    *,
    event_type: str,
    title: str,
    detail: str = "",
    payload: dict | None = None,
) -> TrainingEventRecord:
    event = TrainingEventRecord(
        run_id=run.id,
        created_at=utc_now_iso(),
        event_type=event_type,
        title=title,
        detail=detail,
        payload_json=payload or {},
    )
    session.add(event)
    return event


def register_teacher_workbench_routes(
    app: FastAPI,
    get_db: Callable[..., Iterator[Session]],
    get_current_user: Callable[..., UserRecord],
) -> None:
    @app.get("/api/teacher/overview", response_model=TeacherOverview)
    def teacher_overview(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TeacherOverview:
        _require_teacher(current_user)
        class_statement = select(ClassroomRecord).where(ClassroomRecord.is_active != 0)
        if _role(current_user) != "admin":
            class_statement = class_statement.where(ClassroomRecord.teacher_user_id == current_user.id)
        classes = session.scalars(class_statement.order_by(ClassroomRecord.id.desc())).all()
        class_ids = [item.id for item in classes]
        if not class_ids:
            return TeacherOverview(
                class_count=0,
                student_count=0,
                assignment_count=0,
                active_assignment_count=0,
                completed_run_count=0,
                average_score=None,
                recent_assignments=[],
            )
        student_count = int(
            session.scalar(
                select(func.count(func.distinct(ClassEnrollmentRecord.student_user_id))).where(
                    ClassEnrollmentRecord.class_id.in_(class_ids)
                )
            )
            or 0
        )
        assignments = session.scalars(
            select(AssignmentRecord)
            .where(AssignmentRecord.class_id.in_(class_ids))
            .order_by(AssignmentRecord.id.desc())
        ).all()
        assignment_ids = [item.id for item in assignments]
        completed_run_count = 0
        average_score = None
        if assignment_ids:
            completed_run_count = int(
                session.scalar(
                    select(func.count(TrainingRunRecord.id)).where(
                        TrainingRunRecord.assignment_id.in_(assignment_ids),
                        TrainingRunRecord.status == "completed",
                    )
                )
                or 0
            )
            average_score_raw = session.scalar(
                select(func.avg(TrainingRunRecord.score)).where(
                    TrainingRunRecord.assignment_id.in_(assignment_ids),
                    TrainingRunRecord.status == "completed",
                    TrainingRunRecord.score.is_not(None),
                )
            )
            average_score = round(float(average_score_raw), 1) if average_score_raw is not None else None
        cases = _training_case_map()
        return TeacherOverview(
            class_count=len(classes),
            student_count=student_count,
            assignment_count=len(assignments),
            active_assignment_count=sum(1 for item in assignments if item.status == "active"),
            completed_run_count=completed_run_count,
            average_score=average_score,
            recent_assignments=[_assignment_view(session, item, cases) for item in assignments[:5]],
        )

    @app.get("/api/teacher/classes", response_model=list[ClassroomView])
    def teacher_classes(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[ClassroomView]:
        _require_teacher(current_user)
        statement = select(ClassroomRecord).where(ClassroomRecord.is_active != 0)
        if _role(current_user) != "admin":
            statement = statement.where(ClassroomRecord.teacher_user_id == current_user.id)
        records = session.scalars(statement.order_by(ClassroomRecord.id.desc())).all()
        return [_class_view(session, item) for item in records]

    @app.post("/api/teacher/classes", response_model=ClassroomView, status_code=201)
    def create_classroom(
        command: ClassroomCreate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> ClassroomView:
        _require_teacher(current_user)
        record = ClassroomRecord(
            name=command.name,
            teacher_user_id=current_user.id,
            academic_year=command.academic_year,
            invite_code=_invite_code(session),
            is_active=1,
            created_at=utc_now_iso(),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return _class_view(session, record)

    @app.get("/api/teacher/assignments", response_model=list[AssignmentView])
    def teacher_assignments(
        class_id: int | None = Query(default=None),
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[AssignmentView]:
        _require_teacher(current_user)
        statement = select(AssignmentRecord)
        if class_id is not None:
            _managed_class_or_404(session, current_user, class_id)
            statement = statement.where(AssignmentRecord.class_id == class_id)
        elif _role(current_user) != "admin":
            owned_class_ids = select(ClassroomRecord.id).where(
                ClassroomRecord.teacher_user_id == current_user.id,
                ClassroomRecord.is_active != 0,
            )
            statement = statement.where(AssignmentRecord.class_id.in_(owned_class_ids))
        records = session.scalars(statement.order_by(AssignmentRecord.id.desc())).all()
        cases = _training_case_map()
        return [_assignment_view(session, item, cases) for item in records]

    @app.post("/api/teacher/assignments", response_model=AssignmentView, status_code=201)
    def create_assignment(
        command: AssignmentCreate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AssignmentView:
        _require_teacher(current_user)
        classroom = _managed_class_or_404(session, current_user, command.class_id)
        cases = _training_case_map()
        if command.scenario_id not in cases:
            raise HTTPException(status_code=422, detail="案例编号不存在")
        record = AssignmentRecord(
            class_id=classroom.id,
            teacher_user_id=current_user.id,
            title=command.title,
            scenario_id=command.scenario_id,
            description=command.description,
            start_at=command.start_at,
            due_at=command.due_at,
            status="active",
            requirements_json=command.requirements,
            score_weights_json=command.score_weights,
            created_at=utc_now_iso(),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return _assignment_view(session, record, cases)

    @app.get("/api/teacher/runs", response_model=list[TrainingRunView])
    def teacher_runs(
        assignment_id: int | None = Query(default=None),
        class_id: int | None = Query(default=None),
        run_status: str | None = Query(default=None, alias="status"),
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[TrainingRunView]:
        _require_teacher(current_user)
        statement = select(TrainingRunRecord)
        if assignment_id is not None:
            assignment = _assignment_or_404(session, assignment_id)
            _managed_class_or_404(session, current_user, assignment.class_id)
            statement = statement.where(TrainingRunRecord.assignment_id == assignment_id)
        elif class_id is not None:
            _managed_class_or_404(session, current_user, class_id)
            assignment_ids = select(AssignmentRecord.id).where(AssignmentRecord.class_id == class_id)
            statement = statement.where(TrainingRunRecord.assignment_id.in_(assignment_ids))
        elif _role(current_user) != "admin":
            class_ids = select(ClassroomRecord.id).where(
                ClassroomRecord.teacher_user_id == current_user.id,
                ClassroomRecord.is_active != 0,
            )
            assignment_ids = select(AssignmentRecord.id).where(AssignmentRecord.class_id.in_(class_ids))
            statement = statement.where(TrainingRunRecord.assignment_id.in_(assignment_ids))
        if run_status:
            statement = statement.where(TrainingRunRecord.status == run_status)
        records = session.scalars(statement.order_by(TrainingRunRecord.id.desc())).all()
        cases = _training_case_map()
        return [_run_view(session, item, cases) for item in records]

    @app.get("/api/teacher/runs/{run_id}", response_model=TrainingRunDetail)
    def teacher_run_detail(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunDetail:
        _require_teacher(current_user)
        run = _run_access_or_404(session, current_user, run_id)
        events = session.scalars(
            select(TrainingEventRecord)
            .where(TrainingEventRecord.run_id == run.id)
            .order_by(TrainingEventRecord.id)
        ).all()
        return TrainingRunDetail(
            run=_run_view(session, run),
            events=[_event_view(item) for item in events],
        )

    @app.get("/api/teacher/students", response_model=list[StudentSummary])
    def teacher_students(
        class_id: int | None = Query(default=None),
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[StudentSummary]:
        _require_teacher(current_user)
        if class_id is not None:
            classes = [_managed_class_or_404(session, current_user, class_id)]
        else:
            statement = select(ClassroomRecord).where(ClassroomRecord.is_active != 0)
            if _role(current_user) != "admin":
                statement = statement.where(ClassroomRecord.teacher_user_id == current_user.id)
            classes = session.scalars(statement.order_by(ClassroomRecord.id.desc())).all()
        result: list[StudentSummary] = []
        for classroom in classes:
            enrollments = session.scalars(
                select(ClassEnrollmentRecord).where(ClassEnrollmentRecord.class_id == classroom.id)
            ).all()
            assignment_ids = select(AssignmentRecord.id).where(AssignmentRecord.class_id == classroom.id)
            for enrollment in enrollments:
                student = session.get(UserRecord, enrollment.student_user_id)
                if student is None:
                    continue
                runs = session.scalars(
                    select(TrainingRunRecord).where(
                        TrainingRunRecord.student_user_id == student.id,
                        TrainingRunRecord.assignment_id.in_(assignment_ids),
                    )
                ).all()
                completed = [run for run in runs if run.status == "completed"]
                scores = [float(run.score) for run in completed if run.score is not None]
                elapsed = [float(run.elapsed_seconds or 0) for run in completed]
                first_pass_values = [bool(run.first_pass) for run in completed if run.first_pass is not None]
                result.append(StudentSummary(
                    user_id=student.id,
                    display_name=student.display_name or student.username,
                    username=student.username,
                    class_id=classroom.id,
                    class_name=classroom.name,
                    completed_runs=len(completed),
                    average_score=round(sum(scores) / len(scores), 1) if scores else None,
                    average_elapsed_seconds=round(sum(elapsed) / len(elapsed), 1) if elapsed else None,
                    total_hints=sum(int(run.hints_used or 0) for run in runs),
                    total_wrong_operations=sum(int(run.wrong_operations or 0) for run in runs),
                    first_pass_rate=round(100 * sum(first_pass_values) / len(first_pass_values), 1) if first_pass_values else None,
                ))
        return result

    @app.post("/api/training/classes/join", response_model=EnrollmentView)
    def join_classroom(
        command: JoinClassRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> EnrollmentView:
        if _role(current_user) != "student":
            raise HTTPException(status_code=409, detail="教师/管理员账号不加入学生班级")
        classroom = session.scalar(
            select(ClassroomRecord).where(
                ClassroomRecord.invite_code == command.invite_code,
                ClassroomRecord.is_active != 0,
            )
        )
        if classroom is None:
            raise HTTPException(status_code=404, detail="班级邀请码无效")
        enrollment = session.scalar(
            select(ClassEnrollmentRecord).where(
                ClassEnrollmentRecord.class_id == classroom.id,
                ClassEnrollmentRecord.student_user_id == current_user.id,
            )
        )
        if enrollment is None:
            enrollment = ClassEnrollmentRecord(
                class_id=classroom.id,
                student_user_id=current_user.id,
                joined_at=utc_now_iso(),
            )
            session.add(enrollment)
            session.commit()
            session.refresh(enrollment)
        teacher = session.get(UserRecord, classroom.teacher_user_id)
        return EnrollmentView(
            class_id=classroom.id,
            class_name=classroom.name,
            teacher_name=(teacher.display_name or teacher.username) if teacher else "未知教师",
            joined_at=enrollment.joined_at,
        )

    @app.get("/api/training/classes", response_model=list[EnrollmentView])
    def my_classes(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[EnrollmentView]:
        enrollments = session.scalars(
            select(ClassEnrollmentRecord)
            .where(ClassEnrollmentRecord.student_user_id == current_user.id)
            .order_by(ClassEnrollmentRecord.id.desc())
        ).all()
        result: list[EnrollmentView] = []
        for enrollment in enrollments:
            classroom = session.get(ClassroomRecord, enrollment.class_id)
            if classroom is None or classroom.is_active == 0:
                continue
            teacher = session.get(UserRecord, classroom.teacher_user_id)
            result.append(EnrollmentView(
                class_id=classroom.id,
                class_name=classroom.name,
                teacher_name=(teacher.display_name or teacher.username) if teacher else "未知教师",
                joined_at=enrollment.joined_at,
            ))
        return result

    @app.get("/api/training/assignments", response_model=list[StudentAssignmentView])
    def my_assignments(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[StudentAssignmentView]:
        enrollment_class_ids = [
            item.class_id
            for item in session.scalars(
                select(ClassEnrollmentRecord).where(
                    ClassEnrollmentRecord.student_user_id == current_user.id
                )
            ).all()
        ]
        if not enrollment_class_ids:
            return []
        assignments = session.scalars(
            select(AssignmentRecord)
            .where(
                AssignmentRecord.class_id.in_(enrollment_class_ids),
                AssignmentRecord.status == "active",
            )
            .order_by(AssignmentRecord.id.desc())
        ).all()
        cases = _training_case_map()
        result: list[StudentAssignmentView] = []
        for assignment in assignments:
            classroom = session.get(ClassroomRecord, assignment.class_id)
            teacher = session.get(UserRecord, classroom.teacher_user_id) if classroom else None
            training_case = cases.get(assignment.scenario_id)
            run = session.scalar(
                select(TrainingRunRecord).where(
                    TrainingRunRecord.assignment_id == assignment.id,
                    TrainingRunRecord.student_user_id == current_user.id,
                )
            )
            result.append(StudentAssignmentView(
                id=assignment.id,
                class_id=assignment.class_id,
                class_name=classroom.name if classroom else "未知班级",
                teacher_name=(teacher.display_name or teacher.username) if teacher else "未知教师",
                title=assignment.title,
                scenario_id=assignment.scenario_id,
                scenario_title=training_case.title if training_case else assignment.scenario_id,
                description=assignment.description or "",
                difficulty=training_case.difficulty if training_case else 1,
                recommended_minutes=training_case.recommended_minutes if training_case else 20,
                due_at=assignment.due_at,
                assignment_status=assignment.status,
                run_id=run.id if run else None,
                run_status=run.status if run else "not_started",
                score=round(float(run.score), 1) if run and run.score is not None else None,
                elapsed_seconds=int(run.elapsed_seconds or 0) if run else 0,
            ))
        return result

    @app.post("/api/training/assignments/{assignment_id}/start", response_model=TrainingRunView)
    def start_assignment_run(
        assignment_id: int,
        command: StartRunRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunView:
        assignment = _assignment_or_404(session, assignment_id)
        enrollment = session.scalar(
            select(ClassEnrollmentRecord).where(
                ClassEnrollmentRecord.class_id == assignment.class_id,
                ClassEnrollmentRecord.student_user_id == current_user.id,
            )
        )
        if enrollment is None:
            raise HTTPException(status_code=403, detail="你不属于该任务班级")
        if assignment.status != "active":
            raise HTTPException(status_code=409, detail="该任务当前不可开始")
        start_at = _parse_time(assignment.start_at)
        now = datetime.now(timezone.utc)
        if start_at and now < start_at:
            raise HTTPException(status_code=409, detail="任务尚未开始")
        due_at = _parse_time(assignment.due_at)
        if due_at and now > due_at:
            raise HTTPException(status_code=409, detail="任务已截止")
        if command.aircraft_id is not None:
            aircraft = session.get(AircraftRecord, command.aircraft_id)
            if aircraft is None or aircraft.owner_user_id != current_user.id:
                raise HTTPException(status_code=404, detail="所选飞机不存在")
        existing = session.scalar(
            select(TrainingRunRecord).where(
                TrainingRunRecord.assignment_id == assignment.id,
                TrainingRunRecord.student_user_id == current_user.id,
            )
        )
        if existing is not None:
            if command.aircraft_id is not None and existing.aircraft_id is None:
                existing.aircraft_id = command.aircraft_id
                session.commit()
            return _run_view(session, existing)
        run = TrainingRunRecord(
            assignment_id=assignment.id,
            student_user_id=current_user.id,
            aircraft_id=command.aircraft_id,
            scenario_id=assignment.scenario_id,
            started_at=utc_now_iso(),
            ended_at=None,
            status="in_progress",
            score=None,
            elapsed_seconds=0,
            hints_used=0,
            wrong_operations=0,
            first_pass=None,
            prearm_passed=0,
            flight_validation_passed=0,
            result_json={},
        )
        session.add(run)
        session.flush()
        _append_event(
            session,
            run,
            event_type="run_started",
            title="开始实训任务",
            detail=assignment.title,
            payload={"scenario_id": assignment.scenario_id},
        )
        session.commit()
        session.refresh(run)
        return _run_view(session, run)

    @app.get("/api/training/runs/{run_id}", response_model=TrainingRunDetail)
    def my_run_detail(
        run_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunDetail:
        run = _run_access_or_404(session, current_user, run_id)
        events = session.scalars(
            select(TrainingEventRecord)
            .where(TrainingEventRecord.run_id == run.id)
            .order_by(TrainingEventRecord.id)
        ).all()
        return TrainingRunDetail(run=_run_view(session, run), events=[_event_view(item) for item in events])

    @app.post("/api/training/runs/{run_id}/events", response_model=TrainingEventView, status_code=201)
    def append_training_event(
        run_id: int,
        command: TrainingEventCreate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingEventView:
        run = _run_access_or_404(session, current_user, run_id)
        if run.student_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有学生本人可写入实训过程")
        event = _append_event(
            session,
            run,
            event_type=command.event_type,
            title=command.title,
            detail=command.detail,
            payload=command.payload,
        )
        session.commit()
        session.refresh(event)
        return _event_view(event)

    @app.post("/api/training/runs/{run_id}/progress", response_model=TrainingRunView)
    def update_training_progress(
        run_id: int,
        command: TrainingProgressRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunView:
        run = _run_access_or_404(session, current_user, run_id)
        if run.student_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有学生本人可更新实训进度")
        previous_result = run.result_json if isinstance(run.result_json, dict) else {}
        previous_sections = set(previous_result.get("visited_sections") or [])
        next_sections = list(command.result.get("visited_sections") or [])
        for section in next_sections:
            if section not in previous_sections:
                _append_event(
                    session,
                    run,
                    event_type="section_visit",
                    title="进入调试模块",
                    detail=str(section),
                    payload={"section": section},
                )
        previous_hints = int(previous_result.get("hints_used") or 0)
        if command.hints_used > previous_hints:
            _append_event(
                session, run, event_type="hint", title="使用案例提示",
                detail=f"累计使用 {command.hints_used} 次提示", payload={"hints_used": command.hints_used},
            )
        previous_wrong = int(previous_result.get("wrong_operations") or 0)
        if command.wrong_operations > previous_wrong:
            _append_event(
                session, run, event_type="wrong_operation", title="记录错误操作",
                detail=f"累计 {command.wrong_operations} 次", payload={"wrong_operations": command.wrong_operations},
            )
        previous_conditions = previous_result.get("condition_state") if isinstance(previous_result.get("condition_state"), dict) else {}
        next_conditions = command.result.get("condition_state") if isinstance(command.result.get("condition_state"), dict) else {}
        for key, passed in next_conditions.items():
            if passed is True and previous_conditions.get(key) is not True:
                _append_event(
                    session, run, event_type="condition_passed", title="完成验证条件",
                    detail=str(key), payload={"condition": key},
                )
        run.score = float(command.score)
        run.elapsed_seconds = command.elapsed_seconds
        run.hints_used = command.hints_used
        run.wrong_operations = command.wrong_operations
        run.prearm_passed = 1 if command.prearm_passed else 0
        run.result_json = command.result
        session.commit()
        session.refresh(run)
        return _run_view(session, run)

    @app.post("/api/training/runs/{run_id}/submit", response_model=TrainingRunView)
    def submit_training_run(
        run_id: int,
        command: TrainingSubmitRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunView:
        run = _run_access_or_404(session, current_user, run_id)
        if run.student_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有学生本人可提交实训")
        previous_submissions = int(
            session.scalar(
                select(func.count(TrainingEventRecord.id)).where(
                    TrainingEventRecord.run_id == run.id,
                    TrainingEventRecord.event_type == "submission",
                )
            )
            or 0
        )
        run.score = float(command.score)
        run.elapsed_seconds = command.elapsed_seconds
        run.hints_used = command.hints_used
        run.wrong_operations = command.wrong_operations
        run.prearm_passed = 1 if command.prearm_passed else 0
        run.flight_validation_passed = 1 if command.flight_validation_passed else 0
        run.result_json = command.result
        if command.passed:
            run.status = "completed"
            run.ended_at = utc_now_iso()
            run.first_pass = 1 if previous_submissions == 0 else 0
        else:
            run.status = "in_progress"
            run.ended_at = None
            if run.first_pass is None:
                run.first_pass = 0
        _append_event(
            session,
            run,
            event_type="submission",
            title="提交诊断结果" if command.passed else "提交未通过",
            detail=f"得分 {command.score:.0f}/100",
            payload={
                "passed": command.passed,
                "score": command.score,
                "elapsed_seconds": command.elapsed_seconds,
                "hints_used": command.hints_used,
                "wrong_operations": command.wrong_operations,
                "prearm_passed": command.prearm_passed,
            },
        )
        session.commit()
        session.refresh(run)
        return _run_view(session, run)

    @app.post("/api/training/runs/{run_id}/flight-validation", response_model=TrainingRunView)
    def record_flight_validation(
        run_id: int,
        command: FlightValidationRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> TrainingRunView:
        run = _run_access_or_404(session, current_user, run_id)
        if run.student_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有学生本人可更新飞行验证")
        run.flight_validation_passed = 1 if command.passed else 0
        _append_event(
            session,
            run,
            event_type="flight_validation",
            title="飞行验证通过" if command.passed else "飞行验证未通过",
            detail=command.detail,
            payload={"passed": command.passed},
        )
        session.commit()
        session.refresh(run)
        return _run_view(session, run)

    @app.get("/api/admin/users", response_model=list[AdminUserView])
    def admin_users(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[AdminUserView]:
        _require_admin(current_user)
        users = session.scalars(select(UserRecord).order_by(UserRecord.id)).all()
        return [
            AdminUserView(
                id=item.id,
                username=item.username,
                display_name=item.display_name or item.username,
                role=_role(item),
                is_active=item.is_active != 0,
                created_at=item.created_at or "",
            )
            for item in users
        ]

    @app.patch("/api/admin/users/{user_id}/role", response_model=AdminUserView)
    def admin_update_user_role(
        user_id: int,
        command: AdminRoleUpdate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AdminUserView:
        _require_admin(current_user)
        target = session.get(UserRecord, user_id)
        if target is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        if target.id == current_user.id:
            raise HTTPException(status_code=409, detail="不能修改当前管理员自己的角色")
        if _role(target) == "admin":
            raise HTTPException(status_code=409, detail="不能通过教师工作台修改其他管理员角色")
        target.role = command.role
        session.commit()
        session.refresh(target)
        return AdminUserView(
            id=target.id,
            username=target.username,
            display_name=target.display_name or target.username,
            role=_role(target),
            is_active=target.is_active != 0,
            created_at=target.created_at or "",
        )
