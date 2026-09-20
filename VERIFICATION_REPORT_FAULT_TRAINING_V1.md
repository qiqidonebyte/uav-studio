# Verification Report · Fault Training V1

## 已在当前制品环境完成

- Python `backend/training/catalog.py` 编译：PASS
- Pydantic 案例目录测试：2/2 PASS
- 6 个案例 ID 唯一性：PASS
- 综合案例覆盖 RC / 动力 / 安全 / Preflight：PASS
- `training.ts` TypeScript 语法：PASS
- `Debugging.vue` script TypeScript 语法：PASS
- `Debugging.vue` template 标签平衡检查：PASS
- 评分运行时检查：PASS
  - 全条件完成：100
  - 1 次提示 + 2 次失败操作：86
- 初始自由调试场景：`standard`，不再默认注入电机映射故障
- 教学电机映射案例在 PX4 live 时不调用真实 `MAV_CMD_ACTUATOR_TEST` 分支
- 教学罗盘案例在 PX4 live 时不自动发送真实校准命令
- 案例启动函数无 `px4Api.setParameter` / `testMotor` / `calibrateSensor` 自动写调用
- ZIP 根目录结构将在打包时再次检查

## 当前环境未声称完成

当前制品环境没有完整项目 `node_modules` 和正在运行的 PX4 SIH，因此不声称：

- 全量 `npm run build` 已执行；
- 全量现有 Vitest / Playwright 已执行；
- 真实 PX4 SIH 端到端案例运行已执行。

这些应在项目开发机覆盖后执行。
