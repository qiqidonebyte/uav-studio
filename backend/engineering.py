from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt

from pydantic import ValidationError

from backend.constants import (
    GRAVITY_MPS2,
    MOTOR_ORDER,
    SLOT_DISPLAY_NAMES,
    motor_positions_m,
)
from backend.schemas import (
    AircraftDefinition,
    AircraftEngineeringSummary,
    AssemblyIssue,
    AssemblyValidationResult,
    BatteryParameters,
    Component,
    ESCParameters,
    FrameParameters,
    InertiaEstimate,
    MotorParameters,
    MotorPerformanceProfile,
    PowerModuleParameters,
    PropellerParameters,
    ThrustCurvePoint,
    Vector3,
    parse_component_parameters,
)

REQUIRED_SLOTS = {
    "frame": ("frame_id", "frame"),
    "motor": ("motor_id", "motor"),
    "esc": ("esc_id", "esc"),
    "propeller": ("propeller_id", "propeller"),
    "battery": ("battery_id", "battery"),
    "power_module": ("power_module_id", "power_module"),
    "flight_controller": ("flight_controller_id", "flight_controller"),
}
OPTIONAL_SLOTS = {
    "gnss": ("gnss_id", "gnss"),
    "payload": ("payload_id", "payload"),
}

CG_OFFSET_WARNING_M = 0.02
LOW_THRUST_WEIGHT_RATIO = 1.5
SHORT_ENDURANCE_WARNING_MIN = 10.0
HIGH_PAYLOAD_MASS_FRACTION = 0.25
VOLTAGE_COMPARISON_TOLERANCE_V = 1e-6


class EngineeringInputError(ValueError):
    """Raised when a complete, calculable aircraft definition is required."""


class MissingPerformanceDataError(EngineeringInputError):
    """Raised when the selected motor/propeller/voltage combination is absent."""


@dataclass(frozen=True)
class MassPoint:
    name: str
    mass_kg: float
    position_m: Vector3


@dataclass(frozen=True)
class PerMotorPerformance:
    throttle: float
    thrust_n: float
    current_a: float
    power_w: float


@dataclass(frozen=True)
class RequiredComponents:
    components: dict[str, Component]
    parameters: dict[str, object]


def _issue(code: str, severity: str, message: str) -> AssemblyIssue:
    return AssemblyIssue(code=code, severity=severity, message=message)


def _get_component(
    catalog: dict[int, Component],
    component_id: int | None,
    expected_type: str,
    *,
    required: bool,
) -> Component | None:
    if component_id is None:
        if required:
            raise EngineeringInputError(f"missing required {expected_type} component")
        return None
    component = catalog.get(component_id)
    if component is None:
        raise EngineeringInputError(f"component id {component_id} was not found")
    if component.type != expected_type:
        raise EngineeringInputError(
            f"component id {component_id} is {component.type}, expected {expected_type}"
        )
    return component


