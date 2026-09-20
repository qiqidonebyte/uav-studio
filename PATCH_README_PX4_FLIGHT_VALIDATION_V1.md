# UAV Studio · PX4 Flight Validation V1

This is a **direct overlay package**. Extract it into the repository root. There is no wrapper directory inside the ZIP.

## What changed

- `FlightLab.vue` now routes by preflight permit:
  - `bridge_mode=live` -> PX4 SIH / MAVLink
  - `bridge_mode=demo` -> original UAV-Studio Simple Simulator
- PX4 live flight controls:
  - Connect / Heartbeat
  - Arm / Disarm
  - Relative Takeoff
  - Land
  - SIH wind
- PX4 telemetry now drives:
  - Three.js aircraft
  - Local Flight Map
  - Realtime Charts
  - motor animation/output display
  - battery/power panel
- Fixed takeoff altitude semantics:
  - browser inputs relative altitude
  - Bridge converts to AMSL before `MAV_CMD_NAV_TAKEOFF`
- PX4 live mode does **not** silently fall back to the old simulator.
- Target/waypoint control remains disabled in PX4 V1 rather than pretending to support it.

## Run

```bash
python -m pip install -r requirements.txt

# terminal 1
uvicorn backend.main:app --reload

# terminal 2
python -m backend.px4_service

# terminal 3 (Linux/WSL2)
./scripts/start_px4_sih.sh

# terminal 4
cd frontend
npm install
npm run dev
```

Complete the live PX4 debugging/preflight flow first, then open Flight Lab.

## Verification included

- `tests/test_px4_flight_validation.py`
- `frontend/tests/px4-flight-lab.test.ts`
- `docs/PX4_FLIGHT_VALIDATION_V1.md`
