from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    root / "backend" / "schemas.py",
    root / "backend" / "seed.py",
    root / "backend" / "experiments.py",
    root / "frontend" / "src" / "components" / "ComponentCard.vue",
    root / "frontend" / "src" / "components" / "DroneScene.vue",
    root / "frontend" / "src" / "three" / "AircraftRenderer.ts",
    root / "frontend" / "src" / "three" / "assetRegistry.ts",
    root / "frontend" / "src" / "types" / "visual-test.d.ts",
    root / "frontend" / "tests" / "p0-asset-contract.test.ts",
    root / "frontend" / "tests" / "p0-ui-contract.mjs",
    root / "frontend" / "tests" / "p0-scene-contract.mjs",
    root / "frontend" / "public" / "models" / "uav" / "v1_1" / "asset_manifest.json",
]
missing = [path.relative_to(root) for path in required if not path.exists()]
if missing:
    print("FAIL: missing required files after overlay")
    for path in missing:
        print(" -", path)
    raise SystemExit(1)
print("PASS: P0 Sprint 1 overlay files and existing asset manifest are present.")
