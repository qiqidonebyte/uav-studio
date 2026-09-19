from __future__ import annotations

from dataclasses import dataclass
from math import cos, exp, radians, sin

import numpy as np

from backend.constants import (
    FLIGHT_BOUNDARY_M,
    GRAVITY_MPS2,
    MOTOR_ORDER,
    motor_positions_m,
)
from backend.engineering import (
    interpolate_motor_performance,
    interpolate_motor_performance_at_thrust,
)
from backend.pid import PID
from backend.schemas import (
    AircraftDefinition,
    AircraftEngineeringSummary,
    AngularVelocity,
    Attitude,
    BatteryParameters,
    Component,
    ForcesTelemetry,
    FrameParameters,
    MotorParameters,
    MotorTelemetry,
    PowerTelemetry,
    PropellerParameters,
    TelemetryFrame,
    Vector3,
    WindTelemetry,
    parse_component_parameters,
)


@dataclass(frozen=True)
class SimulatorConfig:
    dt: float = 0.02
    drag_coefficient: float = 0.12
    max_tilt_rad: float = radians(15.0)
    altitude_accel_limit: float = 4.5
    position_accel_limit: float = 3.0
    attitude_accel_limit: float = 18.0
    yaw_accel_limit: float = 4.0
    motor_mix_gain: float = 0.22
    yaw_mix_gain: float = 0.10
    angular_damping: float = 0.35
    yaw_torque_coefficient_m: float = 0.018


