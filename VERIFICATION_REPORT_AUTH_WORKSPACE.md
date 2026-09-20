# Verification Report — UAV Studio v1.5.2 Accounts & Workspace

## Baseline

```text
qiqidonebyte/uav-studio
main
cdd316c938242905cbd4a363eb6fe1d2ac14af29
style: rename aircraft entry to my aircraft
```

This overlay was produced after re-reading the current GitHub code, including
the user's latest App design-switcher and corrected 204 Aircraft delete route.

## Actually executed

### 1. Backend pytest + regressions

Executed:

```text
tests/test_auth_workspace.py
tests/test_auth_migration.py
tests/test_aircraft_library.py
tests/test_aircraft_library_migration.py
tests/test_digital_assembly_instances.py
tests/test_digital_assembly_migration.py
```

Result:

```text
16 passed
```

### 2. Accounts & Workspace source contract

Executed:

```text
python tools/verify_auth_workspace.py
```

Result:

```text
46 / 46 PASS
```

Includes:

- Session table;
- user role/profile;
- aircraft ownership;
- additive migration;
- HttpOnly/SameSite cookie;
- token hashing;
- login/register/logout/me;
- API authentication middleware;
- owner-scoped aircraft;
- 10-aircraft server limit;
- simulation ownership;
- WebSocket authentication;
- experiment isolation;
- multi-session simulator;
- current-user settings;
- frontend router/auth shell/quota UI;
- auth E2E script;
- frontend simulation state reset at logout/account change.

### 3. Runtime FastAPI authentication/workspace integration

Executed:

```text
python tools/verify_auth_runtime.py
```

Result:

```text
PASS
```

The runtime test exercises real SQLite/Pydantic/FastAPI authentication and
aircraft routes.

Verified:

```text
anonymous protected API → 401
invalid login → 401
admin login → session cookie
legacy aircraft → admin ownership
logout → 401

Alice registration
→ independent settings
→ create exactly 10 aircraft
→ aircraft #11 rejected
→ duplicate at 10 rejected
→ case-insensitive duplicate username rejected

Bob registration
→ empty isolated library
→ default independent settings
→ GET Alice aircraft rejected
→ PATCH Alice aircraft rejected
→ duplicate Alice aircraft rejected
→ DELETE Alice aircraft rejected
→ start simulation with Alice aircraft rejected
→ Bob creates own aircraft

Alice login again
→ 10 aircraft restored
→ Alice settings restored
```

Cookie assertions include:

```text
HttpOnly
SameSite=Lax
```

### 4. Aircraft Library regression

Executed:

```text
python tools/verify_aircraft_library.py
```

Result:

```text
49 / 49 PASS
```

The verifier was updated to match the user's current GitHub UI (`我的飞机`
design-switcher) and current corrected 204 delete route.

### 5. Digital Assembly regression

Executed:

```text
python tools/verify_digital_assembly.py
```

Result:

```text
45 / 45 PASS
```

Identity/workspace work therefore does not remove the existing Mount Anchor,
Ghost/Snap, independent M1–M4, install/remove animation or spatial-engineering
contracts.

### 6. Modified frontend source syntax

TypeScript parser PASS for:

```text
api/client.ts
types/auth.ts
types/settings.ts
stores/auth.ts
stores/assembly.ts
stores/settings.ts
router/index.ts
App.vue
Login.vue
Register.vue
AircraftLibrary.vue
Assembly.vue
Settings.vue
```

### 7. Browser E2E source syntax

Executed:

```text
node --check frontend/tests/e2e-auth.mjs
node --check frontend/tests/e2e-aircraft-library.mjs
node --check frontend/tests/e2e-digital-assembly.mjs
node --check frontend/tests/p0-scene-contract.mjs
```

Result:

```text
PASS
```

### 8. Python compile

All changed backend/auth/test/verifier Python modules were compiled with
`py_compile`.

Result:

```text
PASS
```

## Browser/build limitation in this artifact workspace

This overlay workspace does not contain `frontend/node_modules` and does not
run the complete Vite + FastAPI stack.

Therefore I do not claim that the live Playwright auth E2E or full:

```text
vue-tsc --noEmit
vite build
vitest
```

ran in this artifact environment.

The full auth browser E2E is included and syntax-validated. It verifies:

```text
anonymous redirect
→ login/register
→ My Aircraft
→ /10 quota UI
→ HttpOnly session cookie
→ logout
→ protected route redirect
→ login again
→ workspace restored
```

Run it in the complete repository with:

```bash
cd frontend
npm install
npm run build
npm run test
npm run e2e:auth
```

## Deliberate boundary

The component catalog is still a shared authenticated resource in v1.5.2.

Per-user/private components and teacher/admin component permissions are a
separate permission model and were not mixed into this login + aircraft quota
release.
