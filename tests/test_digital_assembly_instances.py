from __future__ import annotations

from backend.assembly_instances import (
    default_assembly_instances,
    inconsistent_instances,
    missing_required_mount_ids,
    mount_completion_by_slot,
    normalized_assembly_instances,
)
from backend.p0_validation import augment_validation
from backend.schemas import (
    AircraftDefinition,
    AssemblyInstance,
    AssemblyValidationResult,
)


def legacy_aircraft() -> AircraftDefinition:
    # Deliberately omit assembly_instances to exercise backwards compatibility.
    return AircraftDefinition(
        id=1,
        name="EduQuad-650",
        frame_id=1,
        motor_id=10,
        esc_id=20,
        propeller_id=30,
        battery_id=40,
        power_module_id=50,
        flight_controller_id=60,
        gnss_id=70,
        payload_id=80,
    )


def explicit_aircraft() -> AircraftDefinition:
    legacy = legacy_aircraft()
    return legacy.model_copy(
        update={"assembly_instances": default_assembly_instances(legacy)}
    )


def test_legacy_aircraft_expands_to_full_physical_assembly() -> None:
    aircraft = legacy_aircraft()
    instances = normalized_assembly_instances(aircraft)

    assert len(instances) == 18
    assert {item.mount_id for item in instances if item.slot == "motor"} == {
        "motor:M1",
        "motor:M2",
        "motor:M3",
        "motor:M4",
    }
    assert mount_completion_by_slot(aircraft)["motor"] == (4, 4)
    assert mount_completion_by_slot(aircraft)["esc"] == (4, 4)
    assert mount_completion_by_slot(aircraft)["propeller"] == (4, 4)


def test_explicit_missing_motor_mount_is_detected() -> None:
    aircraft = explicit_aircraft()
    aircraft = aircraft.model_copy(
        update={
            "assembly_instances": [
                item
                for item in aircraft.assembly_instances
                if item.mount_id != "motor:M2"
            ]
        }
    )

    assert missing_required_mount_ids(aircraft) == ["motor:M2"]

    validation = augment_validation(
        aircraft,
        AssemblyValidationResult(),
    )
    issue = next(
        item
        for item in validation.blocking_errors
        if item.code == "ASSEMBLY_MOUNT_INCOMPLETE"
    )
    assert issue.affected_mount_ids == ["motor:M2"]
    assert issue.affected_slots == ["motor"]
    assert validation.passed is False


def test_physical_instance_component_mismatch_is_blocking() -> None:
    aircraft = explicit_aircraft()
    updated = []
    for item in aircraft.assembly_instances:
        if item.mount_id == "motor:M1":
            updated.append(
                AssemblyInstance(
                    mount_id=item.mount_id,
                    slot="motor",
                    component_id=11,
                )
            )
        else:
            updated.append(item)
    aircraft = aircraft.model_copy(update={"assembly_instances": updated})

    assert inconsistent_instances(aircraft) == ["motor:M1"]

    validation = augment_validation(
        aircraft,
        AssemblyValidationResult(),
    )
    issue = next(
        item
        for item in validation.blocking_errors
        if item.code == "ASSEMBLY_INSTANCE_MISMATCH"
    )
    assert issue.affected_mount_ids == ["motor:M1"]



def test_explicit_empty_physical_state_is_not_treated_as_legacy_full_state() -> None:
    legacy = legacy_aircraft()
    explicit_empty = legacy.model_copy(update={"assembly_instances": []})

    assert normalized_assembly_instances(explicit_empty) == []
    missing = missing_required_mount_ids(explicit_empty)
    assert "frame:main" in missing
    assert "motor:M1" in missing
    assert "flight_controller:main" in missing

def test_optional_selected_component_can_be_physically_pending_without_blocking() -> None:
    aircraft = explicit_aircraft()
    aircraft = aircraft.model_copy(
        update={
            "assembly_instances": [
                item
                for item in aircraft.assembly_instances
                if item.mount_id != "gnss:main"
            ]
        }
    )

    validation = augment_validation(
        aircraft,
        AssemblyValidationResult(),
    )
    assert validation.passed is True
    warning = next(
        item
        for item in validation.warnings
        if item.code == "OPTIONAL_ASSEMBLY_MOUNT_PENDING"
    )
    assert warning.affected_mount_ids == ["gnss:main"]
