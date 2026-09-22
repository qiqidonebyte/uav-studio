# 测试与教学实践验收 V1

## 目的与边界

本版本功能冻结，验收对象是《无人机装调检修》的“装—调—检—修—验”学习闭环。覆盖的含义不是为每一行代码增加低价值断言，而是让每个核心学习任务、角色边界、关键拒绝条件和数据留痕都有可复现证据。

虚拟平台用于参数调整、故障复现、状态观察与反复试错；实体实训用于机械安装、紧固、线路连接、设备检查和安全规范。不得把虚拟通过等同于实体放飞许可。

## 发布前执行顺序

```bash
# 仓库根目录：后端逻辑与 HTTP 接口
PYTHONPATH=/path/to/.venv/lib/python3.12/site-packages python3 -m pytest -q

# frontend：纯逻辑、组件契约及类型/生产构建
cd frontend
npm test -- --run
npm run build
```

浏览器回归需要真实浏览器和正在运行的服务，另开两个终端：

```bash
# 终端 A，仓库根目录
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 终端 B
cd frontend
npm run dev -- --host 127.0.0.1 --port 5174

# 终端 C
cd frontend
P0_BROWSER_PATH=/path/to/chrome npm run test:browser
```

Windows 可省略 `P0_BROWSER_PATH`（脚本会寻找 Edge/Chrome）；若管理员密码不是默认值，使用 `E2E_ADMIN_PASSWORD` 注入，不把密码写入测试文件。`test:browser` 每项均在新浏览器上下文登录，不依赖个人浏览器中遗留的 Cookie。视觉截图命令 `npm run test:p0:capture` 是人工审阅素材，不作为通过门槛。

## 自动化覆盖地图

| 学习/管理环节 | 通过证据 | 自动化位置 |
| --- | --- | --- |
| 注册、登录、退出、会话隔离 | HttpOnly 会话、匿名拒绝、重复用户/错误密码拒绝、工作区回归 | `test_auth_api_routes.py`、`test_auth_workspace.py`、`e2e-auth.mjs` |
| 飞机与组件库 | 模板、创建、复制、编辑、删除、每用户 10 架上限、组件筛选/预览 | `test_aircraft_library.py`、`test_library_settings_api.py`、`e2e-aircraft-library.mjs`、`e2e-component-library.mjs` |
| 数字装配与工程校核 | 7 步、物理安装点、装配缺失阻断、质量/重心/续航重新计算 | `assembly*.test.ts`、`digital-assembly*.test.ts`、`test_engineering.py`、`e2e-assembly.mjs`、`e2e-digital-assembly.mjs` |
| 任务导航与训练记录 | 同一任务上下文、阶段门禁、工作单证据链、复盘归属 | `learning-guide-v1.test.ts`、`training-context.test.ts`、`training-flow-v2.test.ts`、`learning-shell-regression.test.ts` |
| 系统调试与故障诊断 | 传感器、RC、动力、安全参数、故障案例、起飞前检查 | `debugging-workbench.test.ts`、`fault-training.test.ts`、`rc-system.test.ts`、`virtual-rc.test.ts`、`debug-motor-ground.test.ts`、`safety-settings.test.ts`、`preflight-gate.test.ts` |
| 虚拟遥控与动力安全 | Mode 2 摇杆回中/油门保持、固定地面模型、单电机测试、全部停止、已解锁拒绝 | `P0-UI-017`、`virtual-rc.test.ts`、`debug-motor-ground.test.ts`、`test_px4_bridge_optional_dependency.py`、`test_px4_service_routes.py` |
| 飞行验证、记录、回放 | Start→Arm→Takeoff→Land 门禁、地图、记录、回放、PX4 高度换算 | `flight-*.test.ts`、`px4-flight-lab.test.ts`、`test_full_flight_sequence.py`、`e2e-flight-controls.mjs`、`e2e-flight.mjs` |
| 教师、学生、管理员闭环 | 班级/任务/TrainingRun、成绩册、CSV、角色权限、任务锁定 | `test_teacher_workbench_v1.py`、`test_teacher_workbench_v2.py`、`teacher-workbench-v2-contract.test.ts`、`e2e-teacher-workbench.mjs` |
| 课堂可靠性 | 12 槽位、FIFO、队列刷新、释放晋级、重启恢复、幂等、并发/SQLite WAL | `test_classroom_reliability_v1.py`、`px4-session.test.ts` |
| P0 页面可用性 | 学习页布局、1366×768 工作区、滚动、3D 场景与资产契约 | `p0-ui-contract.mjs`、`p0-scene-contract.mjs`、`p0-asset-contract.test.ts` |

