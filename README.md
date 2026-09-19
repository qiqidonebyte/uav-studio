# UAV Studio V1 — 项目起始包

当前学期目标：开发 **UAV Studio：无人机数字设计与飞行验证平台**。

本项目采用：

> 文档驱动 + 测试驱动 + AI 辅助开发

## 当前产品边界

UAV Studio V1 只负责：

1. 真实系统级无人机组件认知与数字装配；
2. 工程参数计算与装配校核；
3. 基础 3D 飞行验证；
4. 二维 Local Flight Map；
5. 飞行数据分析与 Replay。

V1 **不负责** PX4、Gazebo、ROS2、AI、SLAM、复杂三维环境和真实行业巡检业务。这些属于后续 `Autonomy Studio` 与 `UAV Operations`。

## 开发前必读顺序

1. `docs/00_SYSTEM_MATRIX.md`
2. `docs/01_PRODUCT_DESIGN.md`
3. `docs/02_TECHNICAL_DESIGN.md`
4. `docs/03_COMPONENT_ASSEMBLY_SPEC_CN.md`
5. `docs/04_UI_UX_SPEC_CN.md`
6. `docs/05_DATA_CONTRACTS.md`
7. `docs/06_TEST_PLAN.md`
8. `docs/07_UI_VISUAL_ACCEPTANCE_SPEC_CN.md`
9. `docs/08_3D_ASSET_SYSTEM_V1_1.md`
10. `docs/09_P0_TEST_FIRST_PLAN.md`
11. `prompts/01_AI_DEVELOPMENT_PROMPT.md`

## 目录说明

- `docs/`：冻结设计、技术规格和 UI 验收标准。
- `frontend/`：Vue 3 前端与 UI/3D 测试。
- `backend/`：FastAPI + SQLite + SimpleSimulator。
- `tests/`：pytest 后端测试。
- `data/simulations/`：运行时保存遥测 JSON。
- `prompts/`：开发与验收 Prompt。

## 技术栈

- Vue 3 + TypeScript + Vite + Element Plus
- Three.js + ECharts
- Python 3.11+ + FastAPI + NumPy
- SQLite + SQLAlchemy
- pytest + Vitest + Playwright Core

## 当前开发规则

P0 阶段必须遵循：

> 规格先于测试，测试先于实现。

不允许为了让测试变绿而降低验收标准、删除测试、改成 `skip`，或用硬编码截图/假数据绕过契约。

## 最终验收主链

`装配 → 装配检查 → 起飞 → 悬停 → 侧风扰动 → 电机/姿态响应 → 基础地图轨迹 → 降落 → 历史记录 → Replay`
