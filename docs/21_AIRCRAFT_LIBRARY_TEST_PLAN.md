# Aircraft Library Test Plan

## Backend unit tests

`tests/test_aircraft_library.py`

Covers:

- stable template keys;
- full 650 reference physical assembly;
- blank Quad-X state;
- 450 chassis-only state;
- template objects are independent values;
- deterministic duplicate naming;
- legacy portfolio metadata backfill.

`tests/test_aircraft_library_migration.py`

Covers additive SQLite migration for:

```text
description
created_at
updated_at
propeller_directions_json
assembly_instances_json
```

## Runtime FastAPI integration

`tools/verify_aircraft_library_runtime.py`

Executes the real Aircraft Library route implementation using the actual:

- SQLAlchemy models;
- Pydantic schemas;
- SQLite migration;
- `backend/main.py` route handlers.

Unchanged application services are stubbed because this overlay artifact does
not contain every unchanged backend module.

The runtime flow verifies:

```text
list
→ templates
→ create from template
→ duplicate
→ rename + description
→ reload
→ delete
→ experiment traceability guard
→ last-design deletion guard
```

## Frontend source contracts

`tools/verify_aircraft_library.py`

Verifies:

- fixed Aircraft #1 assumptions removed;
- active design local preference;
- portfolio state/actions;
- autosave states;
- Flight Lab uses active aircraft;
- My Aircraft route/navigation;
- real 3D card preview;
- create/duplicate/edit/delete UI;
- assembly Save As;
- E2E script registration.

## Browser E2E

`frontend/tests/e2e-aircraft-library.mjs`

Flow:

```text
open My Aircraft
→ create Blank Quad-X design
→ enter Assembly
→ verify current aircraft + saved state
→ reopen portfolio
→ verify persisted card
→ duplicate
→ rename duplicate
→ delete duplicate
→ delete original
→ verify test cleanup
```

The E2E is intentionally repeatable and restores the portfolio count when done.

## Regression

The package keeps the previous v1.5 Digital Assembly tests and P0 scene
contracts so portfolio work does not silently reintroduce a fixed single-aircraft
architecture.