def _load_required_components(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> RequiredComponents:
    components: dict[str, Component] = {}
    parameters: dict[str, object] = {}
    for slot, (field_name, component_type) in REQUIRED_SLOTS.items():
        component = _get_component(
            catalog,
            getattr(aircraft, field_name),
            component_type,
            required=True,
        )
        assert component is not None
        components[slot] = component
        parameters[slot] = parse_component_parameters(component)
    return RequiredComponents(components=components, parameters=parameters)


def build_mass_points(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> list[MassPoint]:
    required = _load_required_components(aircraft, catalog)
    frame_parameters = required.parameters["frame"]
    assert isinstance(frame_parameters, FrameParameters)

    motor_positions = motor_positions_m(frame_parameters.motor_diagonal_m)
    points = [
        MassPoint("frame", required.components["frame"].mass_kg, Vector3()),
    ]

    for motor_name in MOTOR_ORDER:
        position = motor_positions[motor_name]
        points.extend(
            [
                MassPoint(
                    f"{motor_name}_motor",
                    required.components["motor"].mass_kg,
                    position,
                ),
                MassPoint(
                    f"{motor_name}_esc",
                    required.components["esc"].mass_kg,
                    position,
                ),
                MassPoint(
                    f"{motor_name}_propeller",
                    required.components["propeller"].mass_kg,
                    position,
                ),
            ]
        )

    points.extend(
        [
            MassPoint(
                "battery",
                required.components["battery"].mass_kg,
                frame_parameters.battery_position_m,
            ),
            MassPoint(
                "power_module",
                required.components["power_module"].mass_kg,
                frame_parameters.power_module_position_m,
            ),
            MassPoint(
                "flight_controller",
                required.components["flight_controller"].mass_kg,
                frame_parameters.flight_controller_position_m,
            ),
        ]
    )

    gnss = _get_component(catalog, aircraft.gnss_id, "gnss", required=False)
    if gnss is not None:
        gnss_position = aircraft.gnss_position_m or frame_parameters.gnss_mount_position_m
        points.append(MassPoint("gnss", gnss.mass_kg, gnss_position))

    payload = _get_component(catalog, aircraft.payload_id, "payload", required=False)
    if payload is not None:
        if aircraft.payload_position_m is None:
            raise EngineeringInputError("payload is installed but payload_position_m is missing")
        points.append(MassPoint("payload", payload.mass_kg, aircraft.payload_position_m))

    return points


def calculate_total_mass(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    total_mass_kg = sum(point.mass_kg for point in build_mass_points(aircraft, catalog))
    if total_mass_kg <= 0.0:
        raise EngineeringInputError("total mass must be positive")
    return total_mass_kg


def calculate_center_of_gravity(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> Vector3:
    points = build_mass_points(aircraft, catalog)
    total_mass_kg = sum(point.mass_kg for point in points)
    return Vector3(
        x=sum(point.mass_kg * point.position_m.x for point in points) / total_mass_kg,
        y=sum(point.mass_kg * point.position_m.y for point in points) / total_mass_kg,
        z=sum(point.mass_kg * point.position_m.z for point in points) / total_mass_kg,
    )


def estimate_inertia(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> InertiaEstimate:
    points = build_mass_points(aircraft, catalog)
    return InertiaEstimate(
        ixx=sum(
            point.mass_kg
            * (point.position_m.y**2 + point.position_m.z**2)
            for point in points
        ),
        iyy=sum(
            point.mass_kg
            * (point.position_m.x**2 + point.position_m.z**2)
            for point in points
        ),
        izz=sum(
            point.mass_kg
            * (point.position_m.x**2 + point.position_m.y**2)
            for point in points
        ),
    )


def _linear_interpolate(
    x: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    if isclose(x1, x2, abs_tol=1e-12):
        return y1
    ratio = (x - x1) / (x2 - x1)
    return y1 + ratio * (y2 - y1)


def _validate_throttle(throttle: float) -> None:
    if not 0.0 <= throttle <= 1.0:
        raise EngineeringInputError("throttle must be within 0.0 and 1.0")


def _interpolate_profile_at_throttle(
    profile: MotorPerformanceProfile,
    throttle: float,
) -> ThrustCurvePoint:
    _validate_throttle(throttle)
    points = profile.points
    if isclose(throttle, 0.0, abs_tol=1e-12):
        return points[0]
    if isclose(throttle, 1.0, abs_tol=1e-12):
        return points[-1]

    for lower, upper in zip(points, points[1:]):
        if lower.throttle <= throttle <= upper.throttle:
            return ThrustCurvePoint(
                throttle=throttle,
                thrust_n=_linear_interpolate(
                    throttle,
                    lower.throttle,
                    lower.thrust_n,
                    upper.throttle,
                    upper.thrust_n,
                ),
                current_a=_linear_interpolate(
                    throttle,
                    lower.throttle,
                    lower.current_a,
                    upper.throttle,
                    upper.current_a,
                ),
                power_w=_linear_interpolate(
                    throttle,
                    lower.throttle,
                    lower.power_w,
                    upper.throttle,
                    upper.power_w,
                ),
            )
    raise MissingPerformanceDataError("throttle is outside the performance curve")


def _select_voltage_bracket(
    profiles: list[MotorPerformanceProfile],
    battery_voltage_v: float,
) -> tuple[MotorPerformanceProfile, MotorPerformanceProfile, float]:
    ordered = sorted(profiles, key=lambda profile: profile.battery_voltage_v)
    for profile in ordered:
        if isclose(
            profile.battery_voltage_v,
            battery_voltage_v,
            abs_tol=VOLTAGE_COMPARISON_TOLERANCE_V,
        ):
            return profile, profile, 0.0

    if battery_voltage_v < ordered[0].battery_voltage_v:
        raise MissingPerformanceDataError(
            f"no performance data below {ordered[0].battery_voltage_v:.2f} V"
        )
    if battery_voltage_v > ordered[-1].battery_voltage_v:
        raise MissingPerformanceDataError(
            f"no performance data above {ordered[-1].battery_voltage_v:.2f} V"
        )

    for lower, upper in zip(ordered, ordered[1:]):
        if lower.battery_voltage_v < battery_voltage_v < upper.battery_voltage_v:
            ratio = (battery_voltage_v - lower.battery_voltage_v) / (
                upper.battery_voltage_v - lower.battery_voltage_v
            )
            return lower, upper, ratio
    raise MissingPerformanceDataError("unable to bracket the requested battery voltage")


def interpolate_motor_performance(
    motor: Component,
    propeller_id: int,
    battery_voltage_v: float,
    throttle: float,
) -> ThrustCurvePoint:
    if motor.type != "motor":
        raise EngineeringInputError("motor performance requires a motor component")
    motor_parameters = parse_component_parameters(motor)
    assert isinstance(motor_parameters, MotorParameters)

    matching_profiles = [
        profile
        for profile in motor_parameters.profiles
        if profile.propeller_id == propeller_id
    ]
    if not matching_profiles:
        raise MissingPerformanceDataError(
            f"no performance curve for motor {motor.id} and propeller {propeller_id}"
        )

    lower, upper, ratio = _select_voltage_bracket(
        matching_profiles,
        battery_voltage_v,
    )
    lower_point = _interpolate_profile_at_throttle(lower, throttle)
    if lower is upper:
        return lower_point
    upper_point = _interpolate_profile_at_throttle(upper, throttle)
    return ThrustCurvePoint(
        throttle=throttle,
        thrust_n=_linear_interpolate(
            ratio,
            0.0,
            lower_point.thrust_n,
            1.0,
            upper_point.thrust_n,
        ),
        current_a=_linear_interpolate(
            ratio,
            0.0,
            lower_point.current_a,
            1.0,
            upper_point.current_a,
        ),
        power_w=_linear_interpolate(
            ratio,
            0.0,
            lower_point.power_w,
            1.0,
            upper_point.power_w,
        ),
    )


def interpolate_motor_performance_at_thrust(
    motor: Component,
    propeller_id: int,
    battery_voltage_v: float,
    required_thrust_n: float,
) -> PerMotorPerformance:
    maximum = interpolate_motor_performance(
        motor,
        propeller_id,
        battery_voltage_v,
        1.0,
    )
    if required_thrust_n < 0.0:
        raise EngineeringInputError("required thrust cannot be negative")
    if required_thrust_n > maximum.thrust_n:
        raise EngineeringInputError("requested thrust exceeds the available performance curve")
    if required_thrust_n == 0.0:
        return PerMotorPerformance(0.0, 0.0, 0.0, 0.0)

    low = 0.0
    high = 1.0
    for _ in range(64):
        middle = (low + high) / 2.0
        point = interpolate_motor_performance(
            motor,
            propeller_id,
            battery_voltage_v,
            middle,
        )
        if point.thrust_n < required_thrust_n:
            low = middle
        else:
            high = middle
    point = interpolate_motor_performance(
        motor,
        propeller_id,
        battery_voltage_v,
        (low + high) / 2.0,
    )
    return PerMotorPerformance(
        throttle=point.throttle,
        thrust_n=point.thrust_n,
        current_a=point.current_a,
        power_w=point.power_w,
    )


def _complete_motor_inputs(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> tuple[Component, Component, Component]:
    motor = _get_component(catalog, aircraft.motor_id, "motor", required=True)
    propeller = _get_component(
        catalog,
        aircraft.propeller_id,
        "propeller",
        required=True,
    )
    battery = _get_component(catalog, aircraft.battery_id, "battery", required=True)
    assert motor is not None and propeller is not None and battery is not None
    return motor, propeller, battery


def calculate_total_max_thrust(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)
    point = interpolate_motor_performance(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        1.0,
    )
    return 4.0 * point.thrust_n


def calculate_thrust_weight_ratio(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    total_mass_kg = calculate_total_mass(aircraft, catalog)
    return calculate_total_max_thrust(aircraft, catalog) / (
        total_mass_kg * GRAVITY_MPS2
    )


def estimate_hover_throttle(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    total_mass_kg = calculate_total_mass(aircraft, catalog)
    required_per_motor_n = total_mass_kg * GRAVITY_MPS2 / 4.0
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)
    return interpolate_motor_performance_at_thrust(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        required_per_motor_n,
    ).throttle


def calculate_max_power(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)
    point = interpolate_motor_performance(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        1.0,
    )
    return 4.0 * point.power_w


def calculate_max_current(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)
    point = interpolate_motor_performance(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        1.0,
    )
    return 4.0 * point.current_a


def estimate_hover_power(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    total_mass_kg = calculate_total_mass(aircraft, catalog)
    required_per_motor_n = total_mass_kg * GRAVITY_MPS2 / 4.0
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)
    point = interpolate_motor_performance_at_thrust(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        required_per_motor_n,
    )
    return 4.0 * point.power_w


def estimate_flight_time(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> float:
    battery = _get_component(catalog, aircraft.battery_id, "battery", required=True)
    assert battery is not None
    battery_parameters = parse_component_parameters(battery)
    assert isinstance(battery_parameters, BatteryParameters)

    usable_energy_wh = (
        battery_parameters.capacity_mah
        / 1000.0
        * battery_parameters.nominal_voltage_v
        * battery_parameters.usable_capacity_ratio
    )
    hover_power_w = estimate_hover_power(aircraft, catalog)
    if hover_power_w <= 0.0:
        raise EngineeringInputError("hover power must be positive")
    return usable_energy_wh / hover_power_w * 60.0


def _component_or_issue(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
    slot: str,
    field_name: str,
    expected_type: str,
    *,
    required: bool,
) -> Component | None:
    component_id = getattr(aircraft, field_name)
    if component_id is None:
        if required:
            raise EngineeringInputError(slot)
        return None
    component = catalog.get(component_id)
    if component is None:
        raise EngineeringInputError(f"{slot}:missing")
    if component.type != expected_type:
        raise EngineeringInputError(f"{slot}:type")
    return component


def _collect_components_for_validation(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> tuple[dict[str, Component], list[AssemblyIssue]]:
    components: dict[str, Component] = {}
    issues: list[AssemblyIssue] = []
    for slot, (field_name, expected_type) in REQUIRED_SLOTS.items():
        try:
            component = _component_or_issue(
                aircraft,
                catalog,
                slot,
                field_name,
                expected_type,
                required=True,
            )
        except EngineeringInputError as error:
            reason = str(error)
            code = (
                "COMPONENT_TYPE_MISMATCH"
                if reason.endswith(":type")
                else "REQUIRED_COMPONENT_MISSING"
            )
            issues.append(
                _issue(
                    code,
                    "error",
                    f"必需组件缺失或不可用：{SLOT_DISPLAY_NAMES.get(slot, slot)}",
                )
            )
            continue
        assert component is not None
        components[slot] = component

    for slot, (field_name, expected_type) in OPTIONAL_SLOTS.items():
        try:
            component = _component_or_issue(
                aircraft,
                catalog,
                slot,
                field_name,
                expected_type,
                required=False,
            )
        except EngineeringInputError:
            issues.append(
                _issue(
                    "COMPONENT_TYPE_MISMATCH",
                    "error",
                    f"可选组件类型错误：{SLOT_DISPLAY_NAMES.get(slot, slot)}",
                )
            )
            continue
        if component is not None:
            components[slot] = component
    return components, issues


def _parsed_parameters(
    components: dict[str, Component],
    issues: list[AssemblyIssue],
) -> dict[str, object]:
    parameters: dict[str, object] = {}
    for slot, component in components.items():
        try:
            parameters[slot] = parse_component_parameters(component)
        except ValidationError:
            issues.append(
                _issue(
                    "INVALID_COMPONENT_PARAMETERS",
                    "error",
                    f"组件参数无效：{SLOT_DISPLAY_NAMES.get(slot, slot)}",
                )
            )
    return parameters


def _validate_voltage_compatibility(
    battery: BatteryParameters,
    esc: ESCParameters,
    power_module: PowerModuleParameters,
) -> list[AssemblyIssue]:
    issues: list[AssemblyIssue] = []
    for name, minimum_v, maximum_v in (
        ("电调", esc.voltage_min_v, esc.voltage_max_v),
        ("电源模块", power_module.voltage_min_v, power_module.voltage_max_v),
    ):
        if (
            battery.voltage_min_v < minimum_v - VOLTAGE_COMPARISON_TOLERANCE_V
            or battery.voltage_max_v > maximum_v + VOLTAGE_COMPARISON_TOLERANCE_V
        ):
            issues.append(
                _issue(
                    "VOLTAGE_INCOMPATIBLE",
                    "error",
                    f"电池电压范围与{name}不兼容",
                )
            )
    return issues


def validate_configuration(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> AssemblyValidationResult:
    components, blocking_errors = _collect_components_for_validation(
        aircraft,
        catalog,
    )
    parameters = _parsed_parameters(components, blocking_errors)
    warnings: list[AssemblyIssue] = []

    motor_parameters = parameters.get("motor")
    esc_parameters = parameters.get("esc")
    propeller_parameters = parameters.get("propeller")
    battery_parameters = parameters.get("battery")
    power_module_parameters = parameters.get("power_module")

    if isinstance(propeller_parameters, PropellerParameters):
        if propeller_parameters.direction != "PAIR":
            blocking_errors.append(
                _issue(
                    "PROPELLER_DIRECTION_MISMATCH",
                    "error",
                    "螺旋桨方向未匹配 M1-M4 的 CW/CCW 要求",
                )
            )

    if (
        isinstance(battery_parameters, BatteryParameters)
        and isinstance(esc_parameters, ESCParameters)
        and isinstance(power_module_parameters, PowerModuleParameters)
    ):
        blocking_errors.extend(
            _validate_voltage_compatibility(
                battery_parameters,
                esc_parameters,
                power_module_parameters,
            )
        )

    total_mass_kg: float | None = None
    if not any(
        issue.code in {"REQUIRED_COMPONENT_MISSING", "COMPONENT_TYPE_MISMATCH"}
        for issue in blocking_errors
    ):
        try:
            total_mass_kg = sum(
                point.mass_kg for point in build_mass_points(aircraft, catalog)
            )
            cg = calculate_center_of_gravity(aircraft, catalog)
            if sqrt(cg.x**2 + cg.y**2) > CG_OFFSET_WARNING_M:
                warnings.append(
                    _issue(
                        "CG_OFFSET_WARNING",
                        "warning",
                        "重心水平偏移较大，建议调整组件安装位置",
                    )
                )
        except EngineeringInputError:
            blocking_errors.append(
                _issue(
                    "INVALID_COMPONENT_PARAMETERS",
                    "error",
                    "无法根据当前组件位置计算质量、重心或惯量",
                )
            )

    max_motor_point: ThrustCurvePoint | None = None
    if (
        isinstance(motor_parameters, MotorParameters)
        and isinstance(battery_parameters, BatteryParameters)
        and isinstance(esc_parameters, ESCParameters)
        and isinstance(power_module_parameters, PowerModuleParameters)
        and aircraft.propeller_id is not None
        and "motor" in components
        and "battery" in components
    ):
        try:
            max_motor_point = interpolate_motor_performance(
                components["motor"],
                aircraft.propeller_id,
                battery_parameters.nominal_voltage_v,
                1.0,
            )
        except MissingPerformanceDataError:
            blocking_errors.append(
                _issue(
                    "MOTOR_PERFORMANCE_CURVE_MISSING",
                    "error",
                    "当前电机、螺旋桨和电池电压组合没有可用的推力性能曲线",
                )
            )
        else:
            total_max_thrust_n = 4.0 * max_motor_point.thrust_n
            total_max_current_a = 4.0 * max_motor_point.current_a
            aircraft_weight_n = (
                total_mass_kg * GRAVITY_MPS2
                if total_mass_kg is not None
                else None
            )

            if aircraft_weight_n is not None:
                if total_max_thrust_n < aircraft_weight_n:
                    blocking_errors.append(
                        _issue(
                            "INSUFFICIENT_TOTAL_THRUST",
                            "error",
                            "最大总推力不足以支撑整机重量",
                        )
                    )
                elif total_max_thrust_n / aircraft_weight_n < LOW_THRUST_WEIGHT_RATIO:
                    warnings.append(
                        _issue(
                            "LOW_THRUST_WEIGHT_RATIO",
                            "warning",
                            "推重比低于 1.5，试飞能力有限",
                        )
                    )

            if max_motor_point.current_a > esc_parameters.max_current_a + 1e-9:
                blocking_errors.append(
                    _issue(
                        "ESC_CURRENT_LIMIT_EXCEEDED",
                        "error",
                        "电机最大电流超过电调持续电流能力",
                    )
                )
            if (
                total_max_current_a
                > battery_parameters.max_continuous_current_a + 1e-9
            ):
                blocking_errors.append(
                    _issue(
                        "BATTERY_DISCHARGE_LIMIT_EXCEEDED",
                        "error",
                        "整机最大电流超过电池持续放电能力",
                    )
                )
            if total_max_current_a > power_module_parameters.max_current_a + 1e-9:
                blocking_errors.append(
                    _issue(
                        "POWER_MODULE_CURRENT_LIMIT_EXCEEDED",
                        "error",
                        "整机最大电流超过电源模块能力",
                    )
                )

    if total_mass_kg is not None:
        payload = components.get("payload")
        if payload is not None:
            payload_fraction = payload.mass_kg / total_mass_kg
            if payload_fraction > HIGH_PAYLOAD_MASS_FRACTION:
                warnings.append(
                    _issue(
                        "HIGH_PAYLOAD_MASS_FRACTION",
                        "warning",
                        "载荷质量占整机比例偏高",
                    )
                )

    if not any(
        issue.code
        in {
            "REQUIRED_COMPONENT_MISSING",
            "COMPONENT_TYPE_MISMATCH",
            "INVALID_COMPONENT_PARAMETERS",
            "MOTOR_PERFORMANCE_CURVE_MISSING",
            "INSUFFICIENT_TOTAL_THRUST",
        }
        for issue in blocking_errors
    ):
        try:
            endurance_min = estimate_flight_time(aircraft, catalog)
            if endurance_min < SHORT_ENDURANCE_WARNING_MIN:
                warnings.append(
                    _issue(
                        "SHORT_ESTIMATED_ENDURANCE",
                        "warning",
                        "预计续航不足 10 分钟",
                    )
                )
        except EngineeringInputError:
            pass

    return AssemblyValidationResult(
        blocking_errors=blocking_errors,
        warnings=warnings,
    )


def calculate_aircraft_engineering(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> AircraftEngineeringSummary:
    total_mass_kg = calculate_total_mass(aircraft, catalog)
    cg = calculate_center_of_gravity(aircraft, catalog)
    inertia = estimate_inertia(aircraft, catalog)
    motor, propeller, battery = _complete_motor_inputs(aircraft, catalog)
    battery_parameters = parse_component_parameters(battery)
    esc_parameters = parse_component_parameters(
        _get_component(catalog, aircraft.esc_id, "esc", required=True)
    )
    power_module_parameters = parse_component_parameters(
        _get_component(
            catalog,
            aircraft.power_module_id,
            "power_module",
            required=True,
        )
    )
    assert isinstance(battery_parameters, BatteryParameters)
    assert isinstance(esc_parameters, ESCParameters)
    assert isinstance(power_module_parameters, PowerModuleParameters)

    max_motor_point = interpolate_motor_performance(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        1.0,
    )
    required_hover_thrust_n = total_mass_kg * GRAVITY_MPS2 / 4.0
    hover_motor = interpolate_motor_performance_at_thrust(
        motor,
        propeller.id,
        battery_parameters.nominal_voltage_v,
        required_hover_thrust_n,
    )
    max_total_thrust_n = 4.0 * max_motor_point.thrust_n
    max_current_a = 4.0 * max_motor_point.current_a
    max_power_w = 4.0 * max_motor_point.power_w
    hover_current_a = 4.0 * hover_motor.current_a
    hover_power_w = 4.0 * hover_motor.power_w
    all_components, _ = _collect_components_for_validation(aircraft, catalog)
    payload = all_components.get("payload")
    payload_mass_fraction = (
        payload.mass_kg / total_mass_kg if payload is not None else 0.0
    )

    usable_energy_wh = (
        battery_parameters.capacity_mah
        / 1000.0
        * battery_parameters.nominal_voltage_v
        * battery_parameters.usable_capacity_ratio
    )
    estimated_flight_time_min = usable_energy_wh / hover_power_w * 60.0

    return AircraftEngineeringSummary(
        total_mass_kg=total_mass_kg,
        center_of_gravity_m=cg,
        inertia_kg_m2=inertia,
        max_thrust_per_motor_n=max_motor_point.thrust_n,
        max_total_thrust_n=max_total_thrust_n,
        thrust_weight_ratio=max_total_thrust_n
        / (total_mass_kg * GRAVITY_MPS2),
        hover_throttle=hover_motor.throttle,
        hover_thrust_per_motor_n=required_hover_thrust_n,
        hover_current_a=hover_current_a,
        max_current_a=max_current_a,
        hover_power_w=hover_power_w,
        max_power_w=max_power_w,
        battery_continuous_margin_a=(
            battery_parameters.max_continuous_current_a - max_current_a
        ),
        esc_current_margin_a=esc_parameters.max_current_a
        - max_motor_point.current_a,
        power_module_current_margin_a=(
            power_module_parameters.max_current_a - max_current_a
        ),
        payload_mass_fraction=payload_mass_fraction,
        estimated_flight_time_min=estimated_flight_time_min,
        validation=validate_configuration(aircraft, catalog),
    )
