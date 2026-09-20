# UAV Studio v1.5 — Digital Assembly Edition

## 1. Version goal

This release changes the assembly page from a component configurator with a 3D
viewer into a constrained UAV digital-assembly workbench.

The product contract is:

```text
Component Catalog
      ↓
Component Selection
      ↓
Semantic Mount Anchors
      ↓
Ghost Preview / Snap
      ↓
Physical Part Instances
      ↓
Install / Remove Animation
      ↓
Spatial Engineering Checks
      ↓
Engineering Validation
      ↓
Flight Lab
```

It is intentionally **not** a general CAD constraint solver.

## 2. Physical assembly model

The existing slot-level fields remain the engineering/catalog selection:

```text
motor_id = 10
esc_id = 20
propeller_id = 30
```

A new physical layer records actual installed instances:

```json
{
  "assembly_instances": [
    {"mount_id": "motor:M1", "slot": "motor", "component_id": 10},
    {"mount_id": "motor:M2", "slot": "motor", "component_id": 10}
  ]
}
```

This preserves V1 engineering compatibility while allowing M1–M4 to be
independently installed, selected and removed.

The engineering engine continues to calculate the **intended aircraft design**
from slot-level component choices. `assembly_instances` represents physical
assembly progress and gates validation/flight release. This separation avoids
making mass/thrust calculations fluctuate while a student is midway through a
teaching assembly exercise.

## 3. Mount Anchor contract

Quad-X currently resolves 18 semantic mounts:

```text
frame:main

motor:M1  motor:M2  motor:M3  motor:M4
esc:M1    esc:M2    esc:M3    esc:M4
propeller:M1 ... propeller:M4

battery:main
power_module:main
flight_controller:main
gnss:main
payload:main
```

Mount positions are resolved from frame `mount_points` when present. Legacy
frames deterministically derive the same contract from `motor_diagonal_m` and
existing component positions.

Each mount contains:

- semantic ID;
- accepted slot type;
- body-frame position;
- installation approach offset;
- snap radius;
- optional M1–M4 identity;
- required/optional status.

## 4. Unified transform

Every part starts from one immutable assembly datum.

```text
current position
  = base datum
  + explosion offset × explosion progress
  + install offset × (1 - install progress)
```

Therefore normal view, exploded view and installation animation no longer own
separate position logic.

## 5. Interactive assembly

The component card keeps the old **Quick Configure** path for compatibility and
adds **3D Assembly**.

3D Assembly mode:

1. select a catalog component;
2. old physical instances for that slot are removed;
3. all legal empty Mount Anchors appear in the 3D scene;
4. the selected real GLB is already staged as a translucent Ghost at every legal empty mount;
5. hovering an anchor highlights that exact Ghost and confirms the snap target;
6. clicking the anchor persists that physical instance;
7. the installed part animates from its approach offset into the datum;
8. the next legal mount remains available until the slot is complete.

Removal runs the inverse visual motion before the database change is persisted.

## 6. Spatial engineering

Two checks are part of v1.5.

### Rotor disc collision

The system uses actual propeller diameter and semantic rotor centers. Invalid
frame/prop combinations generate a 3D red rotor-disc overlay.

### Battery teaching envelope

The system compares the actual loaded GLB battery bounds against a
frame-scale-aware teaching battery bay. This is a visualization/teaching
envelope, not a manufacturing tolerance model.

## 7. Backend safety

`assembly_instances_json` is an additive SQLite migration.

Existing databases with NULL physical state are interpreted as their historical
fully assembled state. Legacy API clients that omit `assembly_instances` also
receive the compatible default behavior.

The backend blocks flight creation when a required physical mount is missing:

```text
ASSEMBLY_MOUNT_INCOMPLETE
```

It also rejects stale/mismatched physical instances:

```text
ASSEMBLY_INSTANCE_MISMATCH
```

GNSS and payload remain optional; selecting but not physically mounting them
produces a warning rather than a blocking error.

## 8. Non-goals

This release does not add:

- arbitrary 6-DoF free drag;
- mechanical mating solvers;
- manufacturing tolerances;
- threaded fastener simulation;
- full electrical CAD;
- automatic wire routing;
- mesh-mesh precision collision.

Those would increase complexity without improving the current teaching loop
enough to justify the cost.
