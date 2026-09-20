# Accounts & Workspace Test Plan

## Backend tests

`tests/test_auth_workspace.py`

Covers:

- password hashing / verification;
- session token hashing;
- legacy aircraft ownership migration;
- user profile normalization.

`tests/test_auth_migration.py`

Covers additive migration of:

```text
users.display_name
users.role
users.is_active
users.created_at
aircraft.owner_user_id
```

## Runtime FastAPI integration

`tools/verify_auth_runtime.py`

Uses the real auth/database/aircraft route implementation.

Flow:

```text
anonymous protected API → 401
bad admin login → 401
admin login → HttpOnly SameSite cookie
legacy aircraft → admin only
logout → protected API 401

register Alice
→ independent settings
→ create aircraft #1 ... #10
→ #11 rejected 409
→ duplicate rejected at quota
→ duplicate username rejected

register Bob
→ empty aircraft library
→ default independent settings
→ cannot GET/PATCH/duplicate/DELETE Alice aircraft
→ cannot start simulation from Alice aircraft
→ can create Bob aircraft

login Alice again
→ ten aircraft restored
→ settings restored
```

## Static contract verification

`tools/verify_auth_workspace.py`

Verifies:

- session/user/aircraft-owner schema;
- additive migrations;
- auth route contracts;
- HttpOnly / SameSite cookie;
- API auth middleware;
- owner-scoped aircraft;
- backend quota enforcement;
- experiment isolation;
- multi-session simulation manager;
- WebSocket auth;
- current-user settings;
- router guard;
- login/register UI;
- per-user active aircraft storage;
- quota UI;
- auth E2E package command.

## Regression

Also executed:

```text
tools/verify_aircraft_library.py
tools/verify_digital_assembly.py
```

to ensure identity/workspace changes do not remove Aircraft Library or Digital
Assembly contracts.

## Browser E2E

`frontend/tests/e2e-auth.mjs`

Flow:

```text
anonymous /aircraft
→ redirected to login
→ login stable E2E student
   or register it on the first run
→ My Aircraft
→ quota UI contains / 10
→ session cookie is HttpOnly + SameSite Lax
→ JS document.cookie cannot read uav_session
→ logout
→ protected Assembly redirects to login
→ login again
→ saved aircraft workspace returns
```

The browser E2E is repeatable and reuses one fixed test account.
