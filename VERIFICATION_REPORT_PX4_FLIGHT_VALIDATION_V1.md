# Verification Report · PX4 Flight Validation V1

Verified against the current GitHub main-branch contracts inspected before building this overlay.

## Passed in artifact environment

- `backend/px4_service.py` Python compile: PASS
- backend test source Python compile: PASS
- TypeScript syntax transpile:
  - `frontend/src/api/px4.ts`: PASS
  - `frontend/src/utils/px4Flight.ts`: PASS
  - `frontend/tests/px4-flight-lab.test.ts`: PASS
  - `FlightLab.vue` `<script setup lang="ts">`: PASS
- Vue template tag balance: PASS
- Relative takeoff -> AMSL logic test: PASS
  - current AMSL 500 m
  - current relative altitude 1 m
  - requested relative takeoff 2 m
  - computed home AMSL 499 m
  - computed target AMSL 501 m
- Live/demo source routing is explicit:
  - live permit -> PX4 telemetry
  - demo permit -> existing Simple Simulator
- PX4 live branch uses `px4Api.arm/takeoff/land`
- PX4 live branch does not silently invoke `store.takeoff`
- Three.js, Local Flight Map and RealtimeCharts all receive the same `activeTelemetry`
- NED -> UAV Studio coordinate adapter is present and unit-tested
- SIH wind path writes `SIH_WIND_N` / `SIH_WIND_E`
- ZIP top level contains project paths directly; no wrapper folder

## Deliberately not claimed

The artifact environment does not contain the full checked-out repository, frontend `node_modules`, or a running PX4-Autopilot SIH instance. Therefore this report does not claim:

- full `npm run build`
- complete existing frontend test-suite execution
- real Heartbeat -> Arm -> Takeoff -> Hover -> Land runtime execution

Use `docs/PX4_FLIGHT_VALIDATION_V1.md` as the machine-side acceptance procedure with PX4 SIH running.
