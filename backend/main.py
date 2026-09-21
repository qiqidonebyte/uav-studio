from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Iterator

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from backend.database import (
    DEFAULT_DATABASE_URL,
    DEFAULT_SIMULATIONS_DIR,
    build_engine,
    build_session_factory,
    ensure_schema_compatibility,
)
from backend.engineering import (
    EngineeringInputError,
    calculate_aircraft_engineering,
    validate_configuration,
)
from backend.experiments import list_experiments, load_replay, save_experiment
from backend.assembly_instances import default_assembly_instances
from backend.aircraft_library import (
    duplicate_name,
    ensure_aircraft_metadata,
    template_by_key,
    template_definitions,
    utc_now_iso,
)
from backend.component_library import register_component_library_routes
from backend.classroom_reliability import (
    recover_classroom_reliability,
    register_classroom_reliability_routes,
    shutdown_classroom_reliability,
)
from backend.auth import (
    AIRCRAFT_LIMIT_PER_USER,
    SESSION_COOKIE_NAME,
    ensure_legacy_aircraft_ownership,
    register_auth_routes,
    require_current_user,
    session_user,
)
from backend.user_settings import ensure_admin_user, register_user_settings_routes
from backend.models import AircraftRecord, Base, ComponentRecord, SimulationRecord, UserRecord
from backend.p0_validation import augment_validation
from backend.schemas import (
    AircraftCreateFromTemplate,
    AircraftDefinition,
    AircraftDuplicateRequest,
    AircraftLibraryItem,
    AircraftMetadataUpdate,
    AircraftTemplate,
    AssemblyInstance,
    AssemblyState,
    Component,
    ComponentType,
    ExperimentReplay,
    ExperimentSummary,
    PropellerMountDirections,
    SimulationCreateRequest,
    SimulationSnapshot,
    TargetCommand,
    TakeoffCommand,
    Vector3,
    WaypointCommand,
    WindCommand,
)
from backend.seed import seed_database
from backend.simulation_manager import SimulationManager, SimulationNotFoundError


def _component_from_record(record: ComponentRecord) -> Component:
    return Component(
        id=record.id,
        name=record.name,
        type=record.type,
        mass_kg=record.mass_kg,
        parameters_json=record.parameters_json,
    )


def _aircraft_from_record(record: AircraftRecord) -> AircraftDefinition:
    base = AircraftDefinition(
        id=record.id,
        name=record.name,
        frame_id=record.frame_id,
        motor_id=record.motor_id,
        esc_id=record.esc_id,
        propeller_id=record.propeller_id,
        propeller_directions=(
            PropellerMountDirections.model_validate(record.propeller_directions_json)
            if record.propeller_directions_json is not None
            else PropellerMountDirections()
        ),
        battery_id=record.battery_id,
        power_module_id=record.power_module_id,
        flight_controller_id=record.flight_controller_id,
        gnss_id=record.gnss_id,
        payload_id=record.payload_id,
        gnss_position_m=(
            Vector3.model_validate(record.gnss_position_json)
            if record.gnss_position_json is not None
            else None
        ),
        payload_position_m=(
            Vector3.model_validate(record.payload_position_json)
            if record.payload_position_json is not None
            else None
        ),
        assembly_instances=(
            [
                AssemblyInstance.model_validate(item)
                for item in record.assembly_instances_json
            ]
            if isinstance(record.assembly_instances_json, list)
            else []
        ),
    )
    # Existing databases have NULL in the new additive column. Treat them as
    # the old "fully assembled from slot IDs" state, then persist explicit
    # physical instances on the next edit.
    if record.assembly_instances_json is None:
        return base.model_copy(
            update={"assembly_instances": default_assembly_instances(base)}
        )
    return base


def _catalog(session: Session) -> dict[int, Component]:
    records = session.scalars(
        select(ComponentRecord).order_by(ComponentRecord.id)
    ).all()
    return {record.id: _component_from_record(record) for record in records}


