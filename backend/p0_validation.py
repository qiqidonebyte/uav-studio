from __future__ import annotations

import json
from pathlib import Path

from backend.propeller_fit import fit_from_asset_manifest
from backend.assembly_instances import (
    inconsistent_instances,
    missing_required_mount_ids,
    pending_optional_mount_ids,
)
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

ASSET_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "public"
    / "models"
    / "uav"
    / "v1_1"
    / "asset_manifest.json"
)


def _load_asset_manifest() -> dict:
    try:
        payload = json.loads(ASSET_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


_ASSET_MANIFEST = _load_asset_manifest()


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
    if issue.code == "PROPELLER_FRAME_OVERLAP":
        return ["frame", "propeller"]
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
        "PROPELLER_FRAME_OVERLAP",
    }:
        return ["M1", "M2", "M3", "M4"]
    if issue.code in {
        "INSUFFICIENT_TOTAL_THRUST",
        "MOTOR_PERFORMANCE_CURVE_MISSING",
    }:
        return ["M1", "M2", "M3", "M4"]
    return []


def _visual_propeller_fit_issue(
    aircraft: AircraftDefinition,
) -> AssemblyIssue | None:
    fit = fit_from_asset_manifest(
        _ASSET_MANIFEST,
        aircraft.frame_id,
        aircraft.propeller_id,
    )
    if fit is None or not fit.overlaps:
        return None

    overlap_mm = -fit.clearance_m * 1000.0
    spacing_mm = fit.adjacent_motor_spacing_m * 1000.0
    diameter_mm = fit.propeller_diameter_m * 1000.0
    return AssemblyIssue(
        code="PROPELLER_FRAME_OVERLAP",
        severity="error",
        message=(
            "机架与螺旋桨尺寸不兼容："
            f"相邻电机间距 {spacing_mm:.1f} mm，"
            f"桨盘直径 {diameter_mm:.1f} mm，"
            f"旋翼盘重叠约 {overlap_mm:.1f} mm"
        ),
        affected_slots=["frame", "propeller"],
        affected_mounts=["M1", "M2", "M3", "M4"],
    )



def _physical_assembly_issues(
    aircraft: AircraftDefinition,
) -> tuple[list[AssemblyIssue], list[AssemblyIssue]]:
    errors: list[AssemblyIssue] = []
    warnings: list[AssemblyIssue] = []

    inconsistent = inconsistent_instances(aircraft)
    if inconsistent:
        affected_slots = sorted(
            {
                mount_id.split(":", 1)[0]
                for mount_id in inconsistent
                if ":" in mount_id
            }
        )
        errors.append(
            AssemblyIssue(
                code="ASSEMBLY_INSTANCE_MISMATCH",
                severity="error",
                message=(
                    "3D 装配实例与当前组件选择不一致："
                    + "、".join(inconsistent)
                ),
                affected_slots=affected_slots,
                affected_mount_ids=inconsistent,
            )
        )

    missing = missing_required_mount_ids(aircraft)
    if missing:
        affected_slots = sorted(
            {
                mount_id.split(":", 1)[0]
                for mount_id in missing
                if ":" in mount_id
            }
        )
        errors.append(
            AssemblyIssue(
                code="ASSEMBLY_MOUNT_INCOMPLETE",
                severity="error",
                message=(
                    "物理装配尚未完成："
                    + "、".join(missing)
                    + "。请在 3D 装配视图中完成安装。"
                ),
                affected_slots=affected_slots,
                affected_mount_ids=missing,
            )
        )

    optional = pending_optional_mount_ids(aircraft)
    if optional:
        affected_slots = sorted(
            {
                mount_id.split(":", 1)[0]
                for mount_id in optional
                if ":" in mount_id
            }
        )
        warnings.append(
            AssemblyIssue(
                code="OPTIONAL_ASSEMBLY_MOUNT_PENDING",
                severity="warning",
                message=(
                    "已选择但尚未物理安装的可选组件："
                    + "、".join(optional)
                ),
                affected_slots=affected_slots,
                affected_mount_ids=optional,
            )
        )
    return errors, warnings


def augment_validation(
    aircraft: AircraftDefinition,
    validation: AssemblyValidationResult,
) -> AssemblyValidationResult:
    """Attach UI location metadata and checked-in visual fit constraints."""

    def enrich(issue: AssemblyIssue) -> AssemblyIssue:
        return issue.model_copy(
            update={
                "affected_slots": (
                    issue.affected_slots
                    if issue.affected_slots
                    else _affected_slots(aircraft, issue)
                ),
                "affected_mounts": (
                    issue.affected_mounts
                    if issue.affected_mounts
                    else _affected_mounts(aircraft, issue)
                ),
                "affected_mount_ids": list(issue.affected_mount_ids),
            }
        )

    blocking_errors = [
        enrich(issue) for issue in validation.blocking_errors
    ]
    physical_errors, physical_warnings = _physical_assembly_issues(aircraft)
    for issue in physical_errors:
        if all(existing.code != issue.code for existing in blocking_errors):
            blocking_errors.append(issue)

    fit_issue = _visual_propeller_fit_issue(aircraft)
    if (
        fit_issue is not None
        and all(issue.code != fit_issue.code for issue in blocking_errors)
    ):
        blocking_errors.append(fit_issue)

    return validation.model_copy(
        update={
            "blocking_errors": blocking_errors,
            "warnings": (
                [enrich(issue) for issue in validation.warnings]
                + physical_warnings
            ),
        }
    )
