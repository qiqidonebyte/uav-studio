# UAV Studio v1.5.2 — Accounts & Workspace

## 1. Goal

This release removes the old implicit single-admin behavior and introduces a
real account boundary for UAV Studio.

The product contract becomes:

```text
User Account
    ↓
Private Aircraft Workspace
    ↓
Aircraft Design (max 10 / user)
    ↓
Assembly / Engineering / Flight / Experiments
```

The component catalog remains a shared system resource in this release.

## 2. Authentication

Authentication uses server-side random sessions.

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

The browser receives a random `uav_session` cookie.

Cookie properties:

```text
HttpOnly
SameSite=Lax
Path=/
7-day session lifetime
Secure when UAV_SESSION_SECURE_COOKIE=1
```

Only the SHA-256 hash of the random session token is stored in SQLite. The raw
session token is not stored in the database.

Passwords continue to use the existing PBKDF2-SHA256 contract.

## 3. Registration

Registration is open in v1.5.2.

Usernames:

```text
3–32 characters
A-Z / a-z / 0-9 / _ / -
case-insensitive through lowercase normalization
```

New accounts receive:

```text
role = student
independent settings_json
independent Aircraft Library
aircraft_limit = 10
```

A display name is optional.

## 4. Existing administrator compatibility

Existing databases keep the historical `admin` user and its current password.

On a fresh installation the compatibility administrator is still created. A
deployment may set:

```text
UAV_ADMIN_PASSWORD
```

before the first startup to choose its initial password.

The legacy fallback password remains `123456` for compatibility when the
environment variable is not supplied; production/teaching deployments should
change it immediately.

## 5. Database changes

### users

Additive columns:

```text
display_name
role
is_active
created_at
```

### sessions

New table:

```text
id
token_hash
user_id
created_at
expires_at
last_seen_at
```

### aircraft

Additive column:

```text
owner_user_id
```

Existing pre-auth aircraft with no owner are assigned to the legacy admin on
startup. No aircraft data is discarded.

## 6. API protection

All `/api/*` endpoints require a valid session except:

```text
/api/health
/api/auth/login
/api/auth/register
```

CORS OPTIONS preflight is not blocked.

Aircraft lookups deliberately return `404` for another user's aircraft instead
of revealing its existence.

## 7. Per-user aircraft workspace

All Aircraft Library operations are owner-scoped:

```text
GET    /api/aircraft
GET    /api/aircraft/{id}
POST   /api/aircraft
POST   /api/aircraft/from-template/{key}
POST   /api/aircraft/{id}/duplicate
PATCH  /api/aircraft/{id}/metadata
PUT    /api/aircraft/{id}
DELETE /api/aircraft/{id}
POST   /api/aircraft/{id}/calculate
```

A user can only read or mutate their own aircraft.

## 8. Ten-aircraft limit

The authoritative limit is:

```text
AIRCRAFT_LIMIT_PER_USER = 10
```

The server enforces the limit on every path that creates a new aircraft:

```text
raw create
create from template
duplicate / Save As
```

At the limit the API returns HTTP 409:

```text
每个用户最多保存 10 架飞机，请删除或整理现有设计后再创建。
```

The frontend also:

- displays `current / 10`;
- disables New Design at 10;
- disables Duplicate at 10;
- disables Assembly “Save As” at 10;
- shows the quota in account settings.

Frontend checks are convenience only; the backend remains authoritative.

## 9. Per-user settings

The previous settings code always resolved `admin`.

Now:

```text
GET /api/settings
PUT /api/settings
PUT /api/user/password
GET /api/user/me
```

operate on the authenticated user.

Each account has independent:

```text
general settings
3D settings
flight settings
password
```

## 10. Active aircraft preference

The active aircraft ID is still a browser convenience, but is now namespaced:

```text
uavstudio.activeAircraftId:<user_id>
```

So users sharing the same browser do not overwrite each other's last-opened
aircraft preference.

SQLite remains the source of truth.

## 11. Experiment isolation

Experiment list/replay access is scoped through aircraft ownership.

```text
User
 ↓
AircraftRecord.owner_user_id
 ↓
SimulationRecord.aircraft_id
```

A user cannot read another user's experiment through the experiment endpoints.

## 12. Flight-session isolation

The previous SimulationManager held only one global active simulation. That
would allow one user to replace another user's in-memory flight session.

v1.5.2 changes it to:

```text
simulation_id → SimulationSession
```

so multiple active users can have independent simulation sessions.

All HTTP simulation commands verify that the simulation's aircraft belongs to
the current user.

WebSocket telemetry also validates the session cookie and aircraft ownership
before accepting the connection.

## 13. Frontend

New routes:

```text
/login
/register
```

Protected routes use a Vue Router guard.

The application shell is only shown after authentication.

Login / registration establishes the HttpOnly session automatically. Logout
removes the server-side session and clears local workspace state.

## 14. Product boundary for this release

Implemented:

```text
login
registration
logout
server session
private aircraft workspaces
private settings
private experiment history
10-aircraft quota
legacy data migration
```

Not implemented in v1.5.2:

```text
teacher/admin user-management UI
class/course invitation codes
password reset by email
private per-user component catalogs
fine-grained component-library permissions
OAuth / SSO
```

The existing component library is still a shared authenticated system resource.
