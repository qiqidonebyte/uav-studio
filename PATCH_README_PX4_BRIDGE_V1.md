# UAV-Studio PX4 Bridge V1 覆盖包

本覆盖包基于 **UAV-Studio 调试工作台 V2**，新增真实 PX4 SITL/SIH 通信桥。

## 覆盖方式

ZIP 根目录就是项目根目录内容，**没有额外套一层目录**。

在你的 `uav-studio/` 项目根目录直接解压并允许覆盖即可。

## 新增能力

- `backend/px4/bridge.py`
  - UDP 14540 MAVLink 连接
  - Heartbeat / 飞行模式 / Arm 状态
  - ATTITUDE / LOCAL_POSITION_NED / GPS / 电池
  - ACTUATOR_OUTPUT_STATUS（若 PX4 输出该消息）
  - Arm / Disarm
  - Takeoff / Land
  - PX4 Pre-Arm command
  - M1-M4 `MAV_CMD_ACTUATOR_TEST`
  - PX4 参数读取 / 写入
- `backend/px4_service.py`
  - 独立 FastAPI Bridge，默认端口 8001
- `frontend/src/api/px4.ts`
  - 浏览器 PX4 Bridge API 客户端
- V2 `Debugging.vue`
  - 自动探测 Bridge
  - 真实 PX4 模式 / 教学模拟模式自动切换
  - PX4 SIH 的位置姿态驱动现有 Three.js 飞机
  - M1-M4 单电机测试切换为真实 PX4 command
  - Arm / Disarm / 起飞 2m / 降落 / Pre-Arm
  - 参数读取与修改

## 依赖

新增：

```bash
pymavlink>=2.4.49,<3
```

安装：

```bash
python -m pip install -r requirements.txt
```

V1 故意不同时使用 MAVSDK + pymavlink，因为两套程序默认都会监听 PX4 的 14540，第一版会产生端口竞争。后续如需 MAVSDK，再增加 mavlink-router 做消息分流。

## 启动顺序

### 1. 启动 PX4 SIH

在 Ubuntu / WSL 的 PX4-Autopilot 仓库中：

```bash
make px4_sitl_sih sihsim_quadx
```

或者：

```bash
PX4_DIR=/path/to/PX4-Autopilot ./scripts/start_px4_sih.sh
```

PX4 SIH 单机默认会把 MAVSDK/offboard MAVLink 流发送到 UDP 14540。

### 2. 启动 UAV-Studio 原后端

保持你原来的启动方式不变。

### 3. 启动 PX4 Bridge

Linux / WSL：

```bash
./scripts/run_px4_bridge.sh
```

Windows（仅 Bridge，本机能收到 PX4 UDP 时）：

```bat
scripts\run_px4_bridge.bat
```

默认：

- Bridge HTTP：`0.0.0.0:8001`
- MAVLink：`udpin:0.0.0.0:14540`

可覆盖：

```bash
PX4_CONNECTION=udpin:0.0.0.0:14540 PX4_BRIDGE_PORT=8001 ./scripts/run_px4_bridge.sh
```

### 4. 启动前端

保持原方式：

```bash
cd frontend
npm install
npm run dev
```

进入 **系统调试**。

## 最小验收

1. 右侧显示 `PX4 SIH 已连接`。
2. 能看到 PX4 模式、GPS、姿态、高度、电池。
3. 点击 M1-M4 测试可发送真实 `MAV_CMD_ACTUATOR_TEST`。
4. 点击解锁 / 上锁得到 PX4 ACK。
5. 点击起飞 2m 后，PX4 SIH 的 `LOCAL_POSITION_NED` 被转换为 UAV-Studio Z 向上坐标，Three.js 飞机同步升高。
6. 点击降落后 Three.js 跟随 SIH 回落。
7. 可读取/写入一个 PX4 参数，例如 `RTL_RETURN_ALT`。

## 安全边界

V1 的执行机构测试是为 **PX4 SITL/SIH** 开发和验证的。后续连接真实飞控前，应增加显式的硬件安全锁、螺旋桨拆除确认、权限控制和真机模式提示；不要直接把当前 SITL 教学按钮用于带桨真机。
