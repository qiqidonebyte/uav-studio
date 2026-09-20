# Verification Report — Propeller Overlap Fix 2.0.1

## Cloud baseline

`qiqidonebyte/uav-studio@main`

HEAD:

`df88d9e3e4cb02138cbda1cbf631c7fdc2bad4d2`

## Root cause confirmed

Realistic Edition 2.0 duplicated central prop fasteners:

- motor asset: prop_adapter + prop_nut
- prop asset: washer + nut

The prop hub was also solid, so it could intersect the motor adapter.

The checked-in 450 frame is additionally physically incompatible with the
current 14/15 inch prop assets:

- adjacent motor spacing = 450 / sqrt(2) = 318.2 mm
- 14 inch prop disc = 355.6 mm
- overlap = 37.4 mm

## Actual executed tests

### Realistic asset suite

`python tools/verify_realistic_assets.py`

Result:

`174 / 174 PASS`

### Propeller-fit focused verifier

`python tools/verify_propeller_fit_fix.py`

Result:

`24 / 24 PASS`

Checks include:

- exact 14/15 inch swept diameters
- no duplicate prop nut/washer
- annular hub exists
- motor owns adapter/nut
- hub is below retaining nut
- hub bore clears adapter
- manifest fit metadata
- 650 + 15in has positive clearance
- 450 + 14in is detected as incompatible
- backend runtime issue is wired
- frontend assembly step is wired

### Pytest asset contracts

`pytest -q tests/test_propeller_fit_assets.py`

Result:

`10 passed`

### Runtime validation integration

`python tools/verify_propeller_fit_runtime.py`

Result:

`PASS runtime p0_validation overlap integration`

This executed the real `backend/p0_validation.py` code path with the current
schema surface stubbed so the overlay could be verified without a full checkout.

Verified:

- 650 + 15in does not add overlap error
- 450 + 14in adds exactly one blocking error
- affected slots = frame + propeller
- affected mounts = M1-M4
- repeated augmentation does not duplicate the issue

### Syntax / compile

Changed Python sources/tests: PASS

`frontend/src/utils/assembly.ts` isolated TypeScript strict compile: PASS

## Tests included for the real repository

- `tests/test_propeller_fit_assets.py`
- `tests/test_propeller_fit_validation.py`
- `frontend/tests/propeller-fit-ui.test.ts`

After overlaying into the full project, run:

```bash
pytest -q tests/test_propeller_fit_assets.py tests/test_propeller_fit_validation.py

cd frontend
npm run test
npm run build
npm run test:p0:scene
```

Full Vite/Vitest/Playwright execution was not run in this artifact environment
because the full repository/node_modules are not present here.
