# UAV Studio P0 Sprint 1 — 高优先级实现

基线：`efa94f78f830be0e3e4bce79e6b72ae5f140cf23`

本轮目标：把上一轮 Test-First 中最高优先级的 RED 转为 GREEN，同时不扩展 V1 产品边界。

## 已实现

### 1. Component Visual 成为 API 数据契约

`Component` 新增：

```text
visual
├── asset_key
├── file
├── cw_file
├── ccw_file
├── thumbnail
└── scale
```

资产文件名来自已提交的：

`frontend/public/models/uav/v1_1/asset_manifest.json`

后端 seed 将 manifest 中的视觉元数据持久化到已有 `parameters_json._visual`，API 层再暴露为第一类 `Component.visual`。

这样不需要 SQLite schema migration，也可以升级已有本地数据库。

### 2. 前端不再使用 numeric Component ID 作为运行时 3D Source of Truth

旧结构：

```text
component.id = 10
→ assetRegistry.ts 硬编码
→ motor_5010_360kv.glb
```

新结构：

```text
asset_manifest.json
→ Component.visual
→ AircraftRenderer
```

空槽 Ghost 仍允许使用按类别定义的教学占位资产，但**已安装组件没有 visual 时必须报错**。

### 3. Missing Asset 改为 Fail Loud

删除正式组件的基础几何体 silent fallback。

如果组件缺少 visual 或 GLB 无法加载：

- Console 报错；
- 3D工作区显示“3D资产加载失败”；
- Visual Test Probe 标记 `sceneReady=false`。

### 4. Assembly Component Card

组件选择不再以 `<select>` 为主要交互。

每张卡片显示：

- GLB真实缩略图；
- 名称；
- 质量；
- 两项关键工程参数；
- 当前安装状态；
- 安装 / 更换按钮。

并提供稳定的 `data-testid` 供 UI 自动测试使用。

### 5. Three.js Visual Test Probe

开发/测试模式暴露：

```text
window.__UAV_VISUAL_TEST__
```

可读取：

- loadedAssets；
- aircraftBounds；
- partBounds；
- M1~M4 mount 快照；
- cameraMode；
- selectedSlot；
- renderer pixelRatio；
- sceneReady。

Probe 只读取真实运行状态，不参与业务计算。

### 6. Replay向后兼容

旧实验 JSON 没有 `Component.visual`。

Replay 加载时只补视觉元数据，不修改历史工程参数和历史 Telemetry，因此旧实验仍可回放。

## 本轮没有实现

以下继续保留到 Sprint 2：

1. Frame mount_points 成为 Engineering / Simulator / Renderer 唯一安装坐标；
2. M1/M2/M3/M4 独立 CW/CCW 桨安装；
3. 故障组件库；
4. ERROR/WARNING 点击后定位具体 3D 部件；
5. Golden Screenshot；
6. GitHub CI。

## Sprint 1 验收

建议运行：

```bash
pytest

cd frontend
npm run test
npm run build
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

本轮目标是上述 P0 Asset / UI / Scene Contract 转为 GREEN。
