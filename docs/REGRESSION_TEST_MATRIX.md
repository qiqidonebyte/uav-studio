# 装调检修回归测试矩阵

本表用于每次覆盖部署前的最小验收。原则：简单、有效、不过度设计；只保留能证明学习过程和系统可靠性的检查。完整执行顺序、浏览器 Golden Path 与课堂人工验收见 [测试与教学实践验收 V1](./TEST_AND_TEACHING_ACCEPTANCE_V1.md)。

| 学习环节 | 必须通过的行为 | 自动化覆盖 |
| --- | --- | --- |
| 登录与角色 | 学生、教师、管理员进入各自入口；越权请求被拒绝 | `test_auth*`、`test_teacher_workbench*` |
| 飞机与组件库 | 可选飞机、组件信息完整、设计可保存 | `aircraft-library.test.ts`、`component-library.test.ts` |
| 无人机装配 | 安装、Mount、空间检查、工程验证形成连续流程 | `assembly*.test.ts`、`digital-assembly.test.ts` |
| 任务导航 | 装—调—检—修—验入口可达；不把“经过页面”误标为完成 | `learning-guide-v1.test.ts`、`learning-shell-regression.test.ts` |
| 训练上下文 | 从任务进入后，装配、调试、飞行、复盘始终属于同一训练记录 | `training-context.test.ts` |
| 传感器调试 | 状态读取、校准门禁、故障案例和日志正常 | `debug-sensors.test.ts`、`debug-scenarios.test.ts` |
| 遥控调试 | 真实遥控器底图与交互热区对齐；Mode 2 双摇杆可拖动；右杆及偏航在松手、失焦时回中，油门保持；通道映射、校准和上锁门禁正常 | `rc-system.test.ts`、`virtual-rc.test.ts`、`P0-UI-017` |
| 动力系统 | 飞机固定在地面；仅测试桨叶转动；“全部停止”立即停转；解锁时禁止测试 | `debug-motor-ground.test.ts`、`test_px4_bridge_optional_dependency.py` |
| 安全与参数 | 参数修改有校验，危险状态禁止写入 | `debug-safety-parameters.test.ts`、`debug-parameter-validation.test.ts` |
| 起飞前检查 | 六项门禁、许可有效期及飞机配置指纹正确 | `preflight*.test.ts`、`flight-control-guards.test.ts` |
| 诊断工作单 | 按任务出现、默认折叠、草稿可保存、提交时校验证据链 | `diagnosis-worksheet.test.ts`、`training-flow.test.ts` |
| 飞行验证 | 未完成前置检查不可起飞；控制、降落和验证结果正确 | `flight-*.test.ts`、`px4-flight.test.ts` |
| 课堂可靠性 | 12 槽位、FIFO 排队、释放晋级、重启恢复、学生隔离 | `test_classroom_reliability_v1.py`、`px4-session.test.ts` |
| 训练复盘 | 能读取本次时间线、工作单、错误操作与成绩 | `learning-guide-v1.test.ts`、`training-bridge.test.ts` |
| 页面布局 | 顶部导航和学习指引不遮挡工作区，调试与复盘可完整滚动，小屏导航可访问 | `learning-shell-regression.test.ts`、`ui-bugfix-v2.test.ts`、构建检查 |
| UI 并发与数据归属 | 任务启动不可重复；快速筛选只保留最新结果；复盘工作单不得跨任务串用 | `ui-bugfix-v2.test.ts` |

## 覆盖部署后的 5 分钟人工验收

1. 学生从“我的实训”开始一项任务，依次打开装配、系统调试、飞行实验，确认 URL 中的 `run/scenario/assignment` 不丢失。
2. 在动力系统页确认飞机静止在地面；测试 M1 后只有对应桨叶转动；点击“全部停止”后立即停转。
3. 未上锁时完成一次动力测试；模拟已解锁状态后确认四个测试按钮和“全部停止”均不可用。
4. 将诊断工作单保持折叠，完成调试；提交诊断时确认五项证据链不完整会被拦截。
5. 在遥控系统页拖动左右摇杆，确认实时通道同步；松开后右杆和偏航回中、油门保持，点击“回中 / 油门最低”后油门归零。
6. 用超过 12 个学生任务申请 PX4，确认第 13 个显示排队位置；释放一个槽位后队首自动进入。

部署前还应执行 `pytest -q`、`npm test -- --run`、`npm run build`；目标浏览器环境执行 `npm run test:browser`。
