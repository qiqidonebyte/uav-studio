from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks: list[tuple[str, bool]] = []


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))


models = read("backend/models.py")
database = read("backend/database.py")
schemas = read("backend/schemas.py")
main = read("backend/main.py")
library = read("backend/aircraft_library.py")
store = read("frontend/src/stores/assembly.ts")
simulation = read("frontend/src/stores/simulation.ts")
router = read("frontend/src/router/index.ts")
app = read("frontend/src/App.vue")
view = read("frontend/src/views/AircraftLibrary.vue")
miniature = read("frontend/src/components/AircraftMiniature.vue")
preview = read("frontend/src/three/aircraftPreview.ts")
assembly = read("frontend/src/views/Assembly.vue")
package = read("frontend/package.json")
e2e = read("frontend/tests/e2e-aircraft-library.mjs")

check("AircraftRecord description", "description: Mapped[str | None]" in models)
check("AircraftRecord created_at", "created_at: Mapped[str | None]" in models)
check("AircraftRecord updated_at", "updated_at: Mapped[str | None]" in models)
check("metadata migration description", 'ADD COLUMN description VARCHAR(1000)' in database)
check("metadata migration created_at", 'ADD COLUMN created_at VARCHAR(64)' in database)
check("metadata migration updated_at", 'ADD COLUMN updated_at VARCHAR(64)' in database)
check("metadata backfill", "ensure_aircraft_metadata" in library)

check("library response schema", "class AircraftLibraryItem(BaseModel)" in schemas)
check("template response schema", "class AircraftTemplate(BaseModel)" in schemas)
check("metadata update schema", "class AircraftMetadataUpdate(BaseModel)" in schemas)
check("stable reference template", 'key="reference-650"' in library)
check("blank template", 'key="blank-quad-x"' in library)
check("450 chassis template", 'key="chassis-450"' in library)

check("GET aircraft library route", '@app.get("/api/aircraft"' in main)
check("GET templates route", '@app.get("/api/aircraft/templates"' in main)
check("create from template route", '"/api/aircraft/from-template/{template_key}"' in main)
check("duplicate route", '"/api/aircraft/{aircraft_id}/duplicate"' in main)
check("metadata route", '"/api/aircraft/{aircraft_id}/metadata"' in main)
check("delete route", '@app.delete("/api/aircraft/{aircraft_id}"' in main)
check("delete preserves experiment traceability", "已有实验记录" in main)
check("delete keeps one design", "至少保留一架飞机设计" in main)
check("design updates touch timestamp", "_touch_aircraft(record)" in main)

check("fixed default aircraft id removed from assembly store", "DEFAULT_AIRCRAFT_ID" not in store)
check("active aircraft local persistence", "uavstudio.activeAircraftId" in store)
check("portfolio list state", "aircraftLibrary" in store)
check("template list state", "aircraftTemplates" in store)
check("createFromTemplate store action", "createFromTemplate" in store)
check("duplicateActive store action", "duplicateActive" in store)
check("metadata update store action", "updateAircraftMetadata" in store)
check("delete store action", "deleteAircraft" in store)
check("autosave states", "saveStatusZh" in store and "'saving'" in store and "'error'" in store)
check("active aircraft used by flight simulation", "assemblyStore.activeAircraftId" in simulation)
check("simulation no fixed aircraft id", "DEFAULT_AIRCRAFT_ID" not in simulation)

check("My Aircraft route", "{ path: '/aircraft', component: AircraftLibrary }" in router)
check("root opens portfolio", "{ path: '/', redirect: '/aircraft' }" in router)
check("top navigation portfolio", 'to="/aircraft">我的飞机' in app)
check("topbar autosave status", "saveStatusZh" in app)
check("real 3D card preview", "aircraftPreviewDataUrl" in miniature)
check("single shared 3D preview renderer", "new AircraftRenderer()" in preview and "const previewCache = new Map" in preview)
check("preview avoids many WebGL contexts", "single shared WebGL context" in preview)
check("design library cards", 'data-testid="aircraft-design-card"' in view)
check("new design dialog", 'data-testid="new-aircraft-dialog"' in view)
check("duplicate design UI", 'data-testid="duplicate-aircraft-design"' in view)
check("rename/description UI", 'data-testid="edit-aircraft-dialog"' in view)
check("safe delete UI", 'data-testid="delete-aircraft-design"' in view)
check("assembly Save As", "另存为副本" in assembly)
check("assembly autosave indicator", "assembly-save-state" in assembly)
check("E2E package script", '"e2e:aircraft-library"' in package)
check("repeatable E2E workflow", "create, persist, duplicate, rename, delete" in e2e)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    sys.exit(1)
