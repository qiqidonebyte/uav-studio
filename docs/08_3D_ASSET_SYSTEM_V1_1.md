# UAV Studio 3D Asset System V1.1

## 目标

本补丁只升级 **3D 资产与渲染层**，不改动现有 FastAPI、工程计算、SimpleSimulator、TelemetryFrame、Local Flight Map 和 Replay 数据协议。

它解决当前 `DroneScene.vue` 主要依赖 `BoxGeometry / CylinderGeometry` 所造成的“功能正确但像教学 Demo”的问题。

## 现实边界

本包模型是 **中等精度教学模型**，不是厂商 CAD，也不是照片级资产。模型能识别机架、外转子电机、ESC、CW/CCW 桨、电池、电源模块、飞控、GNSS 和云台相机，并让不同组件配置在 3D 上产生可见差异。

所有缩略图由本包 GLB 几何直接渲染，不是概念效果图。

## 当前组件映射

- `EduFrame-650` → `frame_650.glb`
- `EduFrame-450` → `frame_450.glb`
- `EduMotor-5010-360KV` → `motor_5010_360kv.glb`
- `EduMotor-4008-500KV` → `motor_4008_500kv.glb`
- `EduESC-30A / 40A` → 两种尺寸模型
- `EduProp-15x5 / 14x4.8` → 各自 CW + CCW 模型
- `EduBattery-6S-10000 / 16000` → 两种体积模型
- `EduPower-120A / 160A` → 两种电源模块
- `EduFC-V1 / V2` → 两种飞控
- `M8N` → GNSS 模型
- `EduCamera-300g` → 云台相机

## 架构

```text
DroneScene.vue
    │
    ├── AircraftRenderer.ts
    │       ├── 根据 AircraftDefinition 查当前组件
    │       ├── 读取组件安装位置
    │       ├── M1~M4 生成 4 组电机/ESC/桨
    │       └── 未安装组件使用半透明 Ghost 显示
    │
    ├── assetRegistry.ts
    │       ├── Component ID → GLB
    │       ├── Component ID → thumbnail
    │       └── M1/M3 CCW, M2/M4 CW
    │
    └── modelLoader.ts
            └── GLTFLoader + 缓存 + 材质克隆
```

## 渲染升级

V1.1 开启：

- GLB / glTF 组件模型；
- Soft Shadow；
- ACES Filmic Tone Mapping；
- sRGB 输出；
- RoomEnvironment 环境反射；
- 关键光 + 补光；
- 真实桨叶旋转（不再用圆盘）；
- 组件选中蓝色高亮；
- 未安装组件半透明 Ghost；
- 可用的跟随 / 俯视 / 侧视 / 自由相机。

## 数据原则

3D 只负责显示，不重新计算工程参数。质量、CG、推重比、续航和仿真数据仍由现有后端产生。

飞行时继续使用同一 `TelemetryFrame`：

```text
TelemetryFrame
  ├── DroneScene
  ├── LocalFlightMap
  ├── RealtimeCharts
  └── Replay
```

## 后续给学生扩展

学生增加新组件时，建议同时提交：

1. 组件工程数据；
2. GLB 模型；
3. 缩略图；
4. `assetRegistry.ts` 映射；
5. 对应测试；
6. 一份简短 ADR，说明为什么这样建模。

不要把 3D 模型路径塞进物理仿真逻辑，也不要让前端用模型尺寸替代工程参数。
