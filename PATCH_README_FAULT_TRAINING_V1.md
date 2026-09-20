# UAV Studio · Fault Training V1

这是 **直接覆盖包**。把 ZIP 解压到当前 `uav-studio` 项目根目录即可；ZIP 内没有额外包装目录。

## 新增能力

- 系统调试左侧“训练场景”升级为“实训案例库”；
- 保留“自由调试”模式；
- 6 个第一批故障实训案例；
- 分类筛选、难度、建议时间、任务说明；
- 开始 / 重新开始 / 退出案例；
- 实训计时；
- 分步提示与提示扣分；
- 自动判断修复与验证状态；
- 提交诊断与 100 分过程评分；
- 综合 Pre-Arm 多故障案例；
- 调试 JSON 报告增加 training 数据；
- 后端 Pydantic 案例模型与目录校验测试。

## 安全边界

V1 的案例启动不会自动向真实 PX4 写入故障参数。

PX4 在线时：

- 电机映射案例继续使用教学执行机构映射，不发送真实电机故障测试；
- 罗盘案例使用教学传感器异常，不自动校准真实飞控；
- RC / Safety 案例先修改本地草稿，只有学生主动点击应用时才走现有 PX4 参数写入。

## 建议覆盖顺序

如果你使用前面生成的补丁：

```text
V2 基线
→ PX4 Bridge
→ 飞控与传感器
→ 遥控系统
→ 安全设置
→ 起飞前检查
→ PX4 Flight Validation
→ 本 Fault Training V1
```

本包不会覆盖 `FlightLab.vue`，因此不会撤销上一版 PX4 飞行验证闭环。

## 验证

```bash
pytest -q tests/test_training_catalog.py

cd frontend
npm run test -- fault-training
npm run build
```

完整说明：`docs/FAULT_TRAINING_V1.md`
