from __future__ import annotations

from datetime import datetime
from typing import Annotated, Iterable, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)

ComponentType = Literal[
    "frame",
    "motor",
    "esc",
    "propeller",
    "battery",
    "power_module",
    "flight_controller",
    "gnss",
    "payload",
]
PropellerDirection = Literal["CW", "CCW", "PAIR"]
FlightMode = Literal["IDLE", "ARMED", "TAKING_OFF", "HOVERING", "LANDING"]
SimulationStatus = Literal["STOPPED", "RUNNING", "PAUSED"]
ExperimentStatus = Literal["COMPLETED", "STOPPED"]

MODEL_CONFIG = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Vector3(BaseModel):
    model_config = MODEL_CONFIG

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Attitude(BaseModel):
    model_config = MODEL_CONFIG

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class AngularVelocity(BaseModel):
    model_config = MODEL_CONFIG

    p: float = 0.0
    q: float = 0.0
    r: float = 0.0


class MotorTelemetry(BaseModel):
    model_config = MODEL_CONFIG

    outputs: Annotated[list[float], Field(min_length=4, max_length=4)]
    thrusts_n: Annotated[list[float], Field(min_length=4, max_length=4)]


class ForcesTelemetry(BaseModel):
    model_config = MODEL_CONFIG

    gravity_n: float
    total_thrust_n: float


class WindTelemetry(BaseModel):
    model_config = MODEL_CONFIG

    speed_mps: float = Field(ge=0.0)
    direction_deg: float


class PowerTelemetry(BaseModel):
    model_config = MODEL_CONFIG

    estimated_power_w: float = Field(ge=0.0)
    battery_remaining: float = Field(ge=0.0, le=1.0)
    voltage_v: float = Field(ge=0.0)
    current_a: float = Field(ge=0.0)


class ThrustCurvePoint(BaseModel):
    model_config = MODEL_CONFIG

    throttle: float = Field(ge=0.0, le=1.0)
    thrust_n: float = Field(ge=0.0)
    current_a: float = Field(ge=0.0)
    power_w: float = Field(ge=0.0)


class MotorPerformanceProfile(BaseModel):
    model_config = MODEL_CONFIG

    battery_voltage_v: float = Field(gt=0.0)
    propeller_id: int = Field(gt=0)
    points: Annotated[list[ThrustCurvePoint], Field(min_length=2)]
    source: str = "Educational Sample Data"

    @model_validator(mode="after")
    def validate_curve(self) -> "MotorPerformanceProfile":
        throttles = [point.throttle for point in self.points]
        if throttles != sorted(throttles) or len(throttles) != len(set(throttles)):
            raise ValueError("performance curve throttles must be strictly increasing")
        if throttles[0] != 0.0 or throttles[-1] != 1.0:
            raise ValueError("performance curve must include throttle 0.0 and 1.0")
        return self


class MotorParameters(BaseModel):
    model_config = MODEL_CONFIG

    kv: float = Field(gt=0.0)
    profiles: Annotated[list[MotorPerformanceProfile], Field(min_length=1)]


class FrameParameters(BaseModel):
    model_config = MODEL_CONFIG

    motor_diagonal_m: float = Field(gt=0.0)
    battery_position_m: Vector3 = Field(default_factory=Vector3)
    power_module_position_m: Vector3 = Field(default_factory=Vector3)
    flight_controller_position_m: Vector3 = Field(default_factory=Vector3)
    gnss_mount_position_m: Vector3 = Field(default_factory=Vector3)
    # P0 Sprint 1 only formalizes the field. Engineering + simulator migration to
    # one shared mount-point source is intentionally left for the next sprint.
    mount_points: dict[str, Vector3] = Field(default_factory=dict)


class ESCParameters(BaseModel):
    model_config = MODEL_CONFIG

    max_current_a: float = Field(gt=0.0)
    voltage_min_v: float = Field(gt=0.0)
    voltage_max_v: float = Field(gt=0.0)

    @model_validator(mode="after")
    def validate_voltage_range(self) -> "ESCParameters":
        if self.voltage_min_v >= self.voltage_max_v:
            raise ValueError("ESC voltage_min_v must be lower than voltage_max_v")
        return self


class PropellerParameters(BaseModel):
    model_config = MODEL_CONFIG

    diameter_in: float = Field(gt=0.0)
    pitch_in: float = Field(gt=0.0)
    direction: PropellerDirection


