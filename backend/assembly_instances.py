from __future__ import annotations

from collections import defaultdict

from backend.schemas import (
    AircraftDefinition,
    AssemblyInstance,
    ComponentType,
)

MOUNT_IDS_BY_SLOT: dict[ComponentType, tuple[str, ...]] = {
    "frame": ("frame:main",),
    "motor": ("motor:M1", "motor:M2", "motor:M3", "motor:M4"),
    "esc": ("esc:M1", "esc:M2", "esc:M3", "esc:M4"),
    "propeller": (
        "propeller:M1",
        "propeller:M2",
        "propeller:M3",
        "propeller:M4",
    ),
    "battery": ("battery:main",),
    "power_module": ("power_module:main",),
    "flight_controller": ("flight_controller:main",),
    "gnss": ("gnss:main",),
    "payload": ("payload:main",),
}

SLOT_FIELD: dict[ComponentType, str] = {
    "frame": "frame_id",
    "motor": "motor_id",
    "esc": "esc_id",
    "propeller": "propeller_id",
    "battery": "battery_id",
    "power_module": "power_module_id",
    "flight_controller": "flight_controller_id",
    "gnss": "gnss_id",
    "payload": "payload_id",
}

REQUIRED_PHYSICAL_SLOTS: tuple[ComponentType, ...] = (
    "frame",
    "motor",
    "esc",
    "propeller",
    "battery",
    "power_module",
    "flight_controller",
)

OPTIONAL_PHYSICAL_SLOTS: tuple[ComponentType, ...] = ("gnss", "payload")


def component_id_for_slot(
    aircraft: AircraftDefinition,
    slot: ComponentType,
) -> int | None:
    value = getattr(aircraft, SLOT_FIELD[slot])
    return value if isinstance(value, int) else None


def default_assembly_instances(
    aircraft: AircraftDefinition,
) -> list[AssemblyInstance]:
    """Create a fully assembled physical state from legacy slot-level IDs."""

    instances: list[AssemblyInstance] = []
    for slot, mount_ids in MOUNT_IDS_BY_SLOT.items():
        component_id = component_id_for_slot(aircraft, slot)
        if component_id is None:
            continue
        instances.extend(
            AssemblyInstance(
                mount_id=mount_id,
                slot=slot,
                component_id=component_id,
            )
            for mount_id in mount_ids
        )
    return instances


def normalized_assembly_instances(
    aircraft: AircraftDefinition,
) -> list[AssemblyInstance]:
    """Use explicit physical state when present, otherwise legacy full state."""

    if "assembly_instances" in aircraft.model_fields_set:
        return list(aircraft.assembly_instances)
    return default_assembly_instances(aircraft)


def instances_by_mount(
    aircraft: AircraftDefinition,
) -> dict[str, AssemblyInstance]:
    return {
        item.mount_id: item
        for item in normalized_assembly_instances(aircraft)
    }


def missing_required_mount_ids(
    aircraft: AircraftDefinition,
) -> list[str]:
    mounted = instances_by_mount(aircraft)
    missing: list[str] = []
    for slot in REQUIRED_PHYSICAL_SLOTS:
        if component_id_for_slot(aircraft, slot) is None:
            # The base engineering validator already reports missing catalog slot.
            continue
        for mount_id in MOUNT_IDS_BY_SLOT[slot]:
            if mount_id not in mounted:
                missing.append(mount_id)
    return missing


def pending_optional_mount_ids(
    aircraft: AircraftDefinition,
) -> list[str]:
    mounted = instances_by_mount(aircraft)
    pending: list[str] = []
    for slot in OPTIONAL_PHYSICAL_SLOTS:
        if component_id_for_slot(aircraft, slot) is None:
            continue
        for mount_id in MOUNT_IDS_BY_SLOT[slot]:
            if mount_id not in mounted:
                pending.append(mount_id)
    return pending


def inconsistent_instances(
    aircraft: AircraftDefinition,
) -> list[str]:
    """Return physical mounts whose slot or component disagrees with catalog state."""

    problems: list[str] = []
    allowed_mounts = {
        mount_id: slot
        for slot, mount_ids in MOUNT_IDS_BY_SLOT.items()
        for mount_id in mount_ids
    }
    seen: set[str] = set()

    for instance in aircraft.assembly_instances:
        expected_slot = allowed_mounts.get(instance.mount_id)
        if expected_slot is None:
            problems.append(instance.mount_id)
            continue
        if instance.mount_id in seen:
            problems.append(instance.mount_id)
            continue
        seen.add(instance.mount_id)
        if instance.slot != expected_slot:
            problems.append(instance.mount_id)
            continue
        selected_component = component_id_for_slot(aircraft, instance.slot)
        if selected_component != instance.component_id:
            problems.append(instance.mount_id)

    return sorted(set(problems))


def mount_completion_by_slot(
    aircraft: AircraftDefinition,
) -> dict[ComponentType, tuple[int, int]]:
    mounted = instances_by_mount(aircraft)
    result: dict[ComponentType, tuple[int, int]] = {}
    for slot, mount_ids in MOUNT_IDS_BY_SLOT.items():
        result[slot] = (
            sum(1 for mount_id in mount_ids if mount_id in mounted),
            len(mount_ids),
        )
    return result
