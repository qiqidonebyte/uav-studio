from __future__ import annotations

from backend.p0_validation import augment_validation
from backend.schemas import AssemblyValidationResult
from backend.seed import build_seed_aircraft


def issue_codes(validation: AssemblyValidationResult) -> set[str]:
    return {issue.code for issue in validation.blocking_errors}


def test_650_with_15_inch_prop_does_not_add_visual_overlap_error() -> None:
    aircraft = build_seed_aircraft()
    validation = augment_validation(aircraft, AssemblyValidationResult())

    assert "PROPELLER_FRAME_OVERLAP" not in issue_codes(validation)


def test_450_with_14_inch_prop_adds_blocking_visual_overlap_error() -> None:
    aircraft = build_seed_aircraft().model_copy(
        update={"frame_id": 2, "propeller_id": 31}
    )
    validation = augment_validation(aircraft, AssemblyValidationResult())

    assert "PROPELLER_FRAME_OVERLAP" in issue_codes(validation)
    issue = next(
        item
        for item in validation.blocking_errors
        if item.code == "PROPELLER_FRAME_OVERLAP"
    )
    assert issue.severity == "error"
    assert issue.affected_slots == ["frame", "propeller"]
    assert issue.affected_mounts == ["M1", "M2", "M3", "M4"]
    assert "旋翼盘重叠" in issue.message


def test_visual_overlap_error_is_not_duplicated() -> None:
    aircraft = build_seed_aircraft().model_copy(
        update={"frame_id": 2, "propeller_id": 31}
    )
    first = augment_validation(aircraft, AssemblyValidationResult())
    second = augment_validation(aircraft, first)

    codes = [
        issue.code
        for issue in second.blocking_errors
        if issue.code == "PROPELLER_FRAME_OVERLAP"
    ]
    assert codes == ["PROPELLER_FRAME_OVERLAP"]
