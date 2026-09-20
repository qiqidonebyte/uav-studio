from __future__ import annotations

import math
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

try:
    from pymavlink import mavutil
except Exception as exc:  # pragma: no cover - exercised on machines without optional dependency
    mavutil = None  # type: ignore[assignment]
    PYMAVLINK_IMPORT_ERROR: Exception | None = exc
else:
    PYMAVLINK_IMPORT_ERROR = None


class Px4BridgeError(RuntimeError):
    pass


@dataclass
class _TelemetryState:
    heartbeat_at: float = 0.0
    system_id: int | None = None
    component_id: int | None = None
    mode: str = "UNKNOWN"
    armed: bool = False
    landed_state: int | None = None
    attitude: dict[str, float] = field(default_factory=lambda: {
        "roll": 0.0, "pitch": 0.0, "yaw": 0.0,
        "rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0,
    })
    local_position: dict[str, float] = field(default_factory=lambda: {
        "x": 0.0, "y": 0.0, "z": 0.0,
        "vx": 0.0, "vy": 0.0, "vz": 0.0,
    })
    global_position: dict[str, float | None] = field(default_factory=lambda: {
        "lat_deg": None, "lon_deg": None, "relative_alt_m": None,
    })
    gps: dict[str, int | float | None] = field(default_factory=lambda: {
        "fix_type": None, "satellites": None, "eph": None,
    })
    battery: dict[str, float | int | None] = field(default_factory=lambda: {
        "voltage_v": None, "current_a": None, "remaining": None,
    })
    motor_outputs: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    estimator_flags: int | None = None
    last_statustext: str = ""
    last_statustext_at: float = 0.0


