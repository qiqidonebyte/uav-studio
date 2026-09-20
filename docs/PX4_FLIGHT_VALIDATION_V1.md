# PX4 Flight Validation V1

## Purpose

This patch closes the broken chain between the System Debugging workbench and Flight Lab.

Before:

```text
PX4 debugging -> preflight permit -> FlightLab -> UAV Studio Simple Simulator
```

After:

```text
PX4 debugging -> preflight permit (bridge_mode=live)
             -> FlightLab PX4 mode
             -> PX4 SIH / MAVLink
             -> Three.js + Local Flight Map + Realtime Charts
```

A `demo` preflight permit still uses the original Simple Simulator. A `live` permit never silently falls back to it.

## PX4 validation scope

V1 deliberately validates only:

```text
Connect / Heartbeat
-> Arm
-> Takeoff (relative altitude)
-> Hover
-> Land
```

Waypoint/offboard navigation is intentionally not exposed yet.

## Coordinate contract

PX4 local position is NED. The Bridge already exposes altitude as positive-up. The browser adapter maps:

```text
PX4 North -> UAV Studio +X
PX4 East  -> UAV Studio -Y (Y is left)
PX4 Up    -> UAV Studio +Z
```

Corresponding pitch/yaw and q/r signs are inverted.

## Takeoff altitude correction

`MAV_CMD_NAV_TAKEOFF` param7 is AMSL altitude. The Bridge HTTP API continues to accept a convenient relative altitude, but the service now computes:

```text
home_amsl = current_amsl - current_relative_alt
target_amsl = home_amsl + requested_relative_takeoff_alt
```

and sends the absolute target to PX4.

## SIH wind

In live PX4 mode, Flight Lab's wind controls write:

- `SIH_WIND_N`
- `SIH_WIND_E`

The old UAV-Studio simulator is not involved.

## Acceptance test

1. Complete System Debugging in PX4 live mode.
2. Pass final preflight and enter Flight Lab.
3. Confirm the source shows `PX4 SIH / MAVLink`.
4. Arm.
5. Set 2 m and Takeoff.
6. Confirm Three.js altitude/attitude follows PX4 telemetry.
7. Confirm Local Flight Map and Realtime Charts update from the same PX4 frames.
8. Land and confirm landed state returns to ground.
