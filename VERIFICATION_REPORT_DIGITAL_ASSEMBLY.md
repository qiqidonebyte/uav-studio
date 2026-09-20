# Verification Report — UAV Studio v1.5 Digital Assembly Edition

## Cloud baseline

Repository: `qiqidonebyte/uav-studio`

Branch: `main`

HEAD:

`61a9a82e5c49f039d9b741438b721fd04c5230ab`

Commit:

`feat: fix propeller overlap and update realistic assets`

The implementation was built against exact source blobs recorded in
`BASELINE_GITHUB.json`.

## Actually executed in this build environment

### 1. New backend behavior

```text
pytest:
6 passed
```

Coverage includes:

- legacy aircraft -> fully assembled physical-instance compatibility;
- explicit empty physical state is not mistaken for legacy state;
- independent required mount completion;
- missing mount blocks validation;
- stale/mismatched instance blocks validation;
- optional GNSS physical mount is warning-only;
- additive SQLite migration for assembly_instances_json.

### 2. Digital Assembly static/source contracts

```text
45 / 45 PASS
```

Checks cover backend persistence, semantic mounts, renderer part instances,
Ghost/Snap, install + detach animation, spatial checks, inspector wiring,
visual probe contracts and browser test presence.

### 3. TypeScript core contracts

Strict `tsc --noEmit`:

```text
PASS
```

Checked:

- `types/aircraft.ts`
- `assemblySemantics.ts`
- `assemblyTransforms.ts`
- `utils/assembly.ts`
- `types/visual-test.d.ts`

### 4. Modified TS / Vue source parsing

Parser PASS for:

- AircraftRenderer.ts
- assembly store
- DroneScene.vue
- Assembly.vue
- ComponentCard.vue
- all three new Vitest source files

### 5. Pure runtime contract

New TypeScript semantic/transform modules were compiled to CommonJS and
executed under Node.

Result:

```text
PASS runtime semantic + transform assertions
```

Runtime assertions covered:

- 18 semantic mounts;
- four independent motor mounts;
- legacy instance expansion;
- 650 + 15" rotor layout clear;
- 450 + 15" rotor collision;
- 10 Ah battery teaching envelope fit;
- 16 Ah battery envelope exceedance;
- unified assembly/explosion transform composition.

### 6. E2E source validation

```text
node --check frontend/tests/e2e-digital-assembly.mjs  PASS
node --check frontend/tests/p0-scene-contract.mjs    PASS
```

The supplied Digital Assembly E2E performs:

```text
3D Assembly
→ M1-M4 Mount Anchors
→ Ghost/Snap
→ install four motors
→ exact mount inspector
→ detach one motor
→ backend validation blocks
→ restore
→ 16 Ah envelope warning
→ restore 10 Ah reference configuration
```

### 7. Existing propeller-overlap regression

Against the current Realistic Edition 2.0.1 GLBs:

```text
10 pytest asset tests passed
24 / 24 propeller-fit checks passed
```

This confirms the v1.5 code does not undo the previous propeller hub / swept
diameter / frame-fit fix.

## Environment limitation

This artifact environment does not contain the full project's installed
`node_modules` and a running Vite + FastAPI application.

Therefore I did **not** claim that live Playwright browser E2E or the complete
`vue-tsc + vite build` executed here.

Those browser/build tests are included and should be run after overlaying into
your normal full project environment:

```bash
pytest -q

cd frontend
npm run build
npm run test
npm run test:p0:scene
npm run e2e:digital-assembly
npm run e2e
npm run e2e:flight
```
