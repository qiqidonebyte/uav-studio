# Teacher Workbench V2 验证报告

## 已实际执行

### 后端流程测试

执行：

```bash
PYTHONPATH=. pytest -q tests/test_teacher_workbench_v1.py tests/test_teacher_workbench_v2.py
```

结果：`6 passed`。

覆盖：

1. 教师建班 → 学生邀请码入班；
2. 教师发布实训任务；
3. 学生创建 TrainingRun；
4. progress 过程数据与 TrainingEvent；
5. 诊断成功但尚未 Pre-Arm 的 gate；
6. Pre-Arm 后自动推进到等待飞行验证；
7. 未完成诊断时禁止伪造飞行验证；
8. 完整飞行验证后完成 TrainingRun；
9. 70/20/10 自动加权成绩；
10. 不要求飞行任务时按有效权重归一；
11. 成绩册矩阵；
12. 班级统计；
13. CSV 导出；
14. 学生/其他教师越权访问阻止；
15. 完成后的成绩锁定与 progress 幂等。

### Python 语法检查

`backend/teacher_workbench.py` 与本包测试文件全部 `py_compile` 通过。

### TypeScript / Vue script 语法

使用 TypeScript 5.8 `transpileModule` 检查：

- `frontend/src/api/teacher.ts`
- `frontend/src/types/teacher.ts`
- `frontend/src/utils/trainingFlow.ts`
- `Debugging.vue` script
- `FlightLab.vue` script
- `MyTraining.vue` script
- `TeacherWorkbench.vue` script
- 两个 V2 前端测试文件

全部通过。

### 前端状态机运行断言

独立编译并运行 `trainingFlow.ts`，验证：

- `awaiting_flight` 路由到 `/flight`；
- TrainingRun/assignment/scenario 查询参数保留；
- 未悬停、未执行降落、仍在空中均不能判定飞行验证完成；
- `起飞 + 悬停 + 降落指令 + 返回地面` 才返回通过。

结果：PASS。

## 新增前端测试

- `frontend/tests/training-flow-v2.test.ts`：3 项流程状态机测试；
- `frontend/tests/teacher-workbench-v2-contract.test.ts`：3 项实际页面接入合同测试。

因此在用户原有 80 项前端测试基础上新增 6 个测试用例。由于当前执行环境只有 overlay 而不是完整 npm checkout，未在这里声称完整前端测试总数已经执行通过。

## 已修正但需在完整仓库复跑的旧测试

用户报告的 16 个旧测试失败对应文件均已修正。本隔离 overlay 环境缺少完整 `backend/main.py` 及全部项目依赖文件，因此这些文件这里只做了 Python 语法检查；覆盖到完整仓库后必须执行一次完整 `pytest -q`，确认原 89 pass / 16 fail 被清零且没有新的回归。

## 推荐部署冒烟测试

用 1 教师 + 1 学生真实走一次：

`创建班级 → 加入班级 → 发布 F06（要求飞行） → 开始任务 → 诊断 → Pre-Arm → 进入 FlightLab → PX4 SIH 起飞/悬停/降落 → 教师成绩册出现最终分 → 导出 CSV`。
