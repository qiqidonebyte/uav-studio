from __future__ import annotations

import os
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.px4.flight_bridge import FlightValidationPx4Bridge


DEFAULT_SLOT_COUNT = 12
DEFAULT_PORTS = tuple(range(14600, 14612))


def _parse_ports(slot_count: int) -> list[int]:
    raw = os.getenv("PX4_CLASSROOM_PORTS", "").strip()
    if raw:
        ports = [int(item.strip()) for item in raw.split(",") if item.strip()]
    else:
        ports = list(DEFAULT_PORTS)
    if len(ports) < slot_count:
        raise RuntimeError(
            f"PX4_CLASSROOM_PORTS 仅配置 {len(ports)} 个端口，但 PX4_POOL_SIZE={slot_count}"
        )
    selected = ports[:slot_count]
    if len(set(selected)) != len(selected):
        raise RuntimeError("PX4_CLASSROOM_PORTS 存在重复端口")
    return selected


@dataclass
class Px4Slot:
    slot_id: int
    port: int
    bridge: FlightValidationPx4Bridge
    run_id: int | None = None
    student_user_id: int | None = None
    acquired_at: float = 0.0
    last_seen_at: float = 0.0
    process: subprocess.Popen[Any] | None = None
    recovery_attempts: int = 0
    last_error: str = ""
    lock: threading.RLock = field(default_factory=threading.RLock)

    @property
    def connection_url(self) -> str:
        return f"udpin:0.0.0.0:{self.port}"

    @property
    def free(self) -> bool:
        return self.run_id is None


