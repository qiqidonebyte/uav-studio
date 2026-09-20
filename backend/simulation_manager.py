from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter

from backend.constants import FLIGHT_BOUNDARY_M
from backend.schemas import (
    AircraftDefinition,
    AircraftEngineeringSummary,
    Component,
    SimulationStatus,
    TelemetryFrame,
)
from backend.simulator import SimpleSimulator


@dataclass
class SimulationSession:
    id: int
    simulator: SimpleSimulator
    status: SimulationStatus = "STOPPED"
    started_at: datetime | None = None
    frames: list[TelemetryFrame] = field(default_factory=list)
    target_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    waypoints: list[tuple[float, float, float]] = field(default_factory=list)
    task: asyncio.Task | None = field(default=None, repr=False)


class SimulationNotFoundError(KeyError):
    pass


class SimulationManager:
    """In-memory simulator registry.

    The pre-auth V1 implementation kept one global simulation. With real user
    accounts that would allow one browser to replace another user's session, so
    sessions are now keyed by simulation ID while preserving the public method
    contract used by the API and tests.
    """

    def __init__(self) -> None:
        self._sessions: dict[int, SimulationSession] = {}
        self._next_id = 1
        self._last_active_id: int | None = None

    @property
    def active_session(self) -> SimulationSession | None:
        if self._last_active_id is None:
            return None
        return self._sessions.get(self._last_active_id)

    @property
    def next_id(self) -> int:
        return self._next_id

    def set_next_id(self, next_id: int) -> None:
        self._next_id = max(1, next_id)

    def create(
        self,
        aircraft: AircraftDefinition,
        catalog: dict[int, Component],
        engineering: AircraftEngineeringSummary,
        simulation_id: int | None = None,
    ) -> SimulationSession:
        session = SimulationSession(
            id=simulation_id if simulation_id is not None else self._next_id,
            simulator=SimpleSimulator(aircraft, catalog, engineering),
        )
        self._next_id = max(self._next_id, session.id + 1)
        self._sessions[session.id] = session
        self._last_active_id = session.id
        session.frames.append(session.simulator.telemetry_frame())
        return session

    def require(self, simulation_id: int) -> SimulationSession:
        session = self._sessions.get(simulation_id)
        if session is None:
            raise SimulationNotFoundError(simulation_id)
        return session

    def snapshot(self, simulation_id: int):
        session = self.require(simulation_id)
        return {
            "id": session.id,
            "status": session.status,
            "telemetry": session.simulator.telemetry_frame(),
            "target_position": {
                "x": session.target_position[0],
                "y": session.target_position[1],
                "z": session.target_position[2],
            },
            "waypoints": [
                {"x": point[0], "y": point[1], "z": point[2]}
                for point in session.waypoints
            ],
            "boundary_m": FLIGHT_BOUNDARY_M,
        }

    def frame(self, simulation_id: int) -> TelemetryFrame:
        return self.require(simulation_id).simulator.telemetry_frame()

    def start(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        if session.status == "RUNNING":
            return session
        session.simulator.start()
        if session.started_at is None:
            session.started_at = datetime.now(timezone.utc)
        session.status = "RUNNING"
        self._last_active_id = session.id
        if session.task is None or session.task.done():
            session.task = asyncio.create_task(self._run_loop(session))
        return session

    def pause(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.pause()
        session.status = "PAUSED"
        return session

    def reset(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.reset()
        session.status = "STOPPED"
        session.started_at = None
        session.frames = [session.simulator.telemetry_frame()]
        session.target_position = (0.0, 0.0, 0.0)
        session.waypoints = []
        return session

    def arm(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.arm()
        return session

    def takeoff(self, simulation_id: int, altitude_m: float) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.takeoff(altitude_m)
        session.target_position = (
            session.target_position[0],
            session.target_position[1],
            float(altitude_m),
        )
        return session

    def land(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.land()
        return session

    def set_wind(
        self,
        simulation_id: int,
        speed_mps: float,
        direction_deg: float,
    ) -> SimulationSession:
        session = self.require(simulation_id)
        session.simulator.set_wind(speed_mps, direction_deg)
        return session

    def set_target(
        self,
        simulation_id: int,
        x_m: float,
        y_m: float,
    ) -> SimulationSession:
        session = self.require(simulation_id)
        if abs(x_m) > FLIGHT_BOUNDARY_M or abs(y_m) > FLIGHT_BOUNDARY_M:
            raise ValueError("target position is outside the flight boundary")
        session.simulator.set_target_position(x_m, y_m)
        session.target_position = (
            float(x_m),
            float(y_m),
            session.simulator.target_altitude,
        )
        return session

    def set_waypoints(
        self,
        simulation_id: int,
        waypoints: list[tuple[float, float, float]],
    ) -> SimulationSession:
        session = self.require(simulation_id)
        for x_m, y_m, _ in waypoints:
            if abs(x_m) > FLIGHT_BOUNDARY_M or abs(y_m) > FLIGHT_BOUNDARY_M:
                raise ValueError("waypoint is outside the flight boundary")
        session.waypoints = waypoints
        return session

    def stop(self, simulation_id: int) -> SimulationSession:
        session = self.require(simulation_id)
        self._record_frame(session)
        session.status = "STOPPED"
        session.simulator.pause()
        return session

    async def shutdown(self) -> None:
        sessions = list(self._sessions.values())
        for session in sessions:
            session.status = "STOPPED"
            session.simulator.pause()
        for session in sessions:
            if session.task is not None and not session.task.done():
                session.task.cancel()
        for session in sessions:
            if session.task is not None and not session.task.done():
                try:
                    await session.task
                except asyncio.CancelledError:
                    pass

    async def _run_loop(self, session: SimulationSession) -> None:
        next_step_at = perf_counter()
        try:
            while session.status == "RUNNING":
                started_at = perf_counter()
                session.simulator.step()
                self._record_frame(session)
                next_step_at += session.simulator.dt
                delay = next_step_at - perf_counter()
                if delay > 0.0:
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(0)
                    next_step_at = perf_counter()
                    if perf_counter() - started_at > session.simulator.dt * 4:
                        next_step_at = perf_counter()
        except asyncio.CancelledError:
            raise

    def _record_frame(self, session: SimulationSession) -> None:
        frame = session.simulator.telemetry_frame()
        if not session.frames:
            session.frames.append(frame)
            return
        if frame.t - session.frames[-1].t >= 0.05 - 1e-9:
            session.frames.append(frame)
