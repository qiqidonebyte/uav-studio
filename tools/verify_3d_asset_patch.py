from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
base = root / 'frontend' / 'public' / 'models' / 'uav' / 'v1_1'
manifest = json.loads((base / 'asset_manifest.json').read_text(encoding='utf-8'))
missing = []
for item in manifest['componentMap'].values():
    for key in ('file', 'cw', 'ccw', 'thumbnail'):
        value = item.get(key)
        if value and not (base / value).exists():
            missing.append(value)
for path in [
    root/'frontend/src/three/AircraftRenderer.ts',
    root/'frontend/src/three/assetRegistry.ts',
    root/'frontend/src/three/modelLoader.ts',
    root/'frontend/src/components/DroneScene.vue',
]:
    if not path.exists(): missing.append(str(path.relative_to(root)))
if missing:
    print('FAIL: missing files')
    for item in missing: print(' -', item)
    raise SystemExit(1)
print('PASS: 3D Asset System V1.1 files are complete.')
