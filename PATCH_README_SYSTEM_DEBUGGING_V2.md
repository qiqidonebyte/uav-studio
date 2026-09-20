# UAV Studio — 系统调试工作台 V2 覆盖包

本覆盖包基于 `qiqidonebyte/uav-studio` 当前 `main` 分支结构制作，目标是把此前偏“飞前检查”的调试页面改造成真正具有操作反馈的教学调试工作台。

## 覆盖方式

在 UAV Studio 仓库根目录解压本 ZIP，选择覆盖同名文件即可。

本包不会修改 SQLite 数据库结构，也不会删除现有装配、飞行实验、实验记录或组件库功能。

## 新增/替换文件

- `frontend/src/views/Debugging.vue` — 系统调试主页面
- `frontend/src/components/DebugMotorScene.vue` — 调试专用 3D 飞机包装层
- `frontend/src/utils/debugging.ts` — 教学故障映射与评分逻辑
- `frontend/src/router/index.ts` — 增加 `/debugging` 路由
- `frontend/src/App.vue` — 顶部增加“系统调试”入口与桥接状态提示
- `frontend/tests/debugging-workbench.test.ts` — 教学场景单元测试

## 当前真实实现

### 动力系统调试

- 直接使用当前用户所选择的飞机设计；
- 读取现有工程计算数据：推重比、悬停油门、最大电流、ESC 裕量、电池裕量；
- 使用现有 Three.js / GLB 数字飞机；
- M1–M4 单电机测试会真正驱动现有 3D 旋翼动画；
- 显示执行机构输出百分比；
- 显示电机位置、旋向和当前响应；
- 支持“电机映射故障”教学场景：M1 指令实际驱动 M3；
- 支持学生执行映射修复并进行二次测试；
- 记录调试过程与评分；
- 可导出 JSON 调试记录；
- 可直接进入现有飞行实验页面进行验证。

### 训练场景

- 标准调试
- 电机映射故障
- 罗盘异常
- Failsafe 异常

动力系统为本版本完整实现模块；飞控与传感器、遥控系统、安全设置、起飞前检查已经建立界面入口和教学模块骨架，后续用于接 PX4 SITL/MAVLink 实际状态。

## PX4 / Gazebo 边界

本版本 **没有伪装已经连接 PX4 或 Gazebo**。

界面显示：

- `PX4 SITL · 教学模拟`
- `Gazebo · 待接入`

当前 M1–M4 测试由 UAV Studio 自身数字飞机完成，用于验证教学交互和课程流程。下一阶段可将相同按钮背后的执行逻辑替换为 MAVLink/MAVSDK/PX4 Bridge，而不需要重做页面。

## 建议验证

```bash
cd frontend
npm install
npm run test
npm run build
```

建议重点检查：

1. 登录后顶部出现“系统调试”；
2. `/debugging` 可正常打开；
3. 当前飞机及其工程参数正确显示；
4. 选择“电机映射故障”；
5. 点击“测试 M1”时，3D 视图实际 M3 旋翼转动；
6. 点击“修复映射”后二次测试恢复 M1；
7. “进入飞行验证”可跳转到现有 `/flight`。