class Px4Bridge:
    """Single-consumer MAVLink bridge for a PX4 SITL/SIH instance.

    V1 intentionally uses pymavlink only. This avoids binding MAVSDK and
    pymavlink to the same PX4 offboard UDP port. MAVSDK can be added later
    behind mavlink-router without changing the browser API.
    """

    def __init__(self, connection_url: str | None = None) -> None:
        self.connection_url = connection_url or os.getenv(
            "PX4_CONNECTION", "udpin:0.0.0.0:14540"
        )
        self._connection: Any | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._state = _TelemetryState()
        self._command_waiters: dict[int, tuple[threading.Event, dict[str, Any]]] = {}
        self._param_waiters: dict[str, tuple[threading.Event, dict[str, Any]]] = {}
        self._last_error = ""
        self._started_at = 0.0

    @property
    def dependency_available(self) -> bool:
        return mavutil is not None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if mavutil is None:
            raise Px4BridgeError(
                "pymavlink 未安装，请先执行 pip install -r requirements.txt"
            ) from PYMAVLINK_IMPORT_ERROR
        self._stop.clear()
        self._last_error = ""
        try:
            self._connection = mavutil.mavlink_connection(
                self.connection_url,
                autoreconnect=True,
                source_system=int(os.getenv("PX4_BRIDGE_SYSTEM_ID", "245")),
            )
        except Exception as exc:
            self._connection = None
            self._last_error = str(exc)
            raise Px4BridgeError(f"无法打开 MAVLink 连接：{exc}") from exc
        self._started_at = time.monotonic()
        self._thread = threading.Thread(
            target=self._receive_loop,
            name="uav-studio-px4-bridge",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=1.0)
        self._thread = None

    def reconnect(self, connection_url: str | None = None) -> None:
        self.stop()
        if connection_url:
            self.connection_url = connection_url
        with self._lock:
            self._state = _TelemetryState()
        self.start()

    def _receive_loop(self) -> None:
        assert self._connection is not None
        while not self._stop.is_set():
            try:
                message = self._connection.recv_match(blocking=True, timeout=0.35)
            except Exception as exc:
                self._last_error = str(exc)
                time.sleep(0.2)
                continue
            if message is None:
                continue
            try:
                self._handle_message(message)
            except Exception as exc:
                self._last_error = f"解析 MAVLink 消息失败：{exc}"

    def _handle_message(self, message: Any) -> None:
        msg_type = message.get_type()
        now = time.monotonic()
        with self._lock:
            state = self._state
            if msg_type == "HEARTBEAT":
                state.heartbeat_at = now
                state.system_id = message.get_srcSystem()
                state.component_id = message.get_srcComponent()
                try:
                    state.mode = mavutil.mode_string_v10(message) if mavutil else "UNKNOWN"
                except Exception:
                    state.mode = "UNKNOWN"
                if mavutil:
                    state.armed = bool(
                        int(message.base_mode)
                        & int(mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                    )
            elif msg_type == "ATTITUDE":
                state.attitude = {
                    "roll": float(message.roll),
                    "pitch": float(message.pitch),
                    "yaw": float(message.yaw),
                    "rollspeed": float(message.rollspeed),
                    "pitchspeed": float(message.pitchspeed),
                    "yawspeed": float(message.yawspeed),
                }
            elif msg_type == "LOCAL_POSITION_NED":
                state.local_position = {
                    "x": float(message.x),
                    "y": float(message.y),
                    "z": -float(message.z),
                    "vx": float(message.vx),
                    "vy": float(message.vy),
                    "vz": -float(message.vz),
                }
            elif msg_type == "GLOBAL_POSITION_INT":
                state.global_position = {
                    "lat_deg": float(message.lat) / 1e7,
                    "lon_deg": float(message.lon) / 1e7,
                    "relative_alt_m": float(message.relative_alt) / 1000.0,
                }
            elif msg_type == "GPS_RAW_INT":
                eph = None if int(message.eph) == 65535 else float(message.eph) / 100.0
                satellites = None if int(message.satellites_visible) == 255 else int(message.satellites_visible)
                state.gps = {
                    "fix_type": int(message.fix_type),
                    "satellites": satellites,
                    "eph": eph,
                }
            elif msg_type == "SYS_STATUS":
                voltage = None if int(message.voltage_battery) == 65535 else float(message.voltage_battery) / 1000.0
                current = None if int(message.current_battery) == -1 else float(message.current_battery) / 100.0
                remaining = None if int(message.battery_remaining) < 0 else int(message.battery_remaining)
                state.battery = {
                    "voltage_v": voltage,
                    "current_a": current,
                    "remaining": remaining,
                }
            elif msg_type == "EXTENDED_SYS_STATE":
                state.landed_state = int(message.landed_state)
            elif msg_type == "ESTIMATOR_STATUS":
                state.estimator_flags = int(message.flags)
            elif msg_type == "ACTUATOR_OUTPUT_STATUS":
                raw = list(getattr(message, "actuator", []) or [])
                normalized: list[float] = []
                for item in raw[:4]:
                    value = float(item)
                    if math.isnan(value) or value < 0:
                        value = 0.0
                    normalized.append(max(0.0, min(1.0, value)))
                while len(normalized) < 4:
                    normalized.append(0.0)
                state.motor_outputs = normalized
            elif msg_type == "STATUSTEXT":
                text = getattr(message, "text", b"")
                if isinstance(text, bytes):
                    text = text.decode("utf-8", errors="replace")
                state.last_statustext = str(text).rstrip("\x00")
                state.last_statustext_at = now
            elif msg_type == "COMMAND_ACK":
                command = int(message.command)
                waiter = self._command_waiters.get(command)
                if waiter:
                    event, payload = waiter
                    payload["result"] = int(message.result)
                    payload["progress"] = int(getattr(message, "progress", 0) or 0)
                    event.set()
            elif msg_type == "PARAM_VALUE":
                param_id = getattr(message, "param_id", "")
                if isinstance(param_id, bytes):
                    param_id = param_id.decode("ascii", errors="ignore")
                param_id = str(param_id).rstrip("\x00")
                waiter = self._param_waiters.get(param_id)
                if waiter:
                    event, payload = waiter
                    payload.update({
                        "name": param_id,
                        "value": float(message.param_value),
                        "type": int(message.param_type),
                        "index": int(message.param_index),
                        "count": int(message.param_count),
                    })
                    event.set()

    def _require_connection(self) -> Any:
        if self._connection is None:
            raise Px4BridgeError("PX4 Bridge 尚未启动")
        if not self.is_connected:
            raise Px4BridgeError("尚未收到 PX4 Heartbeat，请先启动 PX4 SIH")
        return self._connection

    @property
    def is_connected(self) -> bool:
        with self._lock:
            heartbeat = self._state.heartbeat_at
        return heartbeat > 0 and (time.monotonic() - heartbeat) < 3.0

    def status(self) -> dict[str, Any]:
        with self._lock:
            heartbeat = self._state.heartbeat_at
            age = None if heartbeat <= 0 else max(0.0, time.monotonic() - heartbeat)
            return {
                "dependency_available": self.dependency_available,
                "running": bool(self._thread and self._thread.is_alive()),
                "connected": bool(heartbeat > 0 and age is not None and age < 3.0),
                "connection_url": self.connection_url,
                "heartbeat_age_s": age,
                "system_id": self._state.system_id,
                "component_id": self._state.component_id,
                "mode": self._state.mode,
                "armed": self._state.armed,
                "last_error": self._last_error,
                "uptime_s": max(0.0, time.monotonic() - self._started_at) if self._started_at else 0.0,
            }

    def telemetry(self) -> dict[str, Any]:
        with self._lock:
            state = self._state
            status = self.status()
            text_recent = (
                state.last_statustext
                if state.last_statustext_at and time.monotonic() - state.last_statustext_at < 20.0
                else ""
            )
            lower = text_recent.lower()
            prearm_ok = not any(
                token in lower
                for token in ("preflight fail", "pre-arm", "arming denied", "arm denied")
            )
            return {
                **status,
                "landed_state": state.landed_state,
                "attitude": dict(state.attitude),
                "local_position": dict(state.local_position),
                "global_position": dict(state.global_position),
                "gps": dict(state.gps),
                "battery": dict(state.battery),
                "motors": {"outputs": list(state.motor_outputs)},
                "estimator": {
                    "flags": state.estimator_flags,
                    "ok": None if state.estimator_flags is None else state.estimator_flags != 0,
                },
                "statustext": text_recent,
                "prearm_ok": prearm_ok,
            }

    def request_streams(self, rate_hz: float = 10.0) -> None:
        connection = self._require_connection()
        interval_us = int(1_000_000 / max(1.0, rate_hz))
        names = (
            "ATTITUDE",
            "LOCAL_POSITION_NED",
            "GLOBAL_POSITION_INT",
            "SYS_STATUS",
            "GPS_RAW_INT",
            "EXTENDED_SYS_STATE",
            "ACTUATOR_OUTPUT_STATUS",
            "ESTIMATOR_STATUS",
        )
        for name in names:
            message_id = getattr(mavutil.mavlink, f"MAVLINK_MSG_ID_{name}", None)
            if message_id is None:
                continue
            connection.mav.command_long_send(
                connection.target_system,
                connection.target_component,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0,
                float(message_id),
                float(interval_us),
                0, 0, 0, 0, 0,
            )

    def _command(self, command: int, params: list[float], timeout: float = 3.0) -> dict[str, Any]:
        connection = self._require_connection()
        values = list(params[:7]) + [0.0] * (7 - len(params))
        event = threading.Event()
        payload: dict[str, Any] = {}
        with self._lock:
            self._command_waiters[command] = (event, payload)
        try:
            connection.mav.command_long_send(
                connection.target_system,
                connection.target_component,
                command,
                0,
                *values,
            )
            if not event.wait(timeout=timeout):
                return {"accepted": False, "timeout": True, "command": command}
            result = int(payload.get("result", -1))
            accepted_values = {
                int(mavutil.mavlink.MAV_RESULT_ACCEPTED),
                int(mavutil.mavlink.MAV_RESULT_IN_PROGRESS),
            }
            return {
                "accepted": result in accepted_values,
                "timeout": False,
                "command": command,
                "result": result,
                "progress": payload.get("progress", 0),
            }
        finally:
            with self._lock:
                self._command_waiters.pop(command, None)

    def arm(self) -> dict[str, Any]:
        return self._command(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            [1.0, 0.0],
        )

    def disarm(self) -> dict[str, Any]:
        return self._command(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            [0.0, 0.0],
        )

    def takeoff(self, altitude_m: float = 2.0) -> dict[str, Any]:
        if altitude_m <= 0 or altitude_m > 30:
            raise Px4BridgeError("V1 起飞高度必须在 0-30 m")
        nan = float("nan")
        return self._command(
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            [0.0, 0.0, 0.0, nan, nan, nan, float(altitude_m)],
            timeout=5.0,
        )

    def land(self) -> dict[str, Any]:
        nan = float("nan")
        return self._command(
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            [0.0, 0.0, 0.0, nan, nan, nan, 0.0],
            timeout=5.0,
        )

    def prearm_check(self) -> dict[str, Any]:
        command = int(getattr(mavutil.mavlink, "MAV_CMD_RUN_PREARM_CHECKS", 401))
        return self._command(command, [0.0] * 7, timeout=4.0)

    def test_motor(self, motor_index: int, value: float = 0.2, timeout_s: float = 1.5) -> dict[str, Any]:
        if motor_index not in {1, 2, 3, 4}:
            raise Px4BridgeError("仅支持 M1-M4")
        if self.telemetry()["armed"]:
            raise Px4BridgeError("执行机构测试要求飞机处于未解锁状态")
        value = max(0.0, min(0.35, float(value)))
        timeout_s = max(0.2, min(3.0, float(timeout_s)))
        output_function = 100 + motor_index  # PX4 Motor 1..4 => 101..104
        command = int(getattr(mavutil.mavlink, "MAV_CMD_ACTUATOR_TEST", 310))
        result = self._command(
            command,
            [value, timeout_s, 0.0, 0.0, float(output_function), 0.0, 0.0],
            timeout=max(3.0, timeout_s + 1.0),
        )
        return {
            **result,
            "motor": f"M{motor_index}",
            "output_function": output_function,
            "value": value,
            "timeout_s": timeout_s,
        }

    def get_parameter(self, name: str, timeout: float = 2.5) -> dict[str, Any]:
        connection = self._require_connection()
        key = name.strip().upper()
        if not key or len(key) > 16:
            raise Px4BridgeError("PX4 参数名长度必须为 1-16 个字符")
        event = threading.Event()
        payload: dict[str, Any] = {}
        with self._lock:
            self._param_waiters[key] = (event, payload)
        try:
            connection.mav.param_request_read_send(
                connection.target_system,
                connection.target_component,
                key.encode("ascii"),
                -1,
            )
            if not event.wait(timeout=timeout):
                raise Px4BridgeError(f"读取参数 {key} 超时")
            return dict(payload)
        finally:
            with self._lock:
                self._param_waiters.pop(key, None)

    def set_parameter(self, name: str, value: float, timeout: float = 3.0) -> dict[str, Any]:
        connection = self._require_connection()
        current = self.get_parameter(name, timeout=timeout)
        key = str(current["name"])
        param_type = int(current["type"])
        event = threading.Event()
        payload: dict[str, Any] = {}
        with self._lock:
            self._param_waiters[key] = (event, payload)
        try:
            connection.mav.param_set_send(
                connection.target_system,
                connection.target_component,
                key.encode("ascii"),
                float(value),
                param_type,
            )
            if not event.wait(timeout=timeout):
                raise Px4BridgeError(f"设置参数 {key} 超时")
            return dict(payload)
        finally:
            with self._lock:
                self._param_waiters.pop(key, None)
