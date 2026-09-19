from __future__ import annotations

import json
from pathlib import Path

from backend.experiments import _enrich_legacy_visuals
from backend.schemas import Component, parse_component_parameters
from backend.seed import ASSET_MANIFEST_PATH, build_seed_catalog


def test_seed_components_expose_visual_metadata_from_manifest() -> None:
    manifest = json.loads(ASSET_MANIFEST_PATH.read_text(encoding="utf-8"))
    catalog = build_seed_catalog()

    assert set(catalog) == {int(value) for value in manifest["componentMap"]}

    for component_id, component in catalog.items():
        item = manifest["componentMap"][str(component_id)]
        assert component.visual is not None
        assert component.visual.asset_key == f"{item['type']}:{component_id}"
        assert component.visual.file == item.get("file")
        assert component.visual.cw_file == item.get("cw")
        assert component.visual.ccw_file == item.get("ccw")
        assert component.visual.thumbnail == item.get("thumbnail")


def test_seed_visual_files_exist_in_public_asset_directory() -> None:
    base = ASSET_MANIFEST_PATH.parent
    for component in build_seed_catalog().values():
        assert component.visual is not None
        for relative_path in (
            component.visual.file,
            component.visual.cw_file,
            component.visual.ccw_file,
            component.visual.thumbnail,
        ):
            if relative_path is not None:
                assert (base / relative_path).exists(), relative_path


def test_visual_storage_key_is_not_parsed_as_engineering_input() -> None:
    motor = build_seed_catalog()[10]
    parsed = parse_component_parameters(motor)
    assert parsed.kv == 360.0


def test_component_without_visual_remains_valid_for_unit_test_fixtures() -> None:
    component = Component(
        id=999,
        name="Fixture Motor",
        type="motor",
        mass_kg=0.1,
        parameters_json={
            "kv": 500.0,
            "profiles": [
                {
                    "battery_voltage_v": 22.2,
                    "propeller_id": 30,
                    "points": [
                        {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                        {"throttle": 1.0, "thrust_n": 10.0, "current_a": 10.0, "power_w": 222.0},
                    ],
                }
            ],
        },
    )
    assert component.visual is None


def test_legacy_replay_component_receives_visual_without_changing_engineering_data() -> None:
    legacy = Component(
        id=10,
        name="Historical Motor",
        type="motor",
        mass_kg=0.19,
        parameters_json={
            "kv": 360.0,
            "profiles": [
                {
                    "battery_voltage_v": 22.2,
                    "propeller_id": 30,
                    "points": [
                        {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                        {"throttle": 1.0, "thrust_n": 20.0, "current_a": 20.0, "power_w": 444.0},
                    ],
                }
            ],
        },
    )
    enriched = _enrich_legacy_visuals([legacy])[0]
    assert enriched.visual is not None
    assert enriched.visual.file == "motor_5010_360kv.glb"
    assert enriched.mass_kg == 0.19
    assert enriched.name == "Historical Motor"
    assert enriched.parameters_json == legacy.parameters_json


def test_components_api_exposes_first_class_visual_contract(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from backend.main import create_app

    database_path = tmp_path / "visual-contract.db"
    with TestClient(
        create_app(database_url=f"sqlite:///{database_path.as_posix()}")
    ) as client:
        response = client.get("/api/components", params={"type": "motor"})

    assert response.status_code == 200
    motor = next(item for item in response.json() if item["id"] == 10)
    assert motor["visual"]["asset_key"] == "motor:10"
    assert motor["visual"]["file"] == "motor_5010_360kv.glb"
    assert "_visual" not in motor["parameters_json"]