class SimpleSimulator:
    def __init__(
        self,
        aircraft: AircraftDefinition,
        catalog: dict[int, Component],
        engineering: AircraftEngineeringSummary,
        *,
        config: SimulatorConfig | None = None,
    ) -> None:
        if not engineering.validation.passed:
            raise ValueError("aircraft must pass assembly validation before simulation")

        self.aircraft = aircraft
        self.catalog = catalog
        self.engineering = engineering
        self.config = config or SimulatorConfig()
        self.dt = self.config.dt

        self.motor = self._component(aircraft.motor_id, "motor")
        self.propeller = self._component(aircraft.propeller_id, "propeller")
        self.battery = self._component(aircraft.battery_id, "battery")
        self.frame = self._component(aircraft.frame_id, "frame")

        motor_parameters = parse_component_parameters(self.motor)
        propeller_parameters = parse_component_parameters(self.propeller)
        battery_parameters = parse_component_parameters(self.battery)
        frame_parameters = parse_component_parameters(self.frame)
        assert isinstance(motor_parameters, MotorParameters)
        assert isinstance(propeller_parameters, PropellerParameters)
        assert isinstance(battery_parameters, BatteryParameters)
        assert isinstance(frame_parameters, FrameParameters)
        self.motor_parameters = motor_parameters
        self.propeller_parameters = propeller_parameters
        self.battery_parameters = battery_parameters
        self.frame_parameters = frame_parameters

        positions = motor_positions_m(frame_parameters.motor_diagonal_m)
        self.motor_positions = {
            name: np.array(
                [positions[name].x, positions[name].y, positions[name].z],
                dtype=float,
            )
            for name in MOTOR_ORDER
        }
        self.inertia = np.array(
            [
                engineering.inertia_kg_m2.ixx,
                engineering.inertia_kg_m2.iyy,
                engineering.inertia_kg_m2.izz,
            ],
            dtype=float,
        )
        self.inertia = np.maximum(self.inertia, 1e-6)
        self.battery_energy_wh = (
            battery_parameters.capacity_mah / 1000.0
            * battery_parameters.nominal_voltage_v
        )

        self._altitude_pid = PID(
            kp=0.95,
            ki=0.05,
            kd=1.15,
            output_min=-self.config.altitude_accel_limit,
            output_max=self.config.altitude_accel_limit,
            integral_min=-1.0,
            integral_max=1.0,
        )
        self._position_x_pid = PID(
            kp=0.55,
            ki=0.08,
            kd=0.90,
            output_min=-self.config.position_accel_limit,
            output_max=self.config.position_accel_limit,
            integral_min=-0.8,
            integral_max=0.8,
        )
        self._position_y_pid = PID(
            kp=0.55,
            ki=0.08,
            kd=0.90,
            output_min=-self.config.position_accel_limit,
            output_max=self.config.position_accel_limit,
            integral_min=-0.8,
            integral_max=0.8,
        )
        self._roll_pid = PID(
            kp=10.0,
            ki=0.0,
            kd=4.2,
            output_min=-self.config.attitude_accel_limit,
            output_max=self.config.attitude_accel_limit,
            integral_min=-1.0,
            integral_max=1.0,
        )
        self._pitch_pid = PID(
            kp=10.0,
            ki=0.0,
            kd=4.2,
            output_min=-self.config.attitude_accel_limit,
            output_max=self.config.attitude_accel_limit,
            integral_min=-1.0,
            integral_max=1.0,
        )
        self._yaw_pid = PID(
            kp=2.5,
            ki=0.0,
            kd=1.2,
            output_min=-self.config.yaw_accel_limit,
            output_max=self.config.yaw_accel_limit,
            integral_min=-1.0,
            integral_max=1.0,
        )

        self.reset()

    def _component(self, component_id: int | None, component_type: str) -> Component:
        if component_id is None:
            raise ValueError(f"missing required {component_type} component")
        component = self.catalog.get(component_id)
        if component is None or component.type != component_type:
            raise ValueError(f"invalid {component_type} component")
        return component

    @property
    def running(self) -> bool:
        return self._running

    @property
    def armed(self) -> bool:
        return self._armed

    @property
    def flight_mode(self) -> str:
        return self._flight_mode

    @property
    def target_position(self) -> np.ndarray:
        return self._target_position.copy()

    @property
    def target_altitude(self) -> float:
        return self._target_altitude

    def reset(self) -> TelemetryFrame:
        self._running = False
        self._t = 0.0
        self._position = np.zeros(3, dtype=float)
        self._velocity = np.zeros(3, dtype=float)
        self._attitude = np.zeros(3, dtype=float)
        self._angular_velocity = np.zeros(3, dtype=float)
        self._motor_outputs = np.zeros(4, dtype=float)
        self._motor_thrusts = np.zeros(4, dtype=float)
        self._battery_remaining = 1.0
        self._estimated_power_w = 0.0
        self._current_a = 0.0
        self._armed = False
        self._flight_mode = "IDLE"
        self._target_position = np.zeros(3, dtype=float)
        self._target_altitude = 0.0
        self._wind_velocity = np.zeros(3, dtype=float)
        self._wind_speed = 0.0
        self._wind_direction = 0.0
        self._hover_counter = 0
        for pid in self._all_pids():
            pid.reset()
        return self.telemetry_frame()

    def start(self) -> TelemetryFrame:
        self._running = True
        return self.telemetry_frame()

    def pause(self) -> TelemetryFrame:
        self._running = False
        return self.telemetry_frame()

    def stop(self) -> TelemetryFrame:
        return self.reset()

    def arm(self) -> TelemetryFrame:
        if not self._running:
            raise ValueError("simulator must be running before arm")
        if self._flight_mode == "IDLE":
            self._armed = True
            self._flight_mode = "ARMED"
        return self.telemetry_frame()

    def takeoff(self, target_altitude_m: float) -> TelemetryFrame:
        if not self._armed:
            raise ValueError("aircraft must be armed before takeoff")
        if target_altitude_m <= 0.0:
            raise ValueError("target altitude must be positive")
        self._target_altitude = float(target_altitude_m)
        self._target_position[2] = self._target_altitude
        self._flight_mode = "TAKING_OFF"
        self._hover_counter = 0
        for pid in (
            self._altitude_pid,
            self._position_x_pid,
            self._position_y_pid,
            self._roll_pid,
            self._pitch_pid,
            self._yaw_pid,
        ):
            pid.reset()
        return self.telemetry_frame()

    def set_target_position(self, x_m: float, y_m: float) -> TelemetryFrame:
        if not self._armed:
            raise ValueError("aircraft must be armed before setting a target")
        if (
            abs(x_m) > FLIGHT_BOUNDARY_M
            or abs(y_m) > FLIGHT_BOUNDARY_M
        ):
            raise ValueError("target position is outside the flight boundary")
        self._target_position[0] = float(x_m)
        self._target_position[1] = float(y_m)
        return self.telemetry_frame()

    def land(self) -> TelemetryFrame:
        if not self._armed:
            raise ValueError("aircraft must be armed before landing")
        self._target_altitude = 0.0
        self._target_position[:2] = self._position[:2]
        self._flight_mode = "LANDING"
        self._hover_counter = 0
        return self.telemetry_frame()

    def set_wind(self, speed_mps: float, direction_deg: float) -> TelemetryFrame:
        if speed_mps < 0.0:
            raise ValueError("wind speed cannot be negative")
        self._wind_speed = float(speed_mps)
        self._wind_direction = float(direction_deg) % 360.0
        direction_rad = radians(self._wind_direction)
        self._wind_velocity = np.array(
            [
                self._wind_speed * cos(direction_rad),
                self._wind_speed * sin(direction_rad),
                0.0,
            ],
            dtype=float,
        )
        return self.telemetry_frame()

    def step(self, dt: float | None = None) -> TelemetryFrame:
        if not self._running:
            return self.telemetry_frame()
        dt = self.dt if dt is None else float(dt)
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        if self._flight_mode in {"TAKING_OFF", "HOVERING", "LANDING"}:
            outputs = self._control(dt)
            if self._battery_remaining <= 0.0:
                outputs = np.zeros(4, dtype=float)
            thrusts, power_w, current_a = self._propulsion(outputs)
            self._motor_outputs = outputs
            self._motor_thrusts = thrusts
            self._estimated_power_w = power_w
            self._current_a = current_a
            self._consume_battery(power_w, dt)
            self._integrate_dynamics(dt)
        else:
            self._motor_outputs = np.zeros(4, dtype=float)
            self._motor_thrusts = np.zeros(4, dtype=float)
            self._estimated_power_w = 0.0
            self._current_a = 0.0
            if self._position[2] > 0.0:
                self._integrate_dynamics(dt)

        self._apply_ground_constraint()
        self._update_mode()
        self._t += dt
        return self.telemetry_frame()

    def _all_pids(self) -> tuple[PID, ...]:
        return (
            self._altitude_pid,
            self._position_x_pid,
            self._position_y_pid,
            self._roll_pid,
            self._pitch_pid,
            self._yaw_pid,
        )

    def _control(self, dt: float) -> np.ndarray:
        altitude_error = self._target_altitude - self._position[2]
        vertical_accel_command = self._altitude_pid.step(altitude_error, dt)
        required_total_thrust = max(
            0.0,
            self.engineering.total_mass_kg
            * (GRAVITY_MPS2 + vertical_accel_command),
        )
        required_total_thrust = min(
            required_total_thrust,
            self.engineering.max_total_thrust_n,
        )
        required_per_motor = required_total_thrust / 4.0
        base_performance = interpolate_motor_performance_at_thrust(
            self.motor,
            self.propeller.id,
            self.battery_parameters.nominal_voltage_v,
            required_per_motor,
        )

        x_error = self._target_position[0] - self._position[0]
        y_error = self._target_position[1] - self._position[1]
        desired_ax = self._position_x_pid.step(x_error, dt)
        desired_ay = self._position_y_pid.step(y_error, dt)
        target_pitch = max(
            -self.config.max_tilt_rad,
            min(self.config.max_tilt_rad, -desired_ax / GRAVITY_MPS2),
        )
        target_roll = max(
            -self.config.max_tilt_rad,
            min(self.config.max_tilt_rad, -desired_ay / GRAVITY_MPS2),
        )

        roll_accel = self._roll_pid.step(
            target_roll - self._attitude[0],
            dt,
        )
        pitch_accel = self._pitch_pid.step(
            target_pitch - self._attitude[1],
            dt,
        )
        yaw_accel = self._yaw_pid.step(-self._attitude[2], dt)

        roll_mix = (
            roll_accel
            / self.config.attitude_accel_limit
            * self.config.motor_mix_gain
        )
        pitch_mix = (
            pitch_accel
            / self.config.attitude_accel_limit
            * self.config.motor_mix_gain
        )
        yaw_mix = (
            yaw_accel
            / self.config.yaw_accel_limit
            * self.config.yaw_mix_gain
        )

        outputs = (
            np.full(4, base_performance.throttle, dtype=float)
            + roll_mix * np.array([1.0, -1.0, -1.0, 1.0])
            + pitch_mix * np.array([-1.0, -1.0, 1.0, 1.0])
            + yaw_mix * np.array([1.0, -1.0, 1.0, -1.0])
        )
        return np.clip(outputs, 0.0, 1.0)

    def _propulsion(
        self,
        outputs: np.ndarray,
    ) -> tuple[np.ndarray, float, float]:
        points = [
            interpolate_motor_performance(
                self.motor,
                self.propeller.id,
                self.battery_parameters.nominal_voltage_v,
                float(output),
            )
            for output in outputs
        ]
        thrusts = np.array([point.thrust_n for point in points], dtype=float)
        power_w = sum(point.power_w for point in points)
        current_a = sum(point.current_a for point in points)
        return thrusts, float(power_w), float(current_a)

    def _consume_battery(self, power_w: float, dt: float) -> None:
        if self.battery_energy_wh <= 0.0:
            self._battery_remaining = 0.0
            return
        consumed_wh = power_w * dt / 3600.0
        self._battery_remaining = max(
            0.0,
            self._battery_remaining - consumed_wh / self.battery_energy_wh,
        )

    def _integrate_dynamics(self, dt: float) -> None:
        total_thrust = float(np.sum(self._motor_thrusts))
        roll, pitch, yaw = self._attitude
        horizontal_x = -total_thrust * sin(pitch)
        horizontal_y = -total_thrust * sin(roll)
        vertical = total_thrust * cos(roll) * cos(pitch)
        thrust_force = np.array(
            [
                cos(yaw) * horizontal_x - sin(yaw) * horizontal_y,
                sin(yaw) * horizontal_x + cos(yaw) * horizontal_y,
                vertical,
            ],
            dtype=float,
        )
        gravity_force = np.array(
            [0.0, 0.0, -self.engineering.total_mass_kg * GRAVITY_MPS2],
            dtype=float,
        )
        relative_air_velocity = self._velocity - self._wind_velocity
        drag_force = (
            -self.config.drag_coefficient
            * relative_air_velocity
            * np.linalg.norm(relative_air_velocity)
        )
        acceleration = (
            thrust_force + gravity_force + drag_force
        ) / self.engineering.total_mass_kg
        self._velocity += acceleration * dt
        self._position += self._velocity * dt

        torque = np.zeros(3, dtype=float)
        for motor_name, thrust in zip(MOTOR_ORDER, self._motor_thrusts):
            position = self.motor_positions[motor_name]
            torque[0] += position[1] * thrust
            torque[1] += -position[0] * thrust
        torque[2] = self.config.yaw_torque_coefficient_m * float(
            self._motor_thrusts[0]
            - self._motor_thrusts[1]
            + self._motor_thrusts[2]
            - self._motor_thrusts[3]
        )
        angular_acceleration = torque / self.inertia
        self._angular_velocity += angular_acceleration * dt
        self._angular_velocity *= exp(-self.config.angular_damping * dt)
        self._attitude += self._angular_velocity * dt
        self._attitude[0] = max(-radians(35.0), min(radians(35.0), self._attitude[0]))
        self._attitude[1] = max(-radians(35.0), min(radians(35.0), self._attitude[1]))

    def _apply_ground_constraint(self) -> None:
        if self._position[2] < 0.0:
            self._position[2] = 0.0
        if self._position[2] == 0.0 and self._velocity[2] < 0.0:
            self._velocity[2] = 0.0
        for axis in (0, 1):
            if self._position[axis] > FLIGHT_BOUNDARY_M:
                self._position[axis] = FLIGHT_BOUNDARY_M
                self._velocity[axis] = min(0.0, self._velocity[axis])
            elif self._position[axis] < -FLIGHT_BOUNDARY_M:
                self._position[axis] = -FLIGHT_BOUNDARY_M
                self._velocity[axis] = max(0.0, self._velocity[axis])

    def _update_mode(self) -> None:
        if self._flight_mode == "TAKING_OFF":
            within_altitude = (
                abs(self._position[2] - self._target_altitude) < 0.25
            )
            low_vertical_speed = abs(self._velocity[2]) < 0.16
            if within_altitude and low_vertical_speed:
                self._hover_counter += 1
            else:
                self._hover_counter = 0
            if self._hover_counter >= 25:
                self._flight_mode = "HOVERING"
                self._hover_counter = 0
        elif self._flight_mode == "LANDING":
            if self._position[2] <= 0.08 and abs(self._velocity[2]) < 0.25:
                self._position[:] = 0.0
                self._velocity[:] = 0.0
                self._attitude[:] = 0.0
                self._angular_velocity[:] = 0.0
                self._motor_outputs[:] = 0.0
                self._motor_thrusts[:] = 0.0
                self._armed = False
                self._flight_mode = "IDLE"
                self._target_altitude = 0.0

    def telemetry_frame(self) -> TelemetryFrame:
        voltage_v = (
            self.battery_parameters.voltage_min_v
            + (
                self.battery_parameters.voltage_max_v
                - self.battery_parameters.voltage_min_v
            )
            * self._battery_remaining
        )
        return TelemetryFrame(
            t=self._t,
            position=Vector3(
                x=float(self._position[0]),
                y=float(self._position[1]),
                z=float(self._position[2]),
            ),
            velocity=Vector3(
                x=float(self._velocity[0]),
                y=float(self._velocity[1]),
                z=float(self._velocity[2]),
            ),
            attitude=Attitude(
                roll=float(self._attitude[0]),
                pitch=float(self._attitude[1]),
                yaw=float(self._attitude[2]),
            ),
            angular_velocity=AngularVelocity(
                p=float(self._angular_velocity[0]),
                q=float(self._angular_velocity[1]),
                r=float(self._angular_velocity[2]),
            ),
            center_of_gravity=self.engineering.center_of_gravity_m,
            motors=MotorTelemetry(
                outputs=[float(value) for value in self._motor_outputs],
                thrusts_n=[float(value) for value in self._motor_thrusts],
            ),
            forces=ForcesTelemetry(
                gravity_n=(
                    self.engineering.total_mass_kg * GRAVITY_MPS2
                ),
                total_thrust_n=float(np.sum(self._motor_thrusts)),
            ),
            wind=WindTelemetry(
                speed_mps=self._wind_speed,
                direction_deg=self._wind_direction,
            ),
            power=PowerTelemetry(
                estimated_power_w=self._estimated_power_w,
                battery_remaining=self._battery_remaining,
                voltage_v=voltage_v,
                current_a=self._current_a,
            ),
            armed=self._armed,
            flight_mode=self._flight_mode,
        )
