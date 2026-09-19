# UAV Studio V1 技术设计文档

## 1. 强制技术栈

### 前端
- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- Three.js
- ECharts
- 原生 WebSocket

### 后端
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- NumPy
- pytest

## 2. 总体架构

```text
Vue 3 中文工程工作台
  │
  ├─ REST
  └─ WebSocket
  │
FastAPI
  ├─ Engineering Core
  ├─ SimpleSimulator
  ├─ SimulationManager
  └─ Persistence
       ├─ SQLite
       └─ Telemetry JSON
```

原则：
1. Three.js 不计算飞行动力学；
2. Local Map 不计算飞行动力学；
3. 飞行状态只来自 Python SimpleSimulator；
4. 实时、History、Replay 共用同一个 TelemetryFrame；
5. V1 不提前开发 PX4 Adapter；
6. 只允许一个活动仿真。

## 3. 坐标系

Simulator：右手系
- X：前
- Y：左
- Z：上
- m / kg / N / N·m
- 姿态内部：rad

Three.js 坐标转换必须集中在 `frontend/src/three/coordinates.ts`。

Local Map 使用 Simulator 的 X/Y，不做经纬度。

## 4. Quad-X 几何与旋向

```text
                机头 +X

             M1        M2
            CCW        CW

               [FC]

             M4        M3
             CW       CCW
```

位置：
- M1 = [+L/√2, +L/√2, 0]
- M2 = [+L/√2, -L/√2, 0]
- M3 = [-L/√2, -L/√2, 0]
- M4 = [-L/√2, +L/√2, 0]

## 5. Engineering Core

至少实现：
- calculate_total_mass
- calculate_center_of_gravity
- estimate_inertia
- calculate_total_max_thrust
- calculate_thrust_weight_ratio
- estimate_hover_throttle
- calculate_max_power
- estimate_hover_power
- estimate_flight_time
- validate_configuration

CG：`Σ(mi*ri)/Σmi`

惯量采用组件点质量简化：
- Ixx = Σm(y²+z²)
- Iyy = Σm(x²+z²)
- Izz = Σm(x²+y²)

所有结果标记 `Educational Estimation`。

## 6. 动力性能模型

不能只使用 `motor.max_thrust` 而忽略桨与电池。

V1 推荐使用教学性能曲线：

`Motor + Propeller + Battery Voltage → throttle / thrust / current / power`

仿真按曲线线性插值。

如果一个组合没有可用曲线：装配校核应报错或明确降级为估算，不可静默伪造高精度结果。

## 7. SimpleSimulator

内部频率：50Hz (`dt=0.02s`)  
WebSocket：约 20Hz

状态：
- t
- position x/y/z
- velocity vx/vy/vz
- attitude roll/pitch/yaw
- angular_velocity p/q/r
- motor_outputs M1~M4
- motor_thrusts M1~M4
- battery_remaining
- armed
- flight_mode
- target_position / target_altitude
- wind_speed / wind_direction

### 推力
`Ti = profile_interpolate(ui)`；没有曲线的教学降级模型可使用 `Ti = ui² * Tmax`。

### 平移
`m dv/dt = F_total`  
`dp/dt = v`

### 转动
`I dω/dt = τ - ω × (Iω)`

### 旋翼力矩
`τi = ri × Fi`

Yaw 允许使用简化反扭矩系数。

### 风
`v_air = v_aircraft - v_wind`  
`F_drag = -k * v_air * |v_air|`

不做 CFD。

## 8. 控制器

基础教学 PID：
- Altitude
- X/Y Position
- Roll
- Pitch
- 简化 Yaw hold

最大目标倾角：±15°。

控制链：

```text
target x/y → position controller → target roll/pitch
                                    ↓
target z   → altitude controller → base throttle
                                    ↓
                      attitude controller + mixer
                                    ↓
                                M1~M4
```

## 9. 飞行状态

- IDLE
- ARMED
- TAKING_OFF
- HOVERING
- LANDING

Ground constraint：`z >= 0`。

## 10. 数据持久化

SQLite 只存：
- components
- aircraft
- simulations

高频遥测 Stop 后一次性写：
`data/simulations/{simulation_id}.json`

## 11. 前端核心

现有 `frontend/` 是视觉和交互骨架，不应推倒重写。

核心组件：
- `DroneScene.vue`：3D 数字母机、CG、推力、重力、风、轨迹
- `LocalFlightMap.vue`：基础 X/Y 地图
- `RealtimeCharts.vue`：实时数据
- `Assembly.vue`：真实顺序装配
- `FlightLab.vue`：3D / 地图 / 分屏基础试飞
- `History.vue`：历史与 Replay 入口

## 12. V2 迁移保护点

当前最重要的长期协议只有：
- AircraftDefinition
- TelemetryFrame

未来 Autonomy Studio 可以使用 PX4/Gazebo 替代 SimpleSimulator 数据源，但 UAV Studio V1 不提前实现这些技术。
