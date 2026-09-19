from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks: list[tuple[str, bool]] = []

def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))

drone = (ROOT / 'frontend/src/components/DroneScene.vue').read_text(encoding='utf-8')
renderer = (ROOT / 'frontend/src/three/AircraftRenderer.ts').read_text(encoding='utf-8')
math = (ROOT / 'frontend/src/three/explodedView.ts').read_text(encoding='utf-8')
labels = (ROOT / 'frontend/src/three/explodedLabels.ts').read_text(encoding='utf-8')
layout = (ROOT / 'frontend/src/three/explodedLabelLayout.ts').read_text(encoding='utf-8')
scene_test = (ROOT / 'frontend/tests/p0-scene-contract.mjs').read_text(encoding='utf-8')
capture = (ROOT / 'frontend/tests/p0-visual-capture.mjs').read_text(encoding='utf-8')

check('toolbar: assembled', 'data-testid="assembly-view-assembled"' in drone)
check('toolbar: exploded', 'data-testid="assembly-view-exploded"' in drone)
check('exploded hint', 'data-testid="exploded-view-hint"' in drone)
check('animated transition', 'Math.exp(-dt * 6.5)' in drone)
check('renderer receives explosion progress', 'aircraftRenderer.setExplodedProgress(next)' in drone)
check('frame remains datum', "case 'frame':" in math)
check('propeller hierarchy', "case 'propeller':" in math and '0.24, 0.30' in math)
check('motor hierarchy', "case 'motor':" in math and '0.17, 0.11' in math)
check('battery moves downward', "case 'battery':" in math and 'y: -0.31' in math)
check('GNSS moves upward', "case 'gnss':" in math and 'y: 0.36' in math)
check('renderer snapshots exploded parts', 'explodedPartsSnapshot()' in renderer)
check('raycast API preserved', 'raycastMeshes(): THREE.Mesh[]' in renderer)
check('assembly highlighting preserved', 'applyAssemblyState(' in renderer)
check('real GLB loading preserved', 'loadRequired' in renderer and 'loadModel(url)' in renderer)
check('direction labels conditional', 'if (directionLabelsVisible.value)' in drone)
check('direction labels hidden in exploded mode', "assemblyViewMode.value === 'assembled'" in drone)

check('compact DOM labels', 'data-testid="exploded-component-label"' in drone)
check('label width <=164px', 'width: 164px;' in drone)
check('label height <=26px', 'height: 26px;' in drone)
check('labels use real component names', 'component.name' in labels)
check('repeated categories grouped', 'One compact label per component category' in labels and '×${count}' in labels)
check('uninstalled ghost labels excluded', '!part.installed || part.componentId === null' in labels)
check('labels stay at scene edges', 'leftX = cfg.margin' in layout and 'rightX =' in layout)
check('collision resolver exists', 'resolveColumn(' in layout and 'placementsOverlap(' in layout)
check('labels hidden until mostly exploded', 'explosionProgress.value < 0.72' in drone)
check('camera projection drives label positions', 'world.project(camera)' in drone)
check('selected/error visual states retained', 'selected: props.selectedSlot' in drone and 'issue: props.issueSlots.includes' in drone)

check('GLB teaching badge removed from template', 'GLB 教学模型' not in drone)
check('asset badge class removed', 'class="asset-badge"' not in drone and '.asset-badge {' not in drone)
check('asset error panel retained', 'data-testid="asset-error"' in drone)

check('scene E2E checks exploded positions', 'P0-SCENE-013' in scene_test)
check('scene E2E checks labels', 'P0-SCENE-017' in scene_test)
check('scene E2E checks no overlap/compact size', 'P0-SCENE-018' in scene_test)
check('scene E2E checks GLB badge removal', 'P0-SCENE-019' in scene_test)
check('scene E2E restores assembled positions', 'P0-SCENE-016' in scene_test)
check('visual capture has exploded candidate', '03-assembly-exploded-current' in capture)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
if failed:
    sys.exit(1)
