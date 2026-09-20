from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks: list[tuple[str, bool]] = []


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))


schemas = read("backend/schemas.py")
models = read("backend/models.py")
database = read("backend/database.py")
main = read("backend/main.py")
instances = read("backend/assembly_instances.py")
validation = read("backend/p0_validation.py")
types = read("frontend/src/types/aircraft.ts")
semantics = read("frontend/src/three/assemblySemantics.ts")
transforms = read("frontend/src/three/assemblyTransforms.ts")
renderer = read("frontend/src/three/AircraftRenderer.ts")
scene = read("frontend/src/components/DroneScene.vue")
store = read("frontend/src/stores/assembly.ts")
assembly = read("frontend/src/views/Assembly.vue")
card = read("frontend/src/components/ComponentCard.vue")
probe = read("frontend/src/types/visual-test.d.ts")
scene_test = read("frontend/tests/p0-scene-contract.mjs")
e2e = read("frontend/tests/e2e-digital-assembly.mjs")

check("backend AssemblyInstance schema", "class AssemblyInstance(BaseModel)" in schemas)
check("AircraftDefinition physical state", "assembly_instances: list[AssemblyInstance]" in schemas)
check("SQLite physical-state column", "assembly_instances_json" in models)
check("additive migration", "ADD COLUMN assembly_instances_json JSON" in database)
check("legacy default instances", "default_assembly_instances" in instances)
check("required physical mount validation", "ASSEMBLY_MOUNT_INCOMPLETE" in validation)
check("instance consistency validation", "ASSEMBLY_INSTANCE_MISMATCH" in validation)
check("API reads physical state", "record.assembly_instances_json" in main)
check("API persists physical state", "physical_instances" in main)

check("frontend AssemblyInstance contract", "export interface AssemblyInstance" in types)
check("18-mount semantic contract", "motor:M1" in semantics and "payload:main" in semantics)
check("frame-derived mounts", "motor_diagonal_m" in semantics and "buildMountPoints" in semantics)
check("slot-scoped physical instances", "replaceSlotInstances" in semantics)
check("rotor disc collision", "ROTOR_DISC_COLLISION" in semantics)
check("battery envelope", "BATTERY_ENVELOPE_EXCEEDED" in semantics)
check("single datum transform", "composeAssemblyPosition" in transforms)

check("renderer mount IDs", "mountId: string" in renderer)
check("renderer independent part snapshots", "partInstancesSnapshot()" in renderer)
check("renderer install progress", "setInstallationProgress" in renderer)
check("renderer unified transform", "composeAssemblyPosition(" in renderer)
check("renderer mount picking", "mountForObject(" in renderer)

check("scene mount hotspots", 'data-testid="assembly-mount-hotspot"' in scene)
check("real-GLB ghost uses selected candidate", "mountedId ?? selectedId" in renderer and "hoveredMountId" in scene)
check("scene snap install event", "install-at-mount" in scene)
check("scene install animation", "advanceInstallationAnimation" in scene)
check("scene detach animation", "startRemovalAnimationIfNeeded" in scene and "mode: 'remove'" in scene)
check("scene spatial rotor overlay", "CircleGeometry(radius, 64)" in scene)
check("scene battery envelope overlay", "batteryBayDimensions" in scene)
check("scene mount picking", "select-mount" in scene)
check("scene diagnostics event", "spatial-diagnostics" in scene)

check("store constrained assembly session", "beginMountAssembly" in store)
check("store per-mount installation", "installAtMount" in store)
check("store per-mount removal", "removeMount" in store)
check("store removal persistence ordering", "lastRemoval" in store and "setTimeout(resolve, 380)" in store)
check("store quick-config compatibility", "replaceSlotInstances" in store)

check("component card 3D action", 'data-testid="component-3d-assemble"' in card)
check("assembly session UI", 'data-testid="assembly-session-card"' in assembly)
check("mount inspector UI", 'data-testid="mount-inspector"' in assembly)
check("space engineering UI", "空间工程检查" in assembly)
check("issue focus integration", "focusIssue" in assembly)

check("visual probe mount points", "mountPoints:" in probe)
check("visual probe part instances", "partInstances:" in probe)
check("P0 mount contract", "P0-SCENE-020" in scene_test)
check("P0 part instance contract", "P0-SCENE-021" in scene_test)
check("full E2E mount workflow", "Ghost/Snap assembly" in e2e)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    sys.exit(1)