## 浏览器 Golden Path

`npm run test:browser` 顺序验证以下真实交互：

1. 注册、登录、退出、重进工作区；
2. 管理员登录后创建/复制/改名/删除飞机，确认保存；
3. 组件卡片、数字装配、四个独立安装位与空间警告；
4. 组件库筛选、3D 预览与兼容关系；
5. 起飞控制门禁，以及完整飞行—地图—历史—回放；
6. 设置持久化，以及教师/管理员工作台的各管理视图；
7. P0 UI 和三维场景契约；其中包含虚拟遥控器拖动、松手与失焦回中。

若任意浏览器项失败，记录浏览器版本、分辨率、URL、账号角色、操作步骤、控制台错误与截图；修复后应先运行失败项，再运行完整 `test:browser`。

## 人工课堂验收（35 人、2 周、8 课时）

### 课前：教师与管理员

- 管理员确认学生、教师、管理员三个入口及越权跳转；创建班级和任务，检查任务说明与截止设置。
- 教师在成绩册确认每名学生的 TrainingRun、阶段、分数和导出 CSV；不得出现跨学生数据。
- 用 13 个任务申请 PX4，确认前 12 个获得槽位、第 13 个显示排队；释放一个槽位，确认队首晋级。
- 断开一项 PX4 会话或重启后端，确认训练记录未丢失且学生收到可理解的恢复/排队状态。

### 课中：每位学生最小路径

1. 从“我的实训”进入指定任务，核对导航显示当前阶段和下一步。
2. 完成机架→动力→供电→飞控/导航→载荷→螺旋桨→装配检查；确认桨叶最后安装。
3. 在系统调试完成传感器、RC、动力和安全参数。动力页模型必须在地面，只有对应测试桨叶转动；点击“全部停止”后四桨立即停止。
4. 在虚拟遥控器拖动左右摇杆：右杆与偏航松手回中，油门保持；再执行回中/油门最低。
5. 有指导地制造一个故障，填写诊断工作单并提交；缺少证据时应被阻止，补齐后成功提交。
6. 完成起飞前检查和飞行验证；未完成前置条件时，起飞按钮必须不可用。
7. 在复盘页核对本次时间线、错误操作、提示、工作单和成绩均属于本次任务。

### 课后：实体实践与数据归档

- 仅将通过虚拟预训的学生进入实体分组；实体阶段另行执行机械、紧固、连接、设备检查与安全规范，不直接使用虚拟仿真结果作为放飞授权。
- 每次训练记录：学生匿名编号、班级/任务、起止时间、完成状态、首次通过、错误次数、提示次数、总耗时、诊断提交结果、飞行验证结果、教师观察和问题编号。
- 对每个问题保留一项可复核证据（截图、时间线或服务器日志）。论文统计可据此计算首次通过率、平均耗时、错误/提示次数，并用于实体实训分组指导。

## 通过判定

- 自动化：`pytest`、`npm test`、`npm run build` 全部通过；
- 浏览器：完整 Golden Path 在目标部署浏览器通过；
- 课堂：三种角色、学生最小路径及 12/13 槽位演练均有记录；
- 安全：没有把虚拟动力测试或 PX4 验证误写成实体放飞许可。

任何一项未通过时，本版本为“教学试用待修复”，不得标记为正式课堂版本。
