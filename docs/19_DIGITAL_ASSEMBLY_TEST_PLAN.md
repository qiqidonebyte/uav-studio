# Digital Assembly 2.0 Test Plan

## Backend

`tests/test_digital_assembly_instances.py`

Covers:

- legacy aircraft expands to 18 physical instances;
- M1–M4 independent mount state;
- missing required mount blocks validation;
- mismatched component ID blocks validation;
- optional physical mount produces warning only.

`tests/test_digital_assembly_migration.py`

Covers additive SQLite migration for:

- `propeller_directions_json`;
- `assembly_instances_json`.

## Frontend unit contracts

`frontend/tests/assembly-semantics.test.ts`

Covers:

- deterministic 18-mount Quad-X model;
- legacy state expansion;
- repeated-slot clear/replace;
- 650/15" rotor clearance;
- 450/15" rotor collision;
- battery teaching-envelope fit.

`frontend/tests/assembly-transforms.test.ts`

Covers the unified:

```text
datum + explosion + installation
```

transform contract.

`frontend/tests/digital-assembly-workflow.test.ts`

Covers routing of mount-level validation to the correct assembly step.

## Existing scene contract

`p0-scene-contract.mjs` adds:

- semantic mount count and IDs;
- independent M1–M4 installed part instances.

## Full browser E2E

`e2e-digital-assembly.mjs` performs:

```text
Motor step
→ 3D Assembly
→ 4 Mount Anchors
→ hover Ghost/Snap
→ install M1
→ install M2
→ install M3
→ install M4
→ inspect M4
→ remove M4 with animation
→ backend physical validation blocks
→ quick restore
→ install 16 Ah battery
→ battery envelope warning
→ restore 10 Ah reference battery
```

The test restores the reference configuration before exit.
