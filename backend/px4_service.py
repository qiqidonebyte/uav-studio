from __future__ import annotations

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


bridge = Px4Bridge()


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
    version="1.0.0",
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
