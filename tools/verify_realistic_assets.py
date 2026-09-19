from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'frontend' / 'public' / 'models' / 'uav' / 'v1_1'
MANIFEST = json.loads((MODEL_DIR / 'asset_manifest.json').read_text(encoding='utf-8'))

EXPECTED = {
    'frame_650.glb': 4000,
    'frame_450.glb': 3500,
    'motor_5010_360kv.glb': 7000,
    'motor_4008_500kv.glb': 7000,
    'esc_30a.glb': 1000,
    'esc_40a.glb': 1000,
    'prop_15_cw.glb': 1400,
    'prop_15_ccw.glb': 1400,
    'prop_14_cw.glb': 1400,
    'prop_14_ccw.glb': 1400,
    'battery_6s_10000.glb': 750,
    'battery_6s_16000.glb': 750,
    'power_120a.glb': 350,
    'power_160a.glb': 350,
    'fc_v1.glb': 1000,
    'fc_v2.glb': 1000,
    'gnss_m8n.glb': 750,
    'payload_camera_300g.glb': 2400,
    'eduquad650_reference.glb': 50000,
}

checks = []
metrics = {}

def check(name: str, cond: bool, detail: str = '') -> None:
    checks.append((name, bool(cond), detail))

check('manifest assetVersion compatibility', MANIFEST.get('assetVersion') == '1.1.0', str(MANIFEST.get('assetVersion')))
check('manifest visual edition', MANIFEST.get('visualEdition') == 'EduQuad-650 Realistic Edition 2.0')
check('manifest meter units', MANIFEST.get('units') == 'meter')
check('manifest PBR declaration', 'PBR' in MANIFEST.get('materialSystem', ''))

for filename, min_triangles in EXPECTED.items():
    path = MODEL_DIR / filename
    check(f'{filename}: exists', path.exists())
    if not path.exists():
        continue
    raw = path.read_bytes()
    check(f'{filename}: glTF magic', raw[:4] == b'glTF')
    check(f'{filename}: glTF v2', int.from_bytes(raw[4:8], 'little') == 2)
    scene = trimesh.load(path, force='scene')
    triangles = sum(len(g.faces) for g in scene.geometry.values())
    pbr_materials = []
    material_names = set()
    for geom in scene.geometry.values():
        material = getattr(geom.visual, 'material', None)
        if isinstance(material, PBRMaterial):
            pbr_materials.append(material)
            if material.name:
                material_names.add(material.name)
    metrics[filename] = {
        'bytes': path.stat().st_size,
        'triangles': triangles,
        'geometry_nodes': len(scene.geometry),
        'pbr_materials': len(pbr_materials),
        'unique_materials': len(material_names),
        'bounds': scene.bounds.tolist(),
    }
    check(f'{filename}: triangle detail', triangles >= min_triangles, f'{triangles} >= {min_triangles}')
    check(f'{filename}: PBR materials', len(pbr_materials) == len(scene.geometry), f'{len(pbr_materials)}/{len(scene.geometry)}')
    check(f'{filename}: material variety', len(material_names) >= (2 if filename.startswith('prop_') else 3), str(sorted(material_names)))

# Key physical-size sanity checks in meters.
def extents(filename: str):
    scene = trimesh.load(MODEL_DIR / filename, force='scene')
    return scene.extents

f650 = extents('frame_650.glb')
motor = extents('motor_5010_360kv.glb')
prop = extents('prop_15_ccw.glb')
battery = extents('battery_6s_10000.glb')
check('frame650 overall size sane', 0.45 < max(f650[0], f650[2]) < 0.75, str(f650))
check('motor 5010 size sane', 0.05 < max(motor) < 0.14, str(motor))
check('15 inch prop diameter sane', 0.33 < prop[0] < 0.40, str(prop))
check('10Ah battery size sane', 0.18 < max(battery) < 0.28, str(battery))

# Direction-specific propeller files must be geometrically different.
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
for size in ('14', '15'):
    cw = MODEL_DIR / f'prop_{size}_cw.glb'
    ccw = MODEL_DIR / f'prop_{size}_ccw.glb'
    check(f'prop {size}: CW/CCW distinct', sha(cw) != sha(ccw))

# Thumbnails remain honest renders of the GLB geometry and large enough for UI cards.
thumbs = set()
for item in MANIFEST['componentMap'].values():
    if item.get('thumbnail'):
        thumbs.add(item['thumbnail'])
for rel in sorted(thumbs):
    path = MODEL_DIR / rel
    check(f'{rel}: exists', path.exists())
    if path.exists():
        with Image.open(path) as im:
            check(f'{rel}: >= 400px', min(im.size) >= 400, str(im.size))
            check(f'{rel}: PNG', im.format == 'PNG')

# Reference aircraft should be detailed but still browser-friendly.
ref_size = (MODEL_DIR / 'eduquad650_reference.glb').stat().st_size
check('reference aircraft under 2 MiB', ref_size < 2 * 1024 * 1024, str(ref_size))
folder_size = sum(p.stat().st_size for p in MODEL_DIR.rglob('*') if p.is_file())
check('entire realistic asset folder under 5 MiB', folder_size < 5 * 1024 * 1024, str(folder_size))

report_dir = ROOT / 'docs' / 'reports'
report_dir.mkdir(parents=True, exist_ok=True)
(report_dir / 'REALISTIC_ASSET_METRICS.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')

failed = [(n,d) for n,ok,d in checks if not ok]
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f' :: {detail}' if detail else ''))
print(f'\n{len(checks)-len(failed)}/{len(checks)} checks passed')
if failed:
    sys.exit(1)