def _assembly_state(
    aircraft: AircraftDefinition,
    session: Session,
) -> AssemblyState:
    catalog = _catalog(session)
    base_validation = validate_configuration(aircraft, catalog)
    validation = augment_validation(aircraft, base_validation)
    try:
        engineering = calculate_aircraft_engineering(aircraft, catalog)
    except EngineeringInputError:
        engineering = None
    else:
        engineering = engineering.model_copy(update={"validation": validation})
    return AssemblyState(
        aircraft=aircraft,
        engineering=engineering,
        validation=validation,
    )


def _record_timestamp(record: AircraftRecord, field: str) -> str:
    value = getattr(record, field, None)
    if isinstance(value, str) and value:
        return value
    return utc_now_iso()


def _aircraft_library_item(
    record: AircraftRecord,
    session: Session,
) -> AircraftLibraryItem:
    state = _assembly_state(_aircraft_from_record(record), session)
    experiment_count = (
        session.scalar(
            select(func.count(SimulationRecord.id)).where(
                SimulationRecord.aircraft_id == record.id
            )
        )
        or 0
    )
    return AircraftLibraryItem(
        aircraft=state.aircraft,
        engineering=state.engineering,
        validation=state.validation,
        description=record.description or "",
        created_at=_record_timestamp(record, "created_at"),
        updated_at=_record_timestamp(record, "updated_at"),
        experiment_count=experiment_count,
    )


def _touch_new_aircraft(record: AircraftRecord, description: str = "") -> None:
    now = utc_now_iso()
    record.description = description
    record.created_at = now
    record.updated_at = now


def _touch_aircraft(record: AircraftRecord) -> None:
    if not record.created_at:
        record.created_at = utc_now_iso()
    record.updated_at = utc_now_iso()




def _update_aircraft_record(
    record: AircraftRecord,
    aircraft: AircraftDefinition,
) -> None:
    record.name = aircraft.name
    record.frame_id = aircraft.frame_id
    record.motor_id = aircraft.motor_id
    record.esc_id = aircraft.esc_id
    record.propeller_id = aircraft.propeller_id
    record.propeller_directions_json = aircraft.propeller_directions.model_dump()
    record.battery_id = aircraft.battery_id
    record.power_module_id = aircraft.power_module_id
    record.flight_controller_id = aircraft.flight_controller_id
    record.gnss_id = aircraft.gnss_id
    record.payload_id = aircraft.payload_id
    record.gnss_position_json = (
        aircraft.gnss_position_m.model_dump()
        if aircraft.gnss_position_m is not None
        else None
    )
    record.payload_position_json = (
        aircraft.payload_position_m.model_dump()
        if aircraft.payload_position_m is not None
        else None
    )
    physical_instances = (
        aircraft.assembly_instances
        if "assembly_instances" in aircraft.model_fields_set
        else default_assembly_instances(aircraft)
    )
    record.assembly_instances_json = [
        item.model_dump()
        for item in physical_instances
    ]
    _touch_aircraft(record)


