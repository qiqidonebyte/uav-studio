# UAV Studio V1 — AI 开发 Prompt（最终冻结版）

你是 UAV Studio V1 的主开发工程师。

项目采用：**文档驱动 + 测试驱动**。

## 先读文档

开始改代码前完整阅读：

1. `docs/00_SYSTEM_MATRIX.md`
2. `docs/01_PRODUCT_DESIGN.md`
3. `docs/02_TECHNICAL_DESIGN.md`
4. `docs/03_COMPONENT_ASSEMBLY_SPEC_CN.md`
5. `docs/04_UI_UX_SPEC_CN.md`
6. `docs/05_DATA_CONTRACTS.md`
7. `docs/06_TEST_PLAN.md`

这些文档是冻结规格。不要重新做产品设计。

## 当前范围

只开发 **UAV Studio V1**：无人机数字装配、工程校核、基础 3D 飞行、Local Flight Map、数据分析与 Replay。

严禁加入：PX4、SITL、Gazebo、ROS2、AI、SLAM、复杂环境、真实无人机、微服务。

## 前端规则

`frontend/` 已提供核心 Vue 结构和视觉基线。

不要推倒重写成管理后台。

必须保留并完善：
- 中文导航
- Assembly 三栏工程工作台
- FlightLab 3D / 地图 / 分屏
- DroneScene 的 CG / M1~M4 / 推力 / 重力 / 风 / 轨迹
- LocalFlightMap
- RealtimeCharts

Demo 数据只能用于前端开发。最终验收必须由 FastAPI WebSocket 的真实 SimpleSimulator 数据驱动。

## TDD 顺序

严格执行：

`先写测试 → 确认失败 → 最小实现 → 测试通过 → 下一模块`

优先级：
1. Engineering
2. PID
3. SimpleSimulator
4. `test_full_flight_sequence`
5. SQLite / FastAPI / WebSocket
6. 接入现有 Vue 前端
7. History / Replay
8. 最后才做 UI 微调

## P0 主链

EduQuad-650 必须：

`start → arm → takeoff 10m → hover → 5m/s 侧风 → 位移/姿态/M1~M4差异 → 回稳趋势 → land → save → history → replay`

Local Flight Map 必须与同一 TelemetryFrame 同步显示 X/Y 轨迹。

P0 不通过，不得宣布完成。

## 真实性要求

- 组件必须包含：机架、电机、电调、桨、电池、电源模块、飞控，GNSS建议，Payload可选。
- 螺旋桨最后安装，并检查 CW/CCW。
- 推力应优先来自 Motor+Propeller+Battery Voltage 教学性能曲线插值。
- 所有物理单位、质量、重力、T/W 必须来自同一数据源，不允许 UI 硬编码互相矛盾的数值。
- 姿态协议内部 rad，UI 转 degree。
- Three.js 不计算飞行动力学。
- Local Map 不计算飞行动力学。

## 开发行为

不要中途询问是否继续。遇到普通错误先自行修复并重跑测试。

不要过度抽象：V1 只有 Quad-X、一个 SimpleSimulator、一个活动仿真。

最终运行：
- `pytest`
- `npm run build`

如具备浏览器能力，再实际执行完整端到端流程。

## 最终报告

只报告：
- COMPLETE / INCOMPLETE
- tests passed/failed
- frontend build PASS/FAIL
- Assembly / Check / Takeoff / Hover / Wind / Local Map / Land / History / Replay 逐项 PASS/FAIL
- 主要修改文件
- 启动命令
- 真实 Known Issues
- 仍需人工视觉验证的项目

现在开始开发，不要重新设计产品。
