# UAV Studio Classroom Reliability V1

目标不是做分布式平台，而是保证一门 35 人无人机装调检修课能够稳定运行：不串飞机、不串成绩、刷新可恢复、PX4 资源可排队、异常后能继续。

## 1. 课堂资源模型

默认参数：

```bash
PX4_POOL_SIZE=12
PX4_IDLE_TIMEOUT=600
PX4_START_TIMEOUT=30
PX4_RECOVERY_RETRY=1
PX4_CLASSROOM_PORTS=14600,14601,14602,14603,14604,14605,14606,14607,14608,14609,14610,14611
```

35 名学生可以同时拥有 TrainingRun，但最多 12 个 Run 同时绑定 PX4 Slot，其余采用 FIFO 排队。轮询 `status/telemetry` 不会抢占 Slot；第一次 `connect` 才申请资源。

## 2. 为什么课堂池使用 14600-14611

保留现有单机 Bridge 的 `14540` 不动。课堂池单独使用 `14600-14611`，避免正式实训和原 `:8001` 演示 Bridge 抢同一个 UDP 端口。

PX4 默认多实例 offboard 远程端口只依次分配 `14540-14549`，第 11 个及以后默认会复用 `14549`。因此 12 Slot 不能依赖默认端口分配。生产部署应给每个 SIH 实例额外启动一条课堂专用 MAVLink UDP 连接，例如实例 N（N=0..11）使用：

```text
local UDP  = 15600 + N
remote UDP = 14600 + N
```

PX4 命令形式为：

```bash
mavlink start -u <15600+N> -o <14600+N> -t 127.0.0.1 -m onboard -r 4000000
```

这样 12 个实例各自向 UAV Studio 的 12 个独立监听端口发送 MAVLink，同时不影响 PX4 默认的 GCS/offboard 通道。PX4 官方模块文档明确支持用 `mavlink start -u <local> -o <remote> -t <partner>` 增加 UDP MAVLink 实例。

## 3. PX4 进程模式

资源管理器支持两种模式：

### A. 推荐：后台外部管理 12 个 SIH 实例

提前启动 12 个实例，并确保每个实例只向对应端口发送 offboard MAVLink。UAV Studio 只负责占用/释放 Bridge Slot。优点是部署可控，课堂前可以一次性检查全部实例。

### B. 可选：由 Backend 按需启动

配置：

```bash
PX4_DIR=/opt/PX4-Autopilot
PX4_SLOT_LAUNCH_TEMPLATE='你的启动命令，允许使用 {slot} {instance} {port}'
```

同时会提供环境变量 `PX4_SLOT`、`PX4_INSTANCE`、`PX4_OFFBOARD_PORT`。注意：你的启动命令/启动脚本必须真正为该实例建立指向 `{port}` 的课堂专用 MAVLink UDP 通道；仅执行 stock 多实例启动还不够。

## 4. 必须单 worker

Classroom Reliability V1 的 Slot Manager 是进程内状态，故生产后端先固定：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

35 人规模不需要 Redis/分布式锁/多 worker。未来若要多后端进程，再升级共享锁与 Session Manager。

## 5. SQLite 并发

补丁开启：

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;
```

并给 `TrainingRun` 增加 SQLAlchemy optimistic version；并发覆盖会返回 HTTP 409，而不是静默覆盖另一请求。

`TrainingEvent` 增加可选 `event_key`，并建立 `(run_id,event_key)` 唯一索引，浏览器重试不会重复记一条事件。

## 6. 异常恢复

- 浏览器刷新：TrainingRun 与 PX4Session 仍在数据库，重新进入继续。
- 网络短断：10 分钟内 Slot 保留；状态轮询恢复后继续。
- Backend 重启：所有运行中 Slot 释放，PX4Session 重新排队；TrainingRun/成绩不丢。
- PX4 子进程崩溃：如使用 Backend managed process，最多自动重启一次。
- 空闲超过 10 分钟：回收 Slot，TrainingRun 保持原阶段；学生再次连接时重新申请。
- TrainingRun 完成：自动释放 PX4 Slot，并立即把资源让给 FIFO 队首。

核心原则：**TrainingRun 是事实来源，PX4 Session 是可丢弃的临时计算资源。**

## 7. API 路由

自由演示（URL 没有 `run`）：继续使用旧 `:8001/api/px4`，不破坏现有单机演示。

正式实训（URL 带 `?run=123`）：前端自动切换到：

```text
/api/training/runs/123/px4/status
/api/training/runs/123/px4/telemetry
/api/training/runs/123/px4/connect
/api/training/runs/123/px4/arm
/api/training/runs/123/px4/takeoff
/api/training/runs/123/px4/land
...
```

所有命令先验证 `run.student_user_id == current_user.id`，从路由层阻止串台。

## 8. 应用补丁

将 ZIP 解压到任意目录，然后：

```bash
python apply_classroom_reliability_v1.py --repo /path/to/uav-studio --check
python apply_classroom_reliability_v1.py --repo /path/to/uav-studio
```

脚本会在仓库中创建 `.classroom_reliability_backup_v1/` 备份被修改的旧文件。

然后运行：

```bash
pytest -q
cd frontend
npm test
npm run build
```

## 9. 课堂前检查

启动 backend 和 PX4 实例后：

```bash
python scripts/check_px4_classroom_pool.py \
  --base-url http://127.0.0.1:8000 \
  --username admin \
  --password '你的管理员密码'
```

## 10. Golden Path

先只验证 1 教师 + 35 学生 + 12 Slot 的数据/排队闭环：

```bash
python scripts/classroom_golden_path.py \
  --base-url http://127.0.0.1:8000 \
  --admin-password '你的管理员密码'
```

在 12 个 SIH 都确认正常后，执行真实 PX4：

```bash
python scripts/classroom_golden_path.py \
  --base-url http://127.0.0.1:8000 \
  --admin-password '你的管理员密码' \
  --exercise-px4
```

真实模式会以最多 12 个并发批次执行 Arm → Takeoff → Hover → Land，并验证 35 个 Run 最终进入教师成绩册。