def create_app(
    database_url: str = DEFAULT_DATABASE_URL,
    simulations_dir: Path | None = None,
) -> FastAPI:
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)
    simulation_manager = SimulationManager()
    telemetry_dir = simulations_dir or DEFAULT_SIMULATIONS_DIR

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(engine)
        ensure_schema_compatibility(engine)
        with session_factory() as session:
            seed_database(session)
            recover_classroom_reliability(session)
            ensure_aircraft_metadata(session)
            admin = ensure_admin_user(session)
            ensure_legacy_aircraft_ownership(session, admin)
            next_simulation_id = (
                session.scalar(select(func.max(SimulationRecord.id))) or 0
            ) + 1
            simulation_manager.set_next_id(next_simulation_id)
        yield
        shutdown_classroom_reliability()
        await simulation_manager.shutdown()
        engine.dispose()

    app = FastAPI(
        title="UAV Studio V1 API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.session_factory = session_factory
    app.state.simulation_manager = simulation_manager
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StaleDataError)
    async def stale_training_write_handler(_request: Request, _error: StaleDataError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "实训状态已被另一个请求更新，请刷新后重试"},
        )

    def get_db(request: Request) -> Iterator[Session]:
        with request.app.state.session_factory() as session:
            yield session

    @app.middleware("http")
    async def require_login_for_api(request: Request, call_next):
        path = request.url.path
        public_api = {
            "/api/health",
            "/api/auth/login",
            "/api/auth/register",
        }
        if (
            request.method != "OPTIONS"
            and path.startswith("/api/")
            and path not in public_api
        ):
            with request.app.state.session_factory() as auth_session:
                user = session_user(
                    auth_session,
                    request.cookies.get(SESSION_COOKIE_NAME),
                )
                if user is None:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "请先登录"},
                    )
                request.state.user_id = user.id
        return await call_next(request)

    def get_current_user(
        request: Request,
        session: Session = Depends(get_db),
    ) -> UserRecord:
        return require_current_user(request, session)

    def owned_aircraft_or_404(
        session: Session,
        current_user: UserRecord,
        aircraft_id: int,
    ) -> AircraftRecord:
        record = session.get(AircraftRecord, aircraft_id)
        if record is None or record.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="飞机不存在",
            )
        return record

    def owned_aircraft_count(session: Session, current_user: UserRecord) -> int:
        return int(
            session.scalar(
                select(func.count(AircraftRecord.id)).where(
                    AircraftRecord.owner_user_id == current_user.id
                )
            )
            or 0
        )

    def ensure_aircraft_capacity(
        session: Session,
        current_user: UserRecord,
    ) -> None:
        if owned_aircraft_count(session, current_user) >= AIRCRAFT_LIMIT_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"每个用户最多保存 {AIRCRAFT_LIMIT_PER_USER} 架飞机，请删除或整理现有设计后再创建。",
            )

    def manager_for_user_or_404(
        simulation_id: int,
        session: Session,
        current_user: UserRecord,
    ):
        try:
            simulation = simulation_manager.require(simulation_id)
        except SimulationNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仿真不存在",
            ) from error
        aircraft_id = simulation.simulator.aircraft.id
        if not isinstance(aircraft_id, int):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仿真不存在",
            )
        owned_aircraft_or_404(session, current_user, aircraft_id)
        return simulation

    register_auth_routes(app, get_db)
    register_user_settings_routes(app, get_db, get_current_user)
    register_classroom_reliability_routes(app, get_db, get_current_user)
    register_component_library_routes(app, get_db)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/components", response_model=list[Component])
    def list_components(
        component_type: ComponentType | None = Query(default=None, alias="type"),
        session: Session = Depends(get_db),
    ) -> list[Component]:
        statement = select(ComponentRecord)
        if component_type is not None:
            statement = statement.where(ComponentRecord.type == component_type)
        records = session.scalars(
            statement.order_by(ComponentRecord.type, ComponentRecord.id)
        ).all()
        return [_component_from_record(record) for record in records]

    @app.get("/api/aircraft", response_model=list[AircraftLibraryItem])
    def list_aircraft(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[AircraftLibraryItem]:
        records = session.scalars(
            select(AircraftRecord)
            .where(AircraftRecord.owner_user_id == current_user.id)
            .order_by(
                AircraftRecord.updated_at.desc(),
                AircraftRecord.id.desc(),
            )
        ).all()
        return [_aircraft_library_item(record, session) for record in records]

    @app.get("/api/aircraft/templates", response_model=list[AircraftTemplate])
    def get_aircraft_templates() -> list[AircraftTemplate]:
        return template_definitions()

    @app.post(
        "/api/aircraft/from-template/{template_key}",
        response_model=AircraftLibraryItem,
        status_code=status.HTTP_201_CREATED,
    )
    def create_aircraft_from_template(
        template_key: str,
        command: AircraftCreateFromTemplate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AircraftLibraryItem:
        ensure_aircraft_capacity(session, current_user)
        template = template_by_key(template_key)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="飞机模板不存在",
            )

        aircraft = template.aircraft.model_copy(
            update={
                "id": None,
                "name": command.name or template.aircraft.name,
            }
        )
        record = AircraftRecord(owner_user_id=current_user.id)
        _update_aircraft_record(record, aircraft)
        _touch_new_aircraft(record, command.description)
        session.add(record)
        session.commit()
        session.refresh(record)
        return _aircraft_library_item(record, session)

    @app.post(
        "/api/aircraft/{aircraft_id}/duplicate",
        response_model=AircraftLibraryItem,
        status_code=status.HTTP_201_CREATED,
    )
    def duplicate_aircraft(
        aircraft_id: int,
        command: AircraftDuplicateRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AircraftLibraryItem:
        source = owned_aircraft_or_404(session, current_user, aircraft_id)
        ensure_aircraft_capacity(session, current_user)
        aircraft = _aircraft_from_record(source).model_copy(
            update={
                "id": None,
                "name": command.name or duplicate_name(source.name),
            }
        )
        record = AircraftRecord(owner_user_id=current_user.id)
        _update_aircraft_record(record, aircraft)
        _touch_new_aircraft(
            record,
            source.description or "",
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return _aircraft_library_item(record, session)

    @app.patch(
        "/api/aircraft/{aircraft_id}/metadata",
        response_model=AircraftLibraryItem,
    )
    def update_aircraft_metadata(
        aircraft_id: int,
        command: AircraftMetadataUpdate,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AircraftLibraryItem:
        record = owned_aircraft_or_404(session, current_user, aircraft_id)
        if command.name is not None:
            record.name = command.name.strip()
        if command.description is not None:
            record.description = command.description.strip()
        _touch_aircraft(record)
        session.commit()
        session.refresh(record)
        return _aircraft_library_item(record, session)

    @app.delete(
        "/api/aircraft/{aircraft_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
    )
    def delete_aircraft(
        aircraft_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> Response:
        record = owned_aircraft_or_404(session, current_user, aircraft_id)
        aircraft_count = owned_aircraft_count(session, current_user)
        if aircraft_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="至少保留一架飞机设计",
            )
        experiment_count = (
            session.scalar(
                select(func.count(SimulationRecord.id)).where(
                    SimulationRecord.aircraft_id == aircraft_id
                )
            )
            or 0
        )
        if experiment_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该飞机已有实验记录。为保证实验可追溯，不能删除；可以保留或复制后继续设计。",
            )
        session.delete(record)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/aircraft/{aircraft_id}", response_model=AssemblyState)
    def get_aircraft(
        aircraft_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AssemblyState:
        record = owned_aircraft_or_404(session, current_user, aircraft_id)
        return _assembly_state(_aircraft_from_record(record), session)

    @app.post(
        "/api/aircraft",
        response_model=AssemblyState,
        status_code=status.HTTP_201_CREATED,
    )
    def create_aircraft(
        aircraft: AircraftDefinition,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AssemblyState:
        ensure_aircraft_capacity(session, current_user)
        record = AircraftRecord(owner_user_id=current_user.id)
        _update_aircraft_record(record, aircraft)
        _touch_new_aircraft(record)
        session.add(record)
        session.commit()
        session.refresh(record)
        return _assembly_state(_aircraft_from_record(record), session)

    @app.put("/api/aircraft/{aircraft_id}", response_model=AssemblyState)
    def update_aircraft(
        aircraft_id: int,
        aircraft: AircraftDefinition,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AssemblyState:
        record = owned_aircraft_or_404(session, current_user, aircraft_id)
        _update_aircraft_record(record, aircraft)
        session.commit()
        session.refresh(record)
        return _assembly_state(_aircraft_from_record(record), session)

    @app.post(
        "/api/aircraft/{aircraft_id}/calculate",
        response_model=AssemblyState,
    )
    def calculate_aircraft(
        aircraft_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> AssemblyState:
        record = owned_aircraft_or_404(session, current_user, aircraft_id)
        return _assembly_state(_aircraft_from_record(record), session)

    def command_error(error: ValueError) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    @app.post(
        "/api/simulations",
        response_model=SimulationSnapshot,
        status_code=status.HTTP_201_CREATED,
    )
    def create_simulation(
        command: SimulationCreateRequest,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        record = owned_aircraft_or_404(
            session, current_user, command.aircraft_id
        )
        aircraft = _aircraft_from_record(record)
        catalog = _catalog(session)
        validation = augment_validation(
            aircraft,
            validate_configuration(aircraft, catalog),
        )
        if not validation.passed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="装配检查未通过，不能创建飞行仿真",
            )
        engineering = calculate_aircraft_engineering(aircraft, catalog).model_copy(
            update={"validation": validation}
        )
        simulation = simulation_manager.create(
            aircraft,
            catalog,
            engineering,
        )
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation.id)
        )

    @app.get(
        "/api/simulations/{simulation_id}",
        response_model=SimulationSnapshot,
    )
    def get_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/start",
        response_model=SimulationSnapshot,
    )
    async def start_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        simulation_manager.start(simulation_id)
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/pause",
        response_model=SimulationSnapshot,
    )
    def pause_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        simulation_manager.pause(simulation_id)
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/reset",
        response_model=SimulationSnapshot,
    )
    def reset_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        simulation_manager.reset(simulation_id)
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/stop",
        response_model=SimulationSnapshot,
    )
    def stop_simulation(
        simulation_id: int,
        request_session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, request_session, current_user)
        active_simulation = simulation_manager.stop(simulation_id)
        save_experiment(
            active_simulation,
            active_simulation.simulator.aircraft,
            request_session,
            telemetry_dir,
        )
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/arm",
        response_model=SimulationSnapshot,
    )
    def arm_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.arm(simulation_id)
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/takeoff",
        response_model=SimulationSnapshot,
    )
    def takeoff_simulation(
        simulation_id: int,
        command: TakeoffCommand,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.takeoff(simulation_id, command.altitude_m)
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/land",
        response_model=SimulationSnapshot,
    )
    def land_simulation(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.land(simulation_id)
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/wind",
        response_model=SimulationSnapshot,
    )
    def set_simulation_wind(
        simulation_id: int,
        command: WindCommand,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.set_wind(
                simulation_id,
                command.speed_mps,
                command.direction_deg,
            )
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/target",
        response_model=SimulationSnapshot,
    )
    def set_simulation_target(
        simulation_id: int,
        command: TargetCommand,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.set_target(
                simulation_id,
                command.x,
                command.y,
            )
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.post(
        "/api/simulations/{simulation_id}/waypoints",
        response_model=SimulationSnapshot,
    )
    def set_simulation_waypoints(
        simulation_id: int,
        command: WaypointCommand,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> SimulationSnapshot:
        manager_for_user_or_404(simulation_id, session, current_user)
        try:
            simulation_manager.set_waypoints(
                simulation_id,
                [
                    (waypoint.x, waypoint.y, waypoint.z)
                    for waypoint in command.waypoints
                ],
            )
        except ValueError as error:
            raise command_error(error) from error
        return SimulationSnapshot.model_validate(
            simulation_manager.snapshot(simulation_id)
        )

    @app.get(
        "/api/experiments",
        response_model=list[ExperimentSummary],
    )
    def get_experiments(
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> list[ExperimentSummary]:
        return list_experiments(session, owner_user_id=current_user.id)

    @app.get(
        "/api/experiments/{simulation_id}",
        response_model=ExperimentReplay,
    )
    def get_experiment(
        simulation_id: int,
        session: Session = Depends(get_db),
        current_user: UserRecord = Depends(get_current_user),
    ) -> ExperimentReplay:
        try:
            return load_replay(
                session,
                simulation_id,
                owner_user_id=current_user.id,
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验记录不存在",
            ) from error

    @app.websocket("/ws/simulations/{simulation_id}")
    async def simulation_websocket(
        websocket: WebSocket,
        simulation_id: int,
    ) -> None:
        with websocket.app.state.session_factory() as auth_session:
            current_user = session_user(
                auth_session,
                websocket.cookies.get(SESSION_COOKIE_NAME),
            )
            if current_user is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            try:
                manager_for_user_or_404(
                    simulation_id,
                    auth_session,
                    current_user,
                )
            except HTTPException:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

        await websocket.accept()
        try:
            while True:
                frame = simulation_manager.frame(simulation_id)
                await websocket.send_json(frame.model_dump(mode="json"))
                await asyncio.sleep(0.05)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