class BatteryParameters(BaseModel):
    model_config = MODEL_CONFIG

    cell_count: int = Field(gt=0)
    capacity_mah: float = Field(gt=0.0)
    nominal_voltage_v: float = Field(gt=0.0)
    voltage_min_v: float = Field(gt=0.0)
    voltage_max_v: float = Field(gt=0.0)
    max_continuous_current_a: float = Field(gt=0.0)
    usable_capacity_ratio: float = Field(default=0.8, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_voltage_range(self) -> "BatteryParameters":
        if self.voltage_min_v >= self.nominal_voltage_v:
            raise ValueError("battery voltage_min_v must be lower than nominal_voltage_v")
        if self.nominal_voltage_v >= self.voltage_max_v:
            raise ValueError("battery nominal_voltage_v must be lower than voltage_max_v")
        return self


class PowerModuleParameters(BaseModel):
    model_config = MODEL_CONFIG

    max_current_a: float = Field(gt=0.0)
    voltage_min_v: float = Field(gt=0.0)
    voltage_max_v: float = Field(gt=0.0)

    @model_validator(mode="after")
    def validate_voltage_range(self) -> "PowerModuleParameters":
        if self.voltage_min_v >= self.voltage_max_v:
            raise ValueError("power module voltage_min_v must be lower than voltage_max_v")
        return self


class VoltageRangeParameters(BaseModel):
    model_config = MODEL_CONFIG

    voltage_min_v: float = Field(gt=0.0)
    voltage_max_v: float = Field(gt=0.0)

    @model_validator(mode="after")
    def validate_voltage_range(self) -> "VoltageRangeParameters":
        if self.voltage_min_v >= self.voltage_max_v:
            raise ValueError("voltage_min_v must be lower than voltage_max_v")
        return self


class PayloadParameters(BaseModel):
    model_config = MODEL_CONFIG

    mount: Literal["front", "bottom_center"] = "bottom_center"


class ComponentVisual(BaseModel):
    """Pure presentation metadata for one engineering component.

    File names are generated from the checked-in 3D asset manifest.  Physics
    code must never read these values.
    """

    model_config = MODEL_CONFIG

    asset_key: str = Field(min_length=1)
    file: str | None = None
    cw_file: str | None = None
    ccw_file: str | None = None
    thumbnail: str | None = None
    scale: float = Field(default=1.0, gt=0.0)

    @model_validator(mode="after")
    def validate_model_reference(self) -> "ComponentVisual":
        if self.file is None and (self.cw_file is None or self.ccw_file is None):
            raise ValueError("component visual must define file or both cw_file/ccw_file")
        return self


class Component(BaseModel):
    model_config = MODEL_CONFIG

    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    type: ComponentType
    mass_kg: float = Field(gt=0.0)
    parameters_json: dict = Field(default_factory=dict)
    visual: ComponentVisual | None = None

    @field_serializer("parameters_json")
    def serialize_engineering_parameters(self, value: dict) -> dict:
        # `_visual` is an internal persistence detail; API clients receive the
        # first-class `visual` field instead of a duplicated nested copy.
        return {key: item for key, item in value.items() if key != "_visual"}

    @model_validator(mode="before")
    @classmethod
    def derive_visual_from_persisted_parameters(cls, data):
        """Backwards-compatible storage without a SQLite schema migration.

        Existing databases already have a JSON parameters column.  Visual
        metadata is persisted under the reserved `_visual` key, then exposed as
        a first-class `Component.visual` field at the API boundary.
        """

        if not isinstance(data, dict) or data.get("visual") is not None:
            return data
        parameters = data.get("parameters_json")
        if not isinstance(parameters, dict):
            return data
        raw_visual = parameters.get("_visual")
        if not isinstance(raw_visual, dict):
            return data
        next_data = dict(data)
        next_data["visual"] = raw_visual
        return next_data


class AircraftDefinition(BaseModel):
    model_config = MODEL_CONFIG

    id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1)
    frame_id: int | None = Field(default=None, gt=0)
    motor_id: int | None = Field(default=None, gt=0)
    esc_id: int | None = Field(default=None, gt=0)
    propeller_id: int | None = Field(default=None, gt=0)
    battery_id: int | None = Field(default=None, gt=0)
    power_module_id: int | None = Field(default=None, gt=0)
    flight_controller_id: int | None = Field(default=None, gt=0)
    gnss_id: int | None = Field(default=None, gt=0)
    payload_id: int | None = Field(default=None, gt=0)
    gnss_position_m: Vector3 | None = None
    payload_position_m: Vector3 | None = None


class AssemblyIssue(BaseModel):
    model_config = MODEL_CONFIG

    code: str = Field(min_length=1)
    severity: Literal["error", "warning"]
    message: str = Field(min_length=1)


class AssemblyValidationResult(BaseModel):
    model_config = MODEL_CONFIG

    blocking_errors: list[AssemblyIssue] = Field(default_factory=list)
    warnings: list[AssemblyIssue] = Field(default_factory=list)

    @computed_field
    @property
    def passed(self) -> bool:
        return not self.blocking_errors


