# UAV Studio V1 — 无人机数字设计与飞行验证平台

本项目采用：

> 文档驱动 + 测试驱动 + AI 辅助开发

当前产品闭环：

> 组件库 → 数字装配 → 工程计算 → 装配检查 → 3D基础飞行验证 → Local Flight Map → 数据分析 → Replay

## 当前阶段

已完成 3D Asset System V1.1，并进入 **P0 Test-First / Implementation Sprint 1**。

Sprint 1 重点：

- Component Visual 数据契约；
- 资产 fail-loud；
- Assembly Component Card；
- Three.js Visual Test Probe；
- 视觉变体自动验收；
- Replay 旧数据兼容。

下一轮重点：

- Frame Mount System；
- M1~M4 独立桨旋向；
- 故障组件库；
- 工程错误与3D联动；
- Golden Screenshot / CI。

## 开发前必读

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
11. `docs/10_P0_SPRINT1_IMPLEMENTATION.md`

## 测试

后端：

```bash
pytest
```

前端：

```bash
cd frontend
npm run test
npm run build
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

## V1明确不做

- PX4
- Gazebo
- ROS2
- SLAM
- AI视觉
- 复杂3D环境
- 行业巡检业务

这些属于后续 Autonomy Studio / UAV Operations。
