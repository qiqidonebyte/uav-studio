from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

import numpy as np
import pytest
import trimesh

from backend.propeller_fit import (
    fit_from_asset_manifest,
    rotor_disc_clearance_m,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "frontend" / "public" / "models" / "uav" / "v1_1"
MANIFEST = json.loads((MODEL_DIR / "asset_manifest.json").read_text(encoding="utf-8"))
PROP_MOUNT_Y = 0.064


def load_scene(name: str) -> trimesh.Scene:
    return trimesh.load(MODEL_DIR / name, force="scene")


def horizontal_radius(scene: trimesh.Scene) -> float:
    vertices = np.vstack([geometry.vertices for geometry in scene.geometry.values()])
    return float(np.max(np.hypot(vertices[:, 0], vertices[:, 2])))


@pytest.mark.parametrize(
    ("filename", "diameter_m"),
    [
        ("prop_15_cw.glb", 15.0 * 0.0254),
        ("prop_15_ccw.glb", 15.0 * 0.0254),
        ("prop_14_cw.glb", 14.0 * 0.0254),
        ("prop_14_ccw.glb", 14.0 * 0.0254),
    ],
)
def test_visual_propeller_swept_diameter_matches_declared_size(
    filename: str,
    diameter_m: float,
) -> None:
    scene = load_scene(filename)
    actual = 2.0 * horizontal_radius(scene)
    assert actual == pytest.approx(diameter_m, abs=0.0005)


def test_propeller_asset_has_one_owner_for_fasteners_and_a_real_center_bore() -> None:
    prop = load_scene("prop_15_ccw.glb")
    motor = load_scene("motor_5010_360kv.glb")

    names = set(prop.geometry)
    assert "nut" not in names
    assert "washer" not in names
    assert "prop_nut" not in names
    assert {"hub_body", "hub_reinforcement", "blade_0", "blade_1"} <= names
    assert {"prop_adapter", "prop_nut"} <= set(motor.geometry)

    hub = prop.geometry["hub_body"]
    adapter = motor.geometry["prop_adapter"]
    hub_radii = np.hypot(hub.vertices[:, 0], hub.vertices[:, 2])
    adapter_radii = np.hypot(adapter.vertices[:, 0], adapter.vertices[:, 2])

    assert float(hub_radii.min()) > float(adapter_radii.max()) + 0.0003


@pytest.mark.parametrize("motor_file", ["motor_5010_360kv.glb", "motor_4008_500kv.glb"])
def test_standardized_prop_mount_keeps_hub_below_retaining_nut(motor_file: str) -> None:
    prop = load_scene("prop_15_ccw.glb")
    motor = load_scene(motor_file)

    hub_top = float(prop.geometry["hub_body"].bounds[1][1]) + PROP_MOUNT_Y
    nut_bottom = float(motor.geometry["prop_nut"].bounds[0][1])
    assert hub_top < nut_bottom

    # Blade roots may be above/below the nut axially due to pitch, but they must
    # remain radially outside the nut so the meshes cannot intersect.
    nut_radius = float(
        np.max(
            np.hypot(
                motor.geometry["prop_nut"].vertices[:, 0],
                motor.geometry["prop_nut"].vertices[:, 2],
            )
        )
    )
    for blade_name in ("blade_0", "blade_1"):
        blade = prop.geometry[blade_name]
        blade_radius = float(np.min(np.hypot(blade.vertices[:, 0], blade.vertices[:, 2])))
        assert blade_radius > nut_radius + 0.005


def test_known_650_frame_and_15_inch_propeller_have_positive_tip_clearance() -> None:
    fit = fit_from_asset_manifest(MANIFEST, frame_id=1, propeller_id=30)
    assert fit is not None
    assert fit.overlaps is False
    assert fit.clearance_m == pytest.approx(0.65 / sqrt(2.0) - 0.381)
    assert fit.clearance_m > 0.07


def test_known_450_frame_and_14_inch_propeller_are_physically_incompatible() -> None:
    fit = fit_from_asset_manifest(MANIFEST, frame_id=2, propeller_id=31)
    assert fit is not None
    assert fit.overlaps is True
    assert fit.clearance_m < -0.03


def test_fit_math_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError):
        rotor_disc_clearance_m(0.0, 0.3)
    with pytest.raises(ValueError):
        rotor_disc_clearance_m(0.65, 0.0)
