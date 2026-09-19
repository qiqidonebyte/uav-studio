from __future__ import annotations

from backend.schemas import (
    AircraftDefinition,
    AssemblyIssue,
    AssemblyValidationResult,
    MotorName,
)

SLOT_FIELDS: tuple[tuple[str, str], ...] = (
    ("frame", "frame_id"),
    ("motor", "motor_id"),
    ("esc", "esc_id"),
    ("propeller", "propeller_id"),
    ("battery", "battery_id"),
    ("power_module", "power_module_id"),
    ("flight_controller", "flight_controller_id"),
    ("gnss", "gnss_id"),
    ("payload", "payload_id"),
)


def _missing_slots(aircraft: AircraftDefinition) -> list[str]:
    return [
        slot
        for slot, field_name in SLOT_FIELDS
        if getattr(aircraft, field_name) is None
    ]


def _affected_slots(
    aircraft: AircraftDefinition,
    issue: AssemblyIssue,
) -> list[str]:
    if issue.code == "REQUIRED_COMPONENT_MISSING":
        return _missing_slots(aircraft)
    if issue.code == "COMPONENT_TYPE_MISMATCH":
        return [
            slot
            for slot, field_name in SLOT_FIELDS
            if getattr(aircraft, field_name) is not None
        ]
    if issue.code in {
        "PROPELLER_DIRECTION_MISMATCH",
        "PROPELLER_DIRECTION_PAIR_REQUIRED",
        "MOTOR_PERFORMANCE_CURVE_MISSING",
    }:
        return ["motor", "propeller"]
    if issue.code == "INSUFFICIENT_TOTAL_THRUST":
        return ["motor", "propeller", "battery"]
    if issue.code == "ESC_CURRENT_LIMIT":
        return ["esc", "motor"]
    if issue.code == "BATTERY_DISCHARGE_LIMIT":
        return ["battery"]
    if issue.code == "POWER_MODULE_CURRENT_LIMIT":
        return ["power_module"]
    if issue.code == "VOLTAGE_INCOMPATIBLE":
        return ["battery", "esc", "power_module"]
    if issue.code == "CG_OFFSET_WARNING":
        return ["frame", "battery", "payload"]
    return []


def _affected_mounts(
    aircraft: AircraftDefinition,
    issue: AssemblyIssue,
) -> list[MotorName]:
    if issue.code in {
        "PROPELLER_DIRECTION_MISMATCH",
        "PROPELLER_DIRECTION_PAIR_REQUIRED",
    }:
        return ["M1", "M2", "M3", "M4"]
    if issue.code in {
        "INSUFFICIENT_TOTAL_THRUST",
        "MOTOR_PERFORMANCE_CURVE_MISSING",
    }:
        return ["M1", "M2", "M3", "M4"]
    return []


def augment_validation(
    aircraft: AircraftDefinition,
    validation: AssemblyValidationResult,
) -> AssemblyValidationResult:
    """Attach UI location metadata without changing validation outcomes."""

    def enrich(issue: AssemblyIssue) -> AssemblyIssue:
        return issue.model_copy(
            update={
                "affected_slots": _affected_slots(aircraft, issue),
                "affected_mounts": _affected_mounts(aircraft, issue),
            }
        )

    return validation.model_copy(
        update={
            "blocking_errors": [
                enrich(issue) for issue in validation.blocking_errors
            ],
            "warnings": [enrich(issue) for issue in validation.warnings],
        }
    )
