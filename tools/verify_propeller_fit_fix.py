from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "frontend" / "public" / "models" / "uav" / "v1_1"
MANIFEST = json.loads((MODEL_DIR / "asset_manifest.json").read_text(encoding="utf-8"))
checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    checks.append((name, bool(condition), detail))


def scene(name: str) -> trimesh.Scene:
    return trimesh.load(MODEL_DIR / name, force="scene")


for filename, expected in (
    ("prop_15_cw.glb", 0.381),
    ("prop_15_ccw.glb", 0.381),
    ("prop_14_cw.glb", 0.3556),
    ("prop_14_ccw.glb", 0.3556),
):
    s = scene(filename)
    vertices = np.vstack([g.vertices for g in s.geometry.values()])
    diameter = 2 * float(np.max(np.hypot(vertices[:, 0], vertices[:, 2])))
    check(f"{filename}: exact swept diameter", abs(diameter - expected) <= 0.0005, f"{diameter:.6f} m")
    names = set(s.geometry)
    check(f"{filename}: no duplicate nut/washer", not ({"nut", "washer", "prop_nut"} & names), str(sorted(names)))
    check(f"{filename}: annular hub exists", "hub_body" in names, "")

prop = scene("prop_15_ccw.glb")
for motor_file in ("motor_5010_360kv.glb", "motor_4008_500kv.glb"):
    motor = scene(motor_file)
    check(f"{motor_file}: owns prop nut", "prop_nut" in motor.geometry)
    check(f"{motor_file}: owns prop adapter", "prop_adapter" in motor.geometry)
    hub_top = float(prop.geometry["hub_body"].bounds[1][1]) + 0.064
    nut_bottom = float(motor.geometry["prop_nut"].bounds[0][1])
    check(f"{motor_file}: hub below nut", hub_top < nut_bottom, f"hub_top={hub_top:.6f}, nut_bottom={nut_bottom:.6f}")

hub = prop.geometry["hub_body"]
adapter = scene("motor_5010_360kv.glb").geometry["prop_adapter"]
hub_inner = float(np.min(np.hypot(hub.vertices[:,0], hub.vertices[:,2])))
adapter_outer = float(np.max(np.hypot(adapter.vertices[:,0], adapter.vertices[:,2])))
check("hub bore clears adapter", hub_inner > adapter_outer + 0.0003, f"{hub_inner:.6f} > {adapter_outer:.6f}")

component_map = MANIFEST["componentMap"]
fit_meta = (
    MANIFEST.get("fitContractVersion") == "1.0"
    and component_map["1"].get("motor_diagonal_m") == 0.65
    and component_map["2"].get("motor_diagonal_m") == 0.45
    and component_map["30"].get("swept_diameter_m") == 0.381
    and component_map["31"].get("swept_diameter_m") == 0.3556
)
check("manifest fit metadata", fit_meta)

clearance_650_15 = 0.65 / sqrt(2) - 0.381
clearance_450_14 = 0.45 / sqrt(2) - 0.3556
check("650 + 15in clears", clearance_650_15 > 0, f"{clearance_650_15*1000:.1f} mm")
check("450 + 14in is detected incompatible", clearance_450_14 < 0, f"{clearance_450_14*1000:.1f} mm")

p0 = (ROOT / "backend/p0_validation.py").read_text(encoding="utf-8")
assembly = (ROOT / "frontend/src/utils/assembly.ts").read_text(encoding="utf-8")
check("backend runtime issue wired", "PROPELLER_FRAME_OVERLAP" in p0 and "_visual_propeller_fit_issue" in p0)
check("frontend propeller step wired", "'PROPELLER_FRAME_OVERLAP'" in assembly)

failed = [item for item in checks if not item[1]]
for name, ok, detail in checks:
    suffix = f" :: {detail}" if detail else ""
    print(f"{'PASS' if ok else 'FAIL'}  {name}{suffix}")
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    sys.exit(1)
