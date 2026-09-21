# UAV Studio · Teacher Workbench V2

基线：GitHub `qiqidonebyte/uav-studio` main，检查时最新合并提交 `f15a92c5525d99e83477e3a000f91ed1539117ed`。

## 本次目标

把 Teacher Workbench V1 从“班级/任务/记录”推进为完整课程闭环：

`教师发布任务 → 学生开始 TrainingRun → 故障诊断过程自动记录 → Pre-Arm → PX4/教学模拟飞行验证 → TrainingRun 完成 → 自动课程成绩 → 教师成绩册/班级分析/CSV 导出`

## 关键改动

### 1. TrainingRun 全过程状态机

新增/明确阶段：

- `diagnosis` / `in_progress`：故障诊断中
- `awaiting_prearm`：诊断已通过，等待 Pre-Arm
- `awaiting_flight`：诊断与 Pre-Arm 已通过，等待飞行验证
- `completed`：全部要求完成，成绩锁定

已完成记录对后续 progress/submit 做幂等保护，避免复盘操作覆盖正式成绩。

### 2. 现有 Debugging 真正接入课程任务

`/debugging?run=<id>&scenario=<id>&assignment=<id>` 会：

- 自动加载教师指定案例；
- 禁止切换为其他案例/自由调试来绕过任务；
- 自动同步访问模块、成功条件、提示、错误、用时和 Pre-Arm；
- 提交诊断后根据任务要求进入 `awaiting_prearm` / `awaiting_flight` / `completed`；
- 进入 FlightLab 时保留 TrainingRun 上下文。

### 3. FlightLab 自动完成飞行验证

课程任务进入 FlightLab 后，系统记录完整的：

`起飞 → 悬停 → 执行降落 → 返回地面`

只有观察到完整序列才调用 flight-validation API。PX4 SIH 和原教学模拟均支持；同步失败时界面提供“重新同步飞行结果”。

### 4. 自动课程成绩

默认权重：

- 案例诊断成绩 70%
- 飞行验证 20%
- 规范操作 10%

规范操作分采用简单可解释规则：`100 - 提示×10 - 错误操作×5`，最低 0。

若教师不要求飞行验证，则仅对有效权重归一到 100 分，不让“未启用模块”白白丢分。

### 5. 教师成绩册与班级分析

教师工作台新增“课程成绩”：

- 学生 × 实训任务成绩矩阵；
- 每格可查看 TrainingRun；
- 班级完成率、均分、首次通过率、平均用时、平均错误、飞行验证率；
- 每个任务的完成率/均分/首次通过率；
- Excel 可直接打开的 UTF-8 BOM CSV 导出。

### 6. 修复旧后端测试与认证改造不同步

没有削弱生产认证。修改测试以适配当前真实接口：

- `tests/test_api.py`：测试客户端先登录 admin；
- `tests/test_experiments_api.py`：测试客户端先登录 admin；
- `tests/test_visual_contracts.py`：API 合同测试先登录；
- `tests/test_library_settings_api.py`：注入新的 `get_current_user`；
- `tests/test_user_settings_feature.py`：更新 `read_settings(record)`、`write_settings(session, record, settings)`、`change_password(session, record, ...)` 调用。

## 部署

这是 direct overlay 包：解压后根目录直接是 `backend/`、`frontend/`、`tests/`。

覆盖当前仓库后建议：

```bash
# 后端
pytest -q

# 前端（按项目现有命令）
npm test
npm run build
```

本版没有新增数据库表，继续使用 V1 的 Assignment / TrainingRun / TrainingEvent 表；V2 的评分明细保存在 TrainingRun `result_json.grading` 中，因此不需要手工迁移数据库。
