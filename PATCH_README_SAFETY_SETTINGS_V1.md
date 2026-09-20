# UAV Studio 安全设置 V1 — 直接覆盖包

基线：
- UAV Studio V2 调试工作台
- PX4 Bridge V1
- 飞控与传感器 V1

本补丁只补齐“安全设置”页面，不修改 Gazebo、不引入 ROS2/MAVSDK，也不增加第三方依赖。

## 直接覆盖

ZIP 根目录直接包含：

- `frontend/src/views/Debugging.vue`
- `frontend/src/utils/debugging.ts`
- `frontend/src/utils/safety.ts`
- `frontend/tests/debugging-workbench.test.ts`
- `frontend/tests/safety-settings.test.ts`
- `docs/SAFETY_SETTINGS_V1.md`

请在 UAV Studio 项目根目录直接解压覆盖。

## 已实现

1. RC / 手动控制失联保护
   - COM_RC_LOSS_T
   - NAV_RCL_ACT
   - COM_FAIL_ACT_T

2. 数据链路失联保护
   - COM_DL_LOSS_T
   - NAV_DLL_ACT

3. 低电量保护
   - BAT_LOW_THR
   - BAT_CRIT_THR
   - BAT_EMERGEN_THR
   - COM_LOW_BAT_ACT
   - COM_ARM_BAT_MIN

4. RTL / 地理围栏
   - RTL_RETURN_ALT
   - GF_MAX_HOR_DIST
   - GF_MAX_VER_DIST
   - GF_ACTION

5. 解锁 / 自动上锁
   - COM_ARMABLE
   - COM_ARM_WO_GPS
   - COM_DISARM_PRFLT
   - COM_DISARM_LAND

6. 安全策略检查
   - 电池 Low > Critical > Emergency
   - RTL 高度与垂直围栏冲突
   - 失联保护禁用提醒
   - 低电量仅告警提醒
   - 无 GPS 解锁提醒
   - 围栏禁用/无动作提醒
   - Terminate / 飞行中 Disarm 高风险策略拦截

7. 参数工作流
   - 从真实 PX4 顺序读取参数
   - 本地草稿编辑
   - 待应用项计数
   - 飞机已解锁时禁止安全参数写入
   - 一次性应用修改项
   - PX4 PARAM_VALUE 回读
   - Pre-Arm 验证

8. Failsafe 教学场景
   - 初始注入错误的教学参数组合
   - 学生诊断并修复
   - 应用后恢复教学评分和 Pre-Arm 状态

## 注意

“教学推荐值”是课程演示用的安全基线，不是对所有真实机型/场地的通用飞行建议。
真实飞行前仍需根据机体、法规、飞行场地、任务和 PX4 固件版本进行工程复核。
