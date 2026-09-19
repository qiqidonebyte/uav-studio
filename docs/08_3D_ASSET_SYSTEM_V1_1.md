# UAV Studio 3D Asset System V1.1

状态：**已接入；P0 Sprint 1 已完成运行时数据契约升级**

## 目标

3D资产层只负责显示：

- 机架；
- 电机；
- ESC；
- CW/CCW 螺旋桨；
- 电池；
- 电源模块；
- 飞控；
- GNSS；
- 任务载荷。

质量、CG、推重比、功率、续航和飞行状态仍来自后端工程模型与 `TelemetryFrame`。

## 现实边界

当前资产是**中等精度教学模型**，不是厂商 CAD，也不是照片级渲染。

目标是：

> 组件类别看得懂、不同配置看得出、工程变化能解释。

而不是展示每颗螺丝或真实品牌外观。

## P0 Sprint 1 后的资产数据流

运行时不再由前端根据 numeric Component ID 硬编码正式组件模型。

```text
asset_manifest.json
        ↓
backend.seed
        ↓
Component.visual
        ↓
assetRegistry.ts（校验 / URL 解析）
        ↓
AircraftRenderer.ts
        ↓
DroneScene.vue
```

`asset_manifest.json` 负责：

- GLB 文件名；
- CW / CCW 文件；
- thumbnail；
- 资产版本、单位和坐标说明。

后端把这些信息作为 `Component.visual` 暴露给前端。

## Component.visual

```text
visual
├── asset_key
├── file
├── cw_file
├── ccw_file
├── thumbnail
└── scale
```

工程参数和视觉参数严格分开。

物理算法禁止读取 `visual`。

## SQLite向后兼容

为了避免本学期中途要求学生重建数据库，视觉元数据持久化在已有：

```text
components.parameters_json._visual
```

API序列化时 `_visual` 被隐藏，只向前端公开：

```text
Component.visual
```

`parse_component_parameters()` 会忽略 `_visual`，因此它不参与工程计算。

## Fail Loud

已安装 Component 如果：

- 没有 `visual`；
- 没有 file / CW / CCW；
- GLB加载失败；

系统不允许偷偷换成另一个组件模型。

应：

1. Console 报错；
2. 3D工作区显示资产异常；
3. Visual Test Probe `sceneReady=false`。

只有**空安装槽 Ghost**可以使用类别级教学占位资产。

## Renderer职责

`AircraftRenderer.ts`：

- 根据 AircraftDefinition 找当前 Component；
- 读取 `Component.visual`；
- 加载 GLB；
- M1~M4 生成四组动力组件；
- 使用 CW/CCW 模型；
- 未安装部件显示 Ghost；
- 维护选中高亮；
- 提供 raycast meshes；
- 提供自动测试用资产/bounds快照。

`DroneScene.vue`：

- Three.js Scene / Camera / Lighting；
- Telemetry姿态；
- 推力、重力、风、轨迹；
- 相机模式；
- Visual Test Probe；
- 资产错误UI。

## Visual Test Probe

开发/测试模式提供：

```text
window.__UAV_VISUAL_TEST__
```

它只读取真实场景：

- loadedAssets
- aircraftBounds
- partBounds
- mounts
- cameraMode
- selectedSlot
- pixelRatio
- sceneReady

Probe 不得制造假数据用于“骗过测试”。

## 当前仍未统一的安装坐标

P0 Sprint 1 **尚未**完成 Engineering / Simulator / Renderer 的统一 Frame Mount System。

当前 M1~M4 水平位置仍由 `motor_diagonal_m` 派生；其他部分位置仍使用现有 frame 参数。

下一轮必须先写 Mount Contract RED tests，再完成：

```text
Frame.mount_points
        ├── Engineering
        ├── Simulator
        └── AircraftRenderer
```

## Replay

新实验记录保存 `Component.visual`。

旧实验 JSON 没有视觉元数据时，后端 Replay 加载器只补当前视觉信息，不修改历史：

- 质量；
- 工程参数；
- AircraftDefinition；
- TelemetryFrame。

因此旧实验保持可回放。
