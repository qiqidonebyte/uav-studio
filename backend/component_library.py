from __future__ import annotations

from copy import deepcopy
from typing import Callable, Iterator

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import ComponentRecord
from backend.schemas import (
    Component,
    ComponentType,
    ComponentVisual,
    parse_component_parameters,
)


class MutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class LibraryMetadata(MutableModel):
    notes: str = ""
    tags: list[str] = Field(default_factory=list)


class CompatibilityGroup(MutableModel):
    label: str
    component_ids: list[int] = Field(default_factory=list)
    note: str = ""


class LibraryComponent(MutableModel):
    id: int
    name: str
    type: ComponentType
    mass_kg: float
    parameters_json: dict = Field(default_factory=dict)
    visual: ComponentVisual | None = None
    library: LibraryMetadata = Field(default_factory=LibraryMetadata)
    compatibility: list[CompatibilityGroup] = Field(default_factory=list)


class ComponentUpdateRequest(MutableModel):
    name: str = Field(min_length=1, max_length=120)
    mass_kg: float = Field(gt=0.0, le=100.0)
    parameters_json: dict
    notes: str = ""
    tags: list[str] = Field(default_factory=list)


class ComponentCloneRequest(MutableModel):
    name: str = Field(min_length=1, max_length=120)


def _component_from_record(record: ComponentRecord) -> Component:
    return Component(
        id=record.id,
        name=record.name,
        type=record.type,
        mass_kg=record.mass_kg,
        parameters_json=record.parameters_json,
    )


def _library_metadata(parameters: dict | None) -> LibraryMetadata:
    raw = (parameters or {}).get("_library")
    if not isinstance(raw, dict):
        return LibraryMetadata()
    try:
        return LibraryMetadata.model_validate(raw)
    except Exception:
        return LibraryMetadata()


def _public_parameters(parameters: dict | None) -> dict:
    return {
        key: deepcopy(value)
        for key, value in (parameters or {}).items()
        if key not in {"_visual", "_library"}
    }


def _visual_from_parameters(parameters: dict | None) -> ComponentVisual | None:
    raw = (parameters or {}).get("_visual")
    if not isinstance(raw, dict):
        return None
    return ComponentVisual.model_validate(raw)


def _catalog(session: Session) -> dict[int, Component]:
    records = session.scalars(select(ComponentRecord).order_by(ComponentRecord.id)).all()
    return {record.id: _component_from_record(record) for record in records}


def _motor_profile_data(component: Component) -> list[dict]:
    profiles = component.parameters_json.get("profiles")
    return [item for item in profiles if isinstance(item, dict)] if isinstance(profiles, list) else []