class InertiaEstimate(BaseModel):
    model_config = MODEL_CONFIG

    ixx: float = Field(ge=0.0)
    iyy: float = Field(ge=0.0)
    izz: float = Field(ge=0.0)


class AircraftEngineeringSummary(BaseModel):
    model_config = MODEL_CONFIG

    total_mass_kg: float = Field(gt=0.0)
    center_of_gravity_m: Vector3
    inertia_kg_m2: InertiaEstimate
    max_thrust_per_motor_n: float = Field(ge=0.0)
    max_total_thrust_n: float = Field(ge=0.0)
    thrust_weight_ratio: float = Field(ge=0.0)
    hover_throttle: float = Field(ge=0.0, le=1.0)
    hover_thrust_per_motor_n: float = Field(ge=0.0)
    hover_current_a: float = Field(ge=0.0)
    max_current_a: float = Field(ge=0.0)
    hover_power_w: float = Field(ge=0.0)
    max_power_w: float = Field(ge=0.0)
    battery_continuous_margin_a: float
    esc_current_margin_a: float
    power_module_current_margin_a: float
    payload_mass_fraction: float = Field(ge=0.0, le=1.0)
    estimated_flight_time_min: float = Field(ge=0.0)
    validation: AssemblyValidationResult
    estimation_note: Literal["Educational Estimation"] = "Educational Estimation"


class AssemblyState(BaseModel):
    model_config = MODEL_CONFIG

    aircraft: AircraftDefinition
    engineering: AircraftEngineeringSummary | None
    validation: AssemblyValidationResult


class TelemetryFrame(BaseModel):
    model_config = MODEL_CONFIG

    t: float = Field(ge=0.0)
    position: Vector3
    velocity: Vector3
    attitude: Attitude
    angular_velocity: AngularVelocity
    center_of_gravity: Vector3
    motors: MotorTelemetry
    forces: ForcesTelemetry
    wind: WindTelemetry
    power: PowerTelemetry
    armed: bool
    flight_mode: FlightMode


class SimulationCreateRequest(BaseModel):
    model_config = MODEL_CONFIG

    aircraft_id: int = Field(gt=0)


class TakeoffCommand(BaseModel):
    model_config = MODEL_CONFIG

    altitude_m: float = Field(gt=0.0, le=120.0)


class WindCommand(BaseModel):
    model_config = MODEL_CONFIG

    speed_mps: float = Field(ge=0.0, le=30.0)
    direction_deg: float


class TargetCommand(BaseModel):
    model_config = MODEL_CONFIG

    x: float
    y: float


class WaypointCommand(BaseModel):
    model_config = MODEL_CONFIG

    waypoints: list[Vector3] = Field(max_length=20)


class SimulationSnapshot(BaseModel):
    model_config = MODEL_CONFIG

    id: int = Field(gt=0)
    status: SimulationStatus
    telemetry: TelemetryFrame
    target_position: Vector3
    waypoints: list[Vector3]
    boundary_m: float = Field(gt=0.0)


class ExperimentSummary(BaseModel):
    model_config = MODEL_CONFIG

    id: int = Field(gt=0)
    aircraft_id: int = Field(gt=0)
    aircraft_name: str = Field(min_length=1)
    started_at: datetime
    ended_at: datetime
    duration_s: float = Field(ge=0.0)
    max_altitude_m: float = Field(ge=0.0)
    status: ExperimentStatus
    frame_count: int = Field(ge=0)


class ExperimentReplay(BaseModel):
    model_config = MODEL_CONFIG

    experiment: ExperimentSummary
    aircraft: AircraftDefinition
    components: list[Component]
    frames: list[TelemetryFrame]
    target_position: Vector3
    waypoints: list[Vector3]
    boundary_m: float = Field(gt=0.0)


def parse_component_parameters(
    component: Component,
) -> (
    FrameParameters
    | MotorParameters
    | ESCParameters
    | PropellerParameters
    | BatteryParameters
    | PowerModuleParameters
    | VoltageRangeParameters
    | PayloadParameters
):
    parser_by_type = {
        "frame": FrameParameters,
        "motor": MotorParameters,
        "esc": ESCParameters,
        "propeller": PropellerParameters,
        "battery": BatteryParameters,
        "power_module": PowerModuleParameters,
        "flight_controller": VoltageRangeParameters,
        "gnss": VoltageRangeParameters,
        "payload": PayloadParameters,
    }
    # `_visual` is a reserved storage key and is not an engineering input.
    engineering_parameters = {
        key: value
        for key, value in component.parameters_json.items()
        if key != "_visual"
    }
    return parser_by_type[component.type].model_validate(engineering_parameters)


def catalog_values(catalog: dict[int, Component] | Iterable[Component]) -> Iterable[Component]:
    if isinstance(catalog, dict):
        return catalog.values()
    return catalog
