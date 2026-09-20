from __future__ import annotations

import math
import os
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from backend.px4 import Px4Bridge, Px4BridgeError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConnectRequest(StrictModel):
    connection_url: str | None = Field(default=None, max_length=200)


class TakeoffRequest(StrictModel):
    altitude_m: float = Field(default=2.0, gt=0.0, le=30.0)


class MotorTestRequest(StrictModel):
    value: float = Field(default=0.20, ge=0.0, le=0.35)
    timeout_s: float = Field(default=1.5, ge=0.2, le=3.0)


class ParameterWriteRequest(StrictModel):
    value: float


class FlightValidationPx4Bridge(Px4Bridge):
    """PX4 Bridge extension used by Flight Lab.

    The original Bridge API treated the takeoff input as if MAV_CMD_NAV_TAKEOFF
    param7 were a relative altitude. PX4 defines param7 as AMSL altitude.

    We keep the browser API convenient (relative altitude above home), but
    convert it to AMSL using GLOBAL_POSITION_INT before sending command 22.
    """

    def __init__(self, connection_url: str | None = None) -> None:
        super().__init__(connection_url)
        self._alt_amsl_m: float | None = None

    def reconnect(self, connection_url: str | None = None) -> None:
        self._alt_amsl_m = None
        super().reconnect(connection_url)

    def _handle_message(self, message: Any) -> None:
        super()._handle_message(message)
        try:
            if message.get_type() != "GLOBAL_POSITION_INT":
                return
            raw_alt = getattr(message, "alt", None)
            if raw_alt is None:
                return
            value = float(raw_alt) / 1000.0
            if math.isfinite(value):
                self._alt_amsl_m = value
        except Exception:
            # Base telemetry parsing has already succeeded. An unavailable AMSL
            # value only disables relative takeoff until the next good sample.
            return

    def telemetry(self) -> dict[str, Any]:
        payload = super().telemetry()
        global_position = dict(payload.get("global_position") or {})
        global_position["alt_amsl_m"] = self._alt_amsl_m
        payload["global_position"] = global_position
        return payload

    def takeoff(self, altitude_m: float = 2.0) -> dict[str, Any]:
        if altitude_m <= 0 or altitude_m > 30:
            raise Px4BridgeError("PX4 起飞相对高度必须在 0-30 m")

        telemetry = self.telemetry()
        global_position = telemetry.get("global_position") or {}
        current_amsl = self._alt_amsl_m
        relative_alt = global_position.get("relative_alt_m")

        if current_amsl is None:
            raise Px4BridgeError(
                "尚未获得 GLOBAL_POSITION_INT 的 AMSL 高度，无法安全计算起飞目标高度"
            )

        relative_altitude = (
            float(relative_alt)
            if isinstance(relative_alt, (int, float)) and math.isfinite(float(relative_alt))
            else 0.0
        )
        home_amsl = current_amsl - relative_altitude
        target_amsl = home_amsl + float(altitude_m)
        nan = float("nan")

        result = self._command(
            22,  # MAV_CMD_NAV_TAKEOFF
            [0.0, 0.0, 0.0, nan, nan, nan, target_amsl],
            timeout=5.0,
        )
        return {
            **result,
            "relative_altitude_m": float(altitude_m),
            "home_altitude_amsl_m": home_amsl,
            "target_altitude_amsl_m": target_amsl,
        }


bridge = FlightValidationPx4Bridge()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        bridge.start()
    except Px4BridgeError:
        # The service must still boot so the UI can show an actionable dependency/error state.
        pass
    yield
    bridge.stop()


app = FastAPI(
    title="UAV Studio PX4 Bridge V1",
    version="1.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run(action):
    try:
        return action()
    except Px4BridgeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PX4 Bridge 内部错误：{exc}") from exc


@app.get("/api/px4/health")
def health() -> dict[str, Any]:
    return {"service": "uav-studio-px4-bridge", **bridge.status()}


@app.get("/api/px4/status")
def status() -> dict[str, Any]:
    return bridge.status()


@app.get("/api/px4/telemetry")
def telemetry() -> dict[str, Any]:
    return bridge.telemetry()


@app.post("/api/px4/connect")
def connect(request: ConnectRequest) -> dict[str, Any]:
    def action():
        bridge.reconnect(request.connection_url)
        return bridge.status()
    return run(action)


@app.post("/api/px4/disconnect")
def disconnect() -> dict[str, Any]:
    bridge.stop()
    return bridge.status()


@app.post("/api/px4/request-streams")
def request_streams() -> dict[str, Any]:
    return run(lambda: (bridge.request_streams(10.0) or {"ok": True}))


@app.post("/api/px4/arm")
def arm() -> dict[str, Any]:
    return run(bridge.arm)


@app.post("/api/px4/disarm")
def disarm() -> dict[str, Any]:
    return run(bridge.disarm)


@app.post("/api/px4/takeoff")
def takeoff(request: TakeoffRequest) -> dict[str, Any]:
    return run(lambda: bridge.takeoff(request.altitude_m))


@app.post("/api/px4/land")
def land() -> dict[str, Any]:
    return run(bridge.land)


@app.post("/api/px4/prearm-check")
def prearm_check() -> dict[str, Any]:
    return run(bridge.prearm_check)


@app.post("/api/px4/sensors/{sensor}/calibrate")
def calibrate_sensor(sensor: str) -> dict[str, Any]:
    return run(lambda: bridge.calibrate_sensor(sensor))


@app.post("/api/px4/motors/{motor}/test")
def motor_test(motor: str, request: MotorTestRequest) -> dict[str, Any]:
    motor_name = motor.strip().upper()
    if motor_name not in {"M1", "M2", "M3", "M4"}:
        raise HTTPException(status_code=422, detail="motor 必须为 M1-M4")
    return run(lambda: bridge.test_motor(int(motor_name[1]), request.value, request.timeout_s))


@app.get("/api/px4/parameters/{name}")
def read_parameter(name: str) -> dict[str, Any]:
    return run(lambda: bridge.get_parameter(name))


@app.put("/api/px4/parameters/{name}")
def write_parameter(name: str, request: ParameterWriteRequest) -> dict[str, Any]:
    return run(lambda: bridge.set_parameter(name, request.value))


if __name__ == "__main__":
    uvicorn.run(
        "backend.px4_service:app",
        host=os.getenv("PX4_BRIDGE_HOST", "0.0.0.0"),
        port=int(os.getenv("PX4_BRIDGE_PORT", "8001")),
        reload=False,
    )