def _numeric(parameters: dict, key: str) -> float | None:
    value = parameters.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def compatibility_for_component(
    component: Component,
    catalog: dict[int, Component],
) -> list[CompatibilityGroup]:
    groups: list[CompatibilityGroup] = []

    if component.type == "motor":
        profiles = _motor_profile_data(component)
        prop_ids = sorted({int(item["propeller_id"]) for item in profiles if isinstance(item.get("propeller_id"), int)})
        voltages = [float(item["battery_voltage_v"]) for item in profiles if isinstance(item.get("battery_voltage_v"), (int, float))]
        battery_ids: list[int] = []
        for candidate in catalog.values():
            if candidate.type != "battery":
                continue
            nominal = _numeric(candidate.parameters_json, "nominal_voltage_v")
            if nominal is not None and any(abs(nominal - voltage) <= 0.75 for voltage in voltages):
                battery_ids.append(candidate.id)
        groups.append(CompatibilityGroup(label="螺旋桨", component_ids=prop_ids, note="来自电机性能曲线"))
        groups.append(CompatibilityGroup(label="电池", component_ids=sorted(battery_ids), note="标称电压与性能曲线匹配"))

    elif component.type == "propeller":
        motor_ids = [
            candidate.id
            for candidate in catalog.values()
            if candidate.type == "motor"
            and any(item.get("propeller_id") == component.id for item in _motor_profile_data(candidate))
        ]
        groups.append(CompatibilityGroup(label="电机", component_ids=sorted(motor_ids), note="存在可用性能曲线"))

    elif component.type == "battery":
        nominal = _numeric(component.parameters_json, "nominal_voltage_v")
        motor_ids: list[int] = []
        esc_ids: list[int] = []
        if nominal is not None:
            for candidate in catalog.values():
                if candidate.type == "motor" and any(
                    abs(float(item.get("battery_voltage_v", -999)) - nominal) <= 0.75
                    for item in _motor_profile_data(candidate)
                ):
                    motor_ids.append(candidate.id)
                if candidate.type == "esc":
                    vmin = _numeric(candidate.parameters_json, "voltage_min_v")
                    vmax = _numeric(candidate.parameters_json, "voltage_max_v")
                    if vmin is not None and vmax is not None and vmin <= nominal <= vmax:
                        esc_ids.append(candidate.id)
        groups.append(CompatibilityGroup(label="电机", component_ids=sorted(motor_ids), note="存在该电压性能数据"))
        groups.append(CompatibilityGroup(label="电调", component_ids=sorted(esc_ids), note="电压范围兼容"))

    elif component.type == "esc":
        max_current = _numeric(component.parameters_json, "max_current_a")
        vmin = _numeric(component.parameters_json, "voltage_min_v")
        vmax = _numeric(component.parameters_json, "voltage_max_v")
        motor_ids: list[int] = []
        battery_ids: list[int] = []
        for candidate in catalog.values():
            if candidate.type == "motor" and max_current is not None:
                profile_currents = [
                    max(
                        [float(point.get("current_a", 0.0)) for point in item.get("points", []) if isinstance(point, dict)]
                        or [0.0]
                    )
                    for item in _motor_profile_data(candidate)
                ]
                if profile_currents and max(profile_currents) <= max_current:
                    motor_ids.append(candidate.id)
            if candidate.type == "battery" and vmin is not None and vmax is not None:
                nominal = _numeric(candidate.parameters_json, "nominal_voltage_v")
                if nominal is not None and vmin <= nominal <= vmax:
                    battery_ids.append(candidate.id)
        groups.append(CompatibilityGroup(label="电机", component_ids=sorted(motor_ids), note="最大电流不超过电调能力"))
        groups.append(CompatibilityGroup(label="电池", component_ids=sorted(battery_ids), note="标称电压在电调范围内"))

    elif component.type == "power_module":
        max_current = _numeric(component.parameters_json, "max_current_a")
        vmin = _numeric(component.parameters_json, "voltage_min_v")
        vmax = _numeric(component.parameters_json, "voltage_max_v")
        battery_ids: list[int] = []
        for candidate in catalog.values():
            if candidate.type != "battery":
                continue
            nominal = _numeric(candidate.parameters_json, "nominal_voltage_v")
            continuous = _numeric(candidate.parameters_json, "max_continuous_current_a")
            voltage_ok = nominal is not None and vmin is not None and vmax is not None and vmin <= nominal <= vmax
            current_ok = max_current is None or continuous is None or continuous <= max_current * 1.5
            if voltage_ok and current_ok:
                battery_ids.append(candidate.id)
        groups.append(CompatibilityGroup(label="电池", component_ids=sorted(battery_ids), note="电压/电流范围可用"))

    elif component.type == "frame":
        groups.append(CompatibilityGroup(
            label="标准槽位",
            component_ids=[item.id for item in catalog.values() if item.type in {"motor", "esc", "battery", "power_module", "flight_controller", "gnss", "payload"}],
            note="V1 Quad-X 教学机架使用标准安装槽",
        ))

    elif component.type in {"flight_controller", "gnss"}:
        groups.append(CompatibilityGroup(
            label="机架",
            component_ids=sorted(item.id for item in catalog.values() if item.type == "frame"),
            note="使用标准飞控/GNSS安装点",
        ))

    elif component.type == "payload":
        mount = component.parameters_json.get("mount", "bottom_center")
        groups.append(CompatibilityGroup(
            label="机架",
            component_ids=sorted(item.id for item in catalog.values() if item.type == "frame"),
            note=f"使用 {mount} 载荷安装点",
        ))

    return groups


def library_item(record: ComponentRecord, catalog: dict[int, Component]) -> LibraryComponent:
    component = _component_from_record(record)
    return LibraryComponent(
        id=component.id,
        name=component.name,
        type=component.type,
        mass_kg=component.mass_kg,
        parameters_json=_public_parameters(record.parameters_json),
        visual=_visual_from_parameters(record.parameters_json),
        library=_library_metadata(record.parameters_json),
        compatibility=compatibility_for_component(component, catalog),
    )


