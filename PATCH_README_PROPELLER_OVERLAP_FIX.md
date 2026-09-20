# UAV Studio — Propeller Overlap Fix 2.0.1

基线：

- GitHub: `qiqidonebyte/uav-studio`
- Branch: `main`
- HEAD: `df88d9e3e4cb02138cbda1cbf631c7fdc2bad4d2`

本包解决 Realistic Edition 2.0 中的螺旋桨显示/装配干涉问题，并增加回归测试。

## 修复内容

### 1. 螺旋桨中心结构

Realistic Edition 2.0 中：

- Motor GLB 有 `prop_adapter + prop_nut`
- Propeller GLB 又有 `washer + nut`

两个组件在同一轴线上重复建模，会造成桨毂附近的几何穿插。

2.0.1 改成单一所有权：

- Motor：shaft + adapter + retaining nut
- Propeller：annular hub + blade only

Propeller hub 现在有真实中心孔，不再是实心圆柱。

### 2. 桨叶尺寸

桨叶扫掠半径现在按工程尺寸归一化：

- 15 inch = 0.3810 m
- 14 inch = 0.3556 m

GLB 的实际扫掠直径与组件参数一致，不再因为 chord / sweep 改变视觉直径。

### 3. Motor / Prop 统一安装基准

5010 与 4008 的视觉桨安装面统一为：

`Y = 0.064 m`

与当前 `AircraftRenderer` 的 `propellerOffsetY()` 契约一致。

### 4. 机架 / 桨盘碰撞保护

`asset_manifest.json` 新增视觉装配 Fit Contract：

- Frame 650 motor diagonal = 0.65 m
- Frame 450 motor diagonal = 0.45 m
- Prop 15 swept diameter = 0.381 m
- Prop 14 swept diameter = 0.3556 m

后端 `p0_validation.py` 会对这些已知 GLB 资产做真实桨盘间距检查。

例如：

- 650 + 15"：净间隙约 78.6 mm → 允许
- 450 + 14"：重叠约 37.4 mm → `PROPELLER_FRAME_OVERLAP` 阻断

阻断后不能创建飞行仿真。

### 5. 前端装配步骤

`PROPELLER_FRAME_OVERLAP` 已映射到“螺旋桨”步骤，因此该步骤和最终装配检查会显示错误状态。

## 使用

解压 ZIP 到当前 `uav-studio` 根目录，按目录覆盖。

本包不会覆盖：

- `DroneScene.vue`
- `AircraftRenderer.ts`
- 爆炸视图
- 爆炸标签
- 组件库页面
- 设置页面

因此可以直接叠加到你当前已经做过爆炸视图等修改的本地版本。
