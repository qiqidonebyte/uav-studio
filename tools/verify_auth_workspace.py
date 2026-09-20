from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks: list[tuple[str, bool]] = []


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))


models = read("backend/models.py")
database = read("backend/database.py")
auth = read("backend/auth.py")
settings = read("backend/user_settings.py")
main = read("backend/main.py")
experiments = read("backend/experiments.py")
sim_manager = read("backend/simulation_manager.py")
api = read("frontend/src/api/client.ts")
auth_store = read("frontend/src/stores/auth.ts")
assembly = read("frontend/src/stores/assembly.ts")
simulation_store = read("frontend/src/stores/simulation.ts")
settings_store = read("frontend/src/stores/settings.ts")
router = read("frontend/src/router/index.ts")
app = read("frontend/src/App.vue")
login = read("frontend/src/views/Login.vue")
register = read("frontend/src/views/Register.vue")
library = read("frontend/src/views/AircraftLibrary.vue")
settings_view = read("frontend/src/views/Settings.vue")
package = read("frontend/package.json")

check("session table", "class SessionRecord(Base)" in models)
check("user display name", "display_name:" in models)
check("user role", "role:" in models)
check("aircraft owner", "owner_user_id:" in models)
check("user migration", "ALTER TABLE users ADD COLUMN role" in database)
check("aircraft owner migration", "ADD COLUMN owner_user_id INTEGER" in database)
check("ownership index", "ix_aircraft_owner_user_id" in database)

check("HttpOnly session cookie", "httponly=True" in auth)
check("SameSite cookie", 'samesite="lax"' in auth)
check("session token hashing", "session_token_hash" in auth and "sha256" in auth)
check("register route", '"/api/auth/register"' in auth)
check("login route", '"/api/auth/login"' in auth)
check("logout route", '"/api/auth/logout"' in auth)
check("me route", '"/api/auth/me"' in auth)
check("aircraft limit constant", "AIRCRAFT_LIMIT_PER_USER = 10" in auth)
check("legacy ownership", "ensure_legacy_aircraft_ownership" in auth)

check("global API auth middleware", "require_login_for_api" in main)
check("CORS preflight bypass", 'request.method != "OPTIONS"' in main)
check("per-user aircraft listing", "AircraftRecord.owner_user_id == current_user.id" in main)
check("capacity enforcement", "ensure_aircraft_capacity" in main)
check("create assigns owner", "AircraftRecord(owner_user_id=current_user.id)" in main)
check("owned aircraft lookup", "owned_aircraft_or_404" in main)
check("per-user delete count", "owned_aircraft_count(session, current_user)" in main)
check("simulation ownership guard", "manager_for_user_or_404" in main)
check("websocket cookie auth", "websocket.cookies.get(SESSION_COOKIE_NAME)" in main)
check("experiment ownership", "owner_user_id=current_user.id" in main)
check("experiment query join", "AircraftRecord.owner_user_id == owner_user_id" in experiments)
check("multi-session simulator", "self._sessions: dict[int, SimulationSession]" in sim_manager)

check("settings current user dependency", "record: UserRecord = Depends(get_current_user)" in settings)
check("no admin-only settings read", "return read_settings(record)" in settings)

check("axios credentials", "withCredentials: true" in api)
check("auth store", "defineStore('auth'" in auth_store)
check("login UI", 'data-testid="login-form"' in login)
check("register UI", 'data-testid="register-form"' in register)
check("router guard", "router.beforeEach" in router)
check("public login route", "meta: { public: true }" in router)
check("auth-aware app shell", "authStore.authenticated" in app)
check("logout UI", "logout-chip" in app)
check("per-user active aircraft key", "activeAircraftKey(userId" in assembly)
check("store aircraft limit", "canCreateAircraft" in assembly and "aircraftLimit" in assembly)
check("frontend simulation reset", "resetForLogout" in simulation_store and "simulationId.value = null" in simulation_store)
check("library quota display", "store.aircraftLibrary.length }} / {{ store.aircraftLimit" in library)
check("library new disabled at quota", ':disabled="!store.canCreateAircraft"' in library)
check("settings account quota", "aircraftStore.aircraftCount" in settings_view)
check("settings no local admin copy", "本地管理员" not in settings_view)
check("auth E2E package script", '"e2e:auth"' in package)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    sys.exit(1)