def list_library_components(
    session: Session,
    *,
    component_type: ComponentType | None = None,
    search: str = "",
) -> list[LibraryComponent]:
    records = session.scalars(select(ComponentRecord).order_by(ComponentRecord.type, ComponentRecord.id)).all()
    catalog = {record.id: _component_from_record(record) for record in records}
    normalized = search.strip().lower()
    result: list[LibraryComponent] = []
    for record in records:
        if component_type is not None and record.type != component_type:
            continue
        if normalized and normalized not in record.name.lower() and normalized not in str(record.id):
            continue
        result.append(library_item(record, catalog))
    return result


def get_library_component(session: Session, component_id: int) -> LibraryComponent:
    record = session.get(ComponentRecord, component_id)
    if record is None:
        raise KeyError(component_id)
    return library_item(record, _catalog(session))


def clone_library_component(
    session: Session,
    component_id: int,
    *,
    name: str,
) -> LibraryComponent:
    source = session.get(ComponentRecord, component_id)
    if source is None:
        raise KeyError(component_id)
    parameters = deepcopy(source.parameters_json or {})
    metadata = _library_metadata(parameters)
    parameters["_library"] = LibraryMetadata(
        notes=(metadata.notes + ("\n" if metadata.notes else "") + f"复制自组件 #{component_id}").strip(),
        tags=list(dict.fromkeys([*metadata.tags, "自定义"])),
    ).model_dump(mode="json")
    record = ComponentRecord(
        name=name.strip(),
        type=source.type,
        mass_kg=source.mass_kg,
        parameters_json=parameters,
    )
    session.add(record)
    session.flush()
    visual = parameters.get("_visual")
    if isinstance(visual, dict):
        updated_parameters = deepcopy(parameters)
        updated_visual = deepcopy(visual)
        updated_visual["asset_key"] = f"{source.type}:custom-{record.id}"
        updated_parameters["_visual"] = updated_visual
        record.parameters_json = updated_parameters
    session.commit()
    session.refresh(record)
    return get_library_component(session, record.id)


def update_library_component(
    session: Session,
    component_id: int,
    command: ComponentUpdateRequest,
) -> LibraryComponent:
    record = session.get(ComponentRecord, component_id)
    if record is None:
        raise KeyError(component_id)

    stored = deepcopy(record.parameters_json or {})
    engineering = deepcopy(command.parameters_json)
    if any(key.startswith("_") for key in engineering):
        raise ValueError("工程参数不能使用以下划线开头的保留字段")
    if "_visual" in stored:
        engineering["_visual"] = deepcopy(stored["_visual"])
    engineering["_library"] = LibraryMetadata(
        notes=command.notes.strip(),
        tags=list(dict.fromkeys(tag.strip() for tag in command.tags if tag.strip())),
    ).model_dump(mode="json")

    candidate = Component(
        id=record.id,
        name=command.name.strip(),
        type=record.type,
        mass_kg=command.mass_kg,
        parameters_json=engineering,
    )
    # Fail before persistence if the edited engineering contract is invalid.
    parse_component_parameters(candidate)

    record.name = candidate.name
    record.mass_kg = candidate.mass_kg
    record.parameters_json = engineering
    session.commit()
    session.refresh(record)
    return get_library_component(session, record.id)


def register_component_library_routes(
    app: FastAPI,
    get_db: Callable[..., Iterator[Session]],
) -> None:
    @app.get("/api/library/components", response_model=list[LibraryComponent])
    def library_components(
        component_type: ComponentType | None = Query(default=None, alias="type"),
        search: str = Query(default="", max_length=120),
        session: Session = Depends(get_db),
    ) -> list[LibraryComponent]:
        return list_library_components(session, component_type=component_type, search=search)

    @app.get("/api/library/components/{component_id}", response_model=LibraryComponent)
    def library_component_detail(
        component_id: int,
        session: Session = Depends(get_db),
    ) -> LibraryComponent:
        try:
            return get_library_component(session, component_id)
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组件不存在") from error

    @app.post(
        "/api/library/components/{component_id}/clone",
        response_model=LibraryComponent,
        status_code=status.HTTP_201_CREATED,
    )
    def clone_component(
        component_id: int,
        command: ComponentCloneRequest,
        session: Session = Depends(get_db),
    ) -> LibraryComponent:
        try:
            return clone_library_component(session, component_id, name=command.name)
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组件不存在") from error

    @app.put("/api/library/components/{component_id}", response_model=LibraryComponent)
    def update_component(
        component_id: int,
        command: ComponentUpdateRequest,
        session: Session = Depends(get_db),
    ) -> LibraryComponent:
        try:
            return update_library_component(session, component_id, command)
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组件不存在") from error
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
