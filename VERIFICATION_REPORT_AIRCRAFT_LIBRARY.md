# Verification Report — UAV Studio v1.5.1 Aircraft Library

## Baseline

```text
qiqidonebyte/uav-studio
main
61a9a82e5c49f039d9b741438b721fd04c5230ab
feat: fix propeller overlap and update realistic assets
```

The public branch was checked before implementation.

Because the previous v1.5 Digital Assembly overlay has not yet been pushed to
GitHub main, this package is cumulative and includes the v1.5 source changes
required by v1.5.1.

---

## Actually executed tests

### 1. Backend pytest

Executed:

```text
tests/test_aircraft_library.py
tests/test_aircraft_library_migration.py
tests/test_digital_assembly_instances.py
tests/test_digital_assembly_migration.py
```

Result:

```text
11 passed
```

Coverage includes:

- three stable aircraft templates;
- 650 reference full physical assembly;
- blank Quad-X template;
- 450 chassis-only template;
- independent template values;
- deterministic duplicate naming;
- legacy metadata backfill;
- additive SQLite metadata migration;
- previous Digital Assembly physical-instance validation;
- explicit empty-vs-legacy assembly state;
- migration regression.

### 2. Digital Assembly regression verifier

Executed:

```text
python tools/verify_digital_assembly.py
```

Result:

```text
45 / 45 PASS
```

This confirms the Aircraft Library work did not remove:

- Semantic Mount Anchors;
- M1–M4 independent part instances;
- Ghost/Snap assembly;
- install/remove animation;
- spatial checks;
- mount-level validation;
- Digital Assembly visual probe contracts.

### 3. Aircraft Library source-contract verifier

Executed:

```text
python tools/verify_aircraft_library.py
```

Result:

```text
49 / 49 PASS
```

Checks include:

- aircraft metadata DB fields;
- additive migration;
- template contracts;
- portfolio API routes;
- experiment traceability delete guard;
- final-design delete guard;
- no fixed Aircraft #1 in assembly store;
- active aircraft local preference;
- autosave state;
- Flight Lab active-aircraft integration;
- My Aircraft route/navigation;
- real 3D preview pipeline;
- one shared WebGL preview renderer;
- create / duplicate / rename / delete UI;
- Assembly Save As;
- registered E2E workflow.

### 4. Runtime FastAPI portfolio integration

Executed:

```text
python tools/verify_aircraft_library_runtime.py
```

Result:

```text
PASS
```

The real portfolio route code in `backend/main.py` was executed with real:

- SQLAlchemy models;
- SQLite;
- Pydantic schemas;
- migration logic;
- Aircraft Library helper logic.

Unchanged services not included in this overlay artifact were stubbed.

Runtime flow:

```text
GET library
→ GET templates
→ POST create from template
→ POST duplicate
→ PATCH rename + description
→ GET reload
→ DELETE duplicate
→ create experiment record
→ verify delete blocked
→ remove experiment record
→ delete unused design
→ verify final remaining design cannot be deleted
```

### 5. TypeScript strict core contracts

Executed `tsc --noEmit --strict` for:

- `types/aircraft.ts`
- `three/assemblySemantics.ts`
- `three/assemblyTransforms.ts`
- `utils/assembly.ts`
- `types/visual-test.d.ts`

Result:

```text
PASS
```

### 6. Modified TypeScript / Vue parser validation

PASS for:

- `aircraftPreview.ts`
- assembly store;
- simulation store;
- router;
- App.vue;
- AircraftLibrary.vue;
- AircraftMiniature.vue;
- Assembly.vue;
- AircraftRenderer.ts;
- DroneScene.vue;
- ComponentCard.vue;
- Digital Assembly Vitest sources.

### 7. Browser test source syntax

Executed:

```text
node --check frontend/tests/e2e-aircraft-library.mjs
node --check frontend/tests/e2e-digital-assembly.mjs
node --check frontend/tests/p0-scene-contract.mjs
```

Result:

```text
PASS
```

### 8. Python compile

Changed backend/test/tool Python files were compiled with `py_compile`.

Result:

```text
PASS
```

---

## Browser/build limitation

The artifact workspace is an overlay, not a complete freshly cloned project.
It does not contain all unchanged frontend files plus installed `node_modules`
and a running Vite + FastAPI stack.

Therefore this environment did **not** claim execution of:

```text
npm run build
npm run test
npm run e2e:aircraft-library
```

as a live browser stack.

The full browser E2E is included and syntax-validated. Run it after covering
the package into your normal complete repository.

---

## Important behavior verified by design

Normal assembly edits are autosaved to:

```text
PUT /api/aircraft/{activeAircraftId}
```

not Aircraft #1.

Flight Lab creates simulations using the same active aircraft ID.

Design cards use actual renderer-generated thumbnails but a single shared WebGL
context, preventing one-context-per-card scaling problems.
