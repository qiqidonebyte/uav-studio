# UAV Studio 3D Asset System V1.1 — 覆盖包

适配仓库：`qiqidonebyte/uav-studio`，制作时对应 `main` 提交 `5d6128366c56d1634e98245b9bfd53dd41c434f3`。

## 使用方法

先备份或提交你当前未提交改动，然后把本 ZIP **解压到项目根目录**，允许覆盖同名文件。

本包会覆盖：

- `frontend/src/components/DroneScene.vue`

本包会新增：

- `frontend/src/three/AircraftRenderer.ts`
- `frontend/src/three/assetRegistry.ts`
- `frontend/src/three/modelLoader.ts`
- `frontend/public/models/uav/v1_1/**`
- `frontend/tests/asset-registry.test.ts`
- `docs/08_3D_ASSET_SYSTEM_V1_1.md`

不会覆盖后端工程计算、仿真器、Assembly / FlightLab / Replay 页面和现有数据协议。

## 解压后建议执行

```bash
cd frontend
npm install
npm run test
npm run build
```

然后从项目根目录运行原有后端与前端，重点检查：

1. 装配页中央 3D 已从基础几何体切换为 GLB 组件；
2. 650 ↔ 450 机架外形尺寸明显不同；
3. 5010 ↔ 4008 电机尺寸不同；
4. 15 ↔ 14 英寸桨叶长度不同，并且 CW/CCW 为不同模型；
5. 10000 ↔ 16000mAh 电池体积不同；
6. 点击 3D 组件仍然同步右侧检查器；
7. 未安装组件呈半透明 Ghost；
8. 飞行实验的姿态、推力箭头、风、轨迹继续由后端 TelemetryFrame 驱动；
9. 跟随 / 俯视 / 侧视 / 自由视角可用；
10. History / Replay 不应受影响。

## 提交建议

```bash
git add .
git commit -m "feat: upgrade UAV Studio 3D asset system to v1.1"
git push
```

你 push 到 GitHub 后，可以再让 ChatGPT 直接针对提交后的仓库做第二轮代码 Review。

## 模型边界

这些是教学用通用外形，不对应 T-Motor、Pixhawk、Sony 等具体厂商产品的精确 CAD。目的在于让数字装配“看得出真实部件和配置变化”，而不是做照片级广告渲染。
