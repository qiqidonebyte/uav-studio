# UAV Studio V1 数据协议

## 1. Component

```json
{
  "id": 1,
  "name": "EduMotor-5010",
  "type": "motor",
  "mass_kg": 0.18,
  "parameters_json": {}
}
```

`type` 允许：
`frame | motor | esc | propeller | battery | power_module | flight_controller | gnss | payload`

## 2. AircraftDefinition

```json
{
  "id": 1,
  "name": "EduQuad-650",
  "frame_id": 1,
  "motor_id": 10,
  "esc_id": 20,
  "propeller_id": 30,
  "battery_id": 40,
  "power_module_id": 50,
  "flight_controller_id": 60,
  "gnss_id": 70,
  "payload_id": 80,
  "payload_position_m": {"x": 0.1, "y": 0.0, "z": -0.1}
}
```

## 3. TelemetryFrame（冻结）

```json
{
  "t": 0.0,
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
  "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
  "angular_velocity": {"p": 0.0, "q": 0.0, "r": 0.0},
  "center_of_gravity": {"x": 0.0, "y": 0.0, "z": 0.0},
  "motors": {
    "outputs": [0.0, 0.0, 0.0, 0.0],
    "thrusts_n": [0.0, 0.0, 0.0, 0.0]
  },
  "forces": {
    "gravity_n": 0.0,
    "total_thrust_n": 0.0
  },
  "wind": {
    "speed_mps": 0.0,
    "direction_deg": 0.0
  },
  "power": {
    "estimated_power_w": 0.0,
    "battery_remaining": 1.0,
    "voltage_v": 0.0,
    "current_a": 0.0
  },
  "armed": false,
  "flight_mode": "IDLE"
}
```

约束：
- attitude / angular_velocity 内部使用 rad / rad/s；
- UI 转换为 degree；
- 实时、保存、Replay 不得另建第二套格式。

## 4. 坐标

Simulator：X前、Y左、Z上。  
Local Map：直接使用 X/Y 米制坐标。  
Three.js 转换只允许在 `three/coordinates.ts` 中集中处理。
