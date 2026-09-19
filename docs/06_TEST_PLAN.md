# UAV Studio V1 测试计划

开发模式：**测试先行**。

## P0 — 完整飞行链

`test_full_flight_sequence.py`

默认 EduQuad-650：

1. start
2. arm
3. takeoff(10m)
4. 运行直到接近 10m 并进入 HOVERING
5. wind = 5m/s, direction = 90°
6. 验证水平偏移
7. 验证 roll/pitch 非零
8. 验证 M1~M4 输出/推力出现差异
9. 验证具有回稳趋势
10. land
11. 验证 z < 0.1m、IDLE、disarmed、电机接近0、电池下降

P0 不通过，不允许宣布项目完成。

## P1 — Engineering

- 总质量
- CG
- 惯量
- 推重比
- 悬停油门
- 电池/ESC/电压兼容
- 螺旋桨旋向
- Payload 前移引起 CG 前移
- Motor+Prop+Voltage 性能曲线插值

## P1 — PID / Simulator

- PID方向、reset、clamp
- ground constraint
- output 0~1
- battery 0~1
- 无 NaN/Inf
- takeoff / hover / land
- wind disturbance

## P1 — API

- Component list
- Aircraft create/get/calculate
- Simulation create/start/pause/reset/arm/takeoff/land/wind/stop
- WebSocket TelemetryFrame 格式

## P2 — Frontend

人工/浏览器检查：
- 中文文案
- 装配步骤与槽位
- CG 可视化
- M1~M4/旋向
- 3D 起飞
- Local Map 轨迹同步
- 3D/地图/分屏切换
- 推力箭头变化
- 风向示意
- 曲线
- History / Replay

## 最终命令

- `pytest`
- `npm run build`

必须明确区分“自动测试通过”和“需要人工视觉验证”。
