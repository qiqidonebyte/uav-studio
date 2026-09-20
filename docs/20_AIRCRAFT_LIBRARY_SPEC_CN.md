# UAV Studio v1.5.1 — Aircraft Library / Design Save

## 1. Version goal

v1.5 solved **how a UAV is physically assembled**.

v1.5.1 solves the missing product layer:

> A student must be able to own, save, reopen, copy and manage multiple aircraft designs.

Before this release the frontend was effectively bound to:

```text
Aircraft #1
```

Every component change was persisted, but it overwrote the same default aircraft.
That is persistence, not a design portfolio.

v1.5.1 turns `AircraftRecord` into a first-class user design.

---

## 2. Product concepts

UAV Studio now explicitly separates:

```text
Template
   ↓ create / copy

Aircraft Design
   │
   ├── assembly state
   ├── engineering state
   ├── metadata
   └── experiments
```

Templates are generated as fresh values and are never edited in place.

Aircraft Designs are persisted SQLite records.

Experiments keep the aircraft ID/name snapshot for traceability.

---

## 3. Aircraft metadata

`AircraftRecord` receives additive columns:

```text
description
created_at
updated_at
```

Existing databases are migrated by `ensure_schema_compatibility()`.

Legacy rows are backfilled at startup without deleting or recreating data.

---

## 4. Portfolio API

### List designs

```http
GET /api/aircraft
```

Returns:

```text
AircraftDefinition
Engineering summary
Validation
Description
Created time
Updated time
Experiment count
```

### Templates

```http
GET /api/aircraft/templates
```

Current templates:

```text
reference-650
blank-quad-x
chassis-450
```

The 450 chassis template intentionally contains only the frame because the
current 14/15-inch propeller catalog is physically incompatible with a 450
motor diagonal.

### Create from template

```http
POST /api/aircraft/from-template/{template_key}
```

### Duplicate / Save As

```http
POST /api/aircraft/{id}/duplicate
```

The copy receives a new database ID and is independent from the source design.

### Rename / description

```http
PATCH /api/aircraft/{id}/metadata
```

### Delete

```http
DELETE /api/aircraft/{id}
```

Safety rules:

- at least one aircraft design must remain;
- a design with experiment history cannot be deleted, preserving traceability.

---

## 5. Autosave

UAV Studio continues to save component/assembly changes immediately through:

```text
PUT /api/aircraft/{activeAircraftId}
```

The fixed `DEFAULT_AIRCRAFT_ID = 1` assumption is removed.

The active design ID is remembered in local storage only as a convenience.
SQLite remains the source of truth.

UI status:

```text
正在保存…
已保存
保存失败
```

No manual Ctrl+S workflow is required for normal assembly edits.

---

## 6. My Aircraft

New route:

```text
/aircraft
```

This becomes the product entry page.

Each design card contains:

- actual shared-renderer 3D miniature;
- design name and description;
- validation / flyable status;
- total mass;
- TWR;
- estimated endurance;
- last modified time;
- experiment count;
- open / continue design;
- duplicate;
- rename / description;
- delete when safe.

The page is intentionally a **Design Library**, not an admin CRUD table.

---

## 7. True 3D card preview

`AircraftMiniature.vue` reuses:

```text
AircraftRenderer
Component.visual
assembly_instances
```

Therefore the card shows the actual saved aircraft state rather than a generic
static thumbnail.

The design library uses a **single shared WebGL renderer** to generate cached
3D thumbnail images sequentially. Cards display the generated image rather than
opening one WebGL context per card, avoiding browser context limits when many
aircraft designs accumulate.

---

## 8. Templates

### EduQuad-650 Reference

A fully assembled reference configuration.

### Blank Quad-X

All component choices empty; suitable for a from-zero exercise.

### EduQuad-450 Chassis

Only the 450 frame is installed.

It deliberately does **not** present the current 14/15-inch propulsion system as
a valid 450 reference aircraft.

---

## 9. Flight Lab integration

Simulation creation now reads:

```text
assemblyStore.activeAircraftId
```

instead of hard-coding aircraft ID 1.

So the aircraft opened in My Aircraft is the aircraft used by Flight Lab.

---

## 10. Assembly-page integration

The assembly workbench gains:

```text
已保存 / 正在保存 / 保存失败
我的飞机
另存为副本
```

`另存为副本` duplicates the complete current design, including Digital Assembly
physical instances.

---

## 11. Compatibility

This package is cumulative with the previous v1.5 Digital Assembly Edition.

It is built against the verified public cloud baseline:

```text
qiqidonebyte/uav-studio
main
61a9a82e5c49f039d9b741438b721fd04c5230ab
```

The public GitHub branch does not yet contain the locally generated v1.5
Digital Assembly overlay, so v1.5.1 includes the necessary v1.5 modified files
as well.
