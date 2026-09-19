from __future__ import annotations

import math

from backend.schemas import Vector3

GRAVITY_MPS2 = 9.80665
FLIGHT_BOUNDARY_M = 25.0

MOTOR_ORDER = ("M1", "M2", "M3", "M4")
MOTOR_SPINS = {
    "M1": "CCW",
    "M2": "CW",
    "M3": "CCW",
    "M4": "CW",
}
SLOT_DISPLAY_NAMES = {
    "frame": "机架",
    "motor": "电机",
    "esc": "电调",
    "propeller": "螺旋桨",
    "battery": "电池",
    "power_module": "电源模块",
    "flight_controller": "飞控",
    "gnss": "GNSS/罗盘",
    "payload": "任务载荷",
}


def motor_positions_m(motor_diagonal_m: float) -> dict[str, Vector3]:
    """Return the frozen Quad-X motor positions in the body frame.

    ``motor_diagonal_m`` is the distance between diagonally opposite motors.
    The frame origin is at the center of the aircraft.
    """

    radius_m = motor_diagonal_m / 2.0
    offset_m = radius_m / math.sqrt(2.0)
    return {
        "M1": Vector3(x=offset_m, y=offset_m, z=0.0),
        "M2": Vector3(x=offset_m, y=-offset_m, z=0.0),
        "M3": Vector3(x=-offset_m, y=-offset_m, z=0.0),
        "M4": Vector3(x=-offset_m, y=offset_m, z=0.0),
    }