class Px4SessionManager:
    """Small fixed PX4 resource pool for classroom use.

    The manager owns bridge objects and optional PX4 child processes. It does
    not own training state; TrainingRun/PX4Session rows remain the source of
    truth. This keeps recovery simple: runtime slots can be discarded and
    rebuilt without losing student progress or grades.
    """

    def __init__(self) -> None:
        self.slot_count = int(os.getenv("PX4_POOL_SIZE", str(DEFAULT_SLOT_COUNT)))
        if self.slot_count < 1 or self.slot_count > 64:
            raise RuntimeError("PX4_POOL_SIZE 必须在 1-64 之间")
        self.idle_timeout_s = int(os.getenv("PX4_IDLE_TIMEOUT", "600"))
        self.start_timeout_s = int(os.getenv("PX4_START_TIMEOUT", "30"))
        self.recovery_retry = int(os.getenv("PX4_RECOVERY_RETRY", "1"))
        self.launch_template = os.getenv("PX4_SLOT_LAUNCH_TEMPLATE", "").strip()
        self.px4_dir = Path(os.getenv("PX4_DIR", str(Path.home() / "PX4-Autopilot")))
        ports = _parse_ports(self.slot_count)
        self._lock = threading.RLock()
        self._slots: list[Px4Slot] = [
            Px4Slot(
                slot_id=index + 1,
                port=port,
                bridge=FlightValidationPx4Bridge(f"udpin:0.0.0.0:{port}"),
            )
            for index, port in enumerate(ports)
        ]

    def slot(self, slot_id: int) -> Px4Slot | None:
        if slot_id < 1 or slot_id > len(self._slots):
            return None
        return self._slots[slot_id - 1]

    def slot_for_run(self, run_id: int) -> Px4Slot | None:
        with self._lock:
            return next((item for item in self._slots if item.run_id == run_id), None)

    def free_slots(self) -> list[Px4Slot]:
        with self._lock:
            return [item for item in self._slots if item.free]

    def acquire_runtime(self, run_id: int, student_user_id: int) -> Px4Slot | None:
        with self._lock:
            existing = next((item for item in self._slots if item.run_id == run_id), None)
            if existing is not None:
                self.touch(existing)
                return existing
            slot = next((item for item in self._slots if item.free), None)
            if slot is None:
                return None
            now = time.monotonic()
            slot.run_id = run_id
            slot.student_user_id = student_user_id
            slot.acquired_at = now
            slot.last_seen_at = now
            slot.recovery_attempts = 0
            slot.last_error = ""
            self._ensure_started(slot)
            return slot

    def touch(self, slot: Px4Slot) -> None:
        slot.last_seen_at = time.monotonic()

    def release_runtime(self, run_id: int) -> None:
        with self._lock:
            slot = next((item for item in self._slots if item.run_id == run_id), None)
            if slot is None:
                return
            self._stop_slot(slot)
            slot.run_id = None
            slot.student_user_id = None
            slot.acquired_at = 0.0
            slot.last_seen_at = 0.0
            slot.recovery_attempts = 0
            slot.last_error = ""

    def reset_runtime(self) -> None:
        with self._lock:
            for slot in self._slots:
                self._stop_slot(slot)
                slot.run_id = None
                slot.student_user_id = None
                slot.acquired_at = 0.0
                slot.last_seen_at = 0.0
                slot.recovery_attempts = 0
                slot.last_error = ""

    def shutdown(self) -> None:
        self.reset_runtime()

    def runtime_status(self, slot: Px4Slot) -> dict[str, Any]:
        self.touch(slot)
        self._recover_if_needed(slot)
        payload = slot.bridge.status()
        payload.update(
            {
                "slot_id": slot.slot_id,
                "slot_port": slot.port,
                "run_id": slot.run_id,
                "managed_process": bool(self.launch_template),
            }
        )
        if slot.last_error and not payload.get("last_error"):
            payload["last_error"] = slot.last_error
        return payload

    def telemetry(self, slot: Px4Slot) -> dict[str, Any]:
        self.touch(slot)
        self._recover_if_needed(slot)
        payload = slot.bridge.telemetry()
        payload.update({"slot_id": slot.slot_id, "slot_port": slot.port, "run_id": slot.run_id})
        return payload

    def _ensure_started(self, slot: Px4Slot) -> None:
        with slot.lock:
            try:
                slot.bridge.start()
            except Exception as exc:
                slot.last_error = str(exc)
            if self.launch_template and (slot.process is None or slot.process.poll() is not None):
                command = self.launch_template.format(
                    slot=slot.slot_id,
                    instance=slot.slot_id - 1,
                    port=slot.port,
                )
                env = os.environ.copy()
                env.update(
                    {
                        "PX4_SLOT": str(slot.slot_id),
                        "PX4_INSTANCE": str(slot.slot_id - 1),
                        "PX4_OFFBOARD_PORT": str(slot.port),
                    }
                )
                try:
                    slot.process = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=str(self.px4_dir) if self.px4_dir.exists() else None,
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                except Exception as exc:
                    slot.last_error = f"PX4 Slot 启动失败：{exc}"

    def _stop_slot(self, slot: Px4Slot) -> None:
        with slot.lock:
            try:
                slot.bridge.stop()
            except Exception:
                pass
            process = slot.process
            slot.process = None
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass

    def _recover_if_needed(self, slot: Px4Slot) -> None:
        process_dead = slot.process is not None and slot.process.poll() is not None
        bridge_status = slot.bridge.status()
        bridge_dead = not bool(bridge_status.get("running"))
        if not process_dead and not bridge_dead:
            return
        if slot.recovery_attempts >= self.recovery_retry:
            return
        slot.recovery_attempts += 1
        self._stop_slot(slot)
        self._ensure_started(slot)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            used = sum(1 for item in self._slots if not item.free)
            return {
                "pool_size": self.slot_count,
                "used": used,
                "free": self.slot_count - used,
                "idle_timeout_s": self.idle_timeout_s,
                "slots": [
                    {
                        "slot_id": item.slot_id,
                        "port": item.port,
                        "run_id": item.run_id,
                        "student_user_id": item.student_user_id,
                        "connected": item.bridge.is_connected if not item.free else False,
                        "last_error": item.last_error,
                    }
                    for item in self._slots
                ],
            }


session_manager = Px4SessionManager()
