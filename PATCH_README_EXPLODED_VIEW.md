# UAV Studio — 爆炸视图 + 紧凑组件标签实现包

## 云端基线

本包重新以 GitHub `qiqidonebyte/uav-studio` 的 `main` 为基线校验。

HEAD：

`df88d9e3e4cb02138cbda1cbf631c7fdc2bad4d2`

基线关键文件 blob SHA 记录在 `BASELINE_GITHUB.json`。

## 本次实现

### 1. 爆炸视图组件名称标签

标签只在爆炸视图展开超过 72% 后出现。

设计原则：

- 读取真实 `Component.name`；
- 每种组件只显示一个标签；
- 电机 / 电调 / 螺旋桨显示为 `×4`，避免 12 个标签堆满画面；
- 未安装 Ghost 不显示标签；
- 标签固定在场景左右边缘列，尽量不盖住中央 3D 飞机；
- 标签根据 3D 部件的屏幕投影高度排序；
- 同列自动做碰撞消解；
- 标签尺寸固定为 164 × 26 px；
- 名称过长自动省略号；
- 选中组件蓝色描边；
- 工程问题红色描边。

示例：

`电机 ×4  EduMotor-5010-360KV`

### 2. 删除 GLB 教学模型角标

原来的右上角：

`GLB 教学模型`

已完全删除，避免遮挡后方文字。

3D 资产加载失败的错误面板仍然保留。

### 3. 爆炸视图原功能保留

- 机架固定；
- GNSS / 飞控向上；
- 桨 / 电机 / 电调向外分层；
- 电池 / 电源 / 载荷向下；
- 平滑展开 / 收拢；
- 爆炸状态仍可点击 3D 部件；
- 工程错误高亮继续有效；
- 顺 / 逆时针文字只在螺旋桨步骤的整机模式显示。

## 覆盖方式

把 ZIP 解压到当前 `uav-studio` 根目录覆盖。

## 本包文件

- `frontend/src/components/DroneScene.vue`
- `frontend/src/three/AircraftRenderer.ts`
- `frontend/src/three/explodedView.ts`
- `frontend/src/three/explodedLabels.ts`
- `frontend/src/three/explodedLabelLayout.ts`
- `frontend/src/types/visual-test.d.ts`
- `frontend/tests/exploded-view.test.ts`
- `frontend/tests/exploded-labels.test.ts`
- `frontend/tests/p0-scene-contract.mjs`
- `frontend/tests/p0-visual-capture.mjs`
- `tools/verify_exploded_view.py`
- 规格 / 测试文档

## 本地完整回归

```bash
cd frontend
npm run build
npm run test
npm run test:p0:scene
npm run test:p0:capture
npm run e2e
npm run e2e:flight
```
