# UAV-Studio 飞控与传感器调试 V1 — 直接覆盖包

本包基于 **System Debugging V2 + PX4 Bridge V1**，只补齐“飞控与传感器”模块，不修改遥控系统、安全设置和起飞前检查的业务实现。

## 直接覆盖

ZIP 根目录直接包含 `backend/`、`frontend/`、`tests/`、`docs/`、`requirements.txt`，没有额外包装目录。

在当前 UAV-Studio 项目根目录解压并允许覆盖同名文件即可。

## 新增能力

### 前端
- 飞控姿态仪：Roll / Pitch / Yaw / Heading
- IMU 三轴实时数据：加速度、角速度、温度、数据延迟
- GNSS/GPS：Fix、卫星数、EPH、经纬度、相对高度
- 磁罗盘：航向、三轴磁场、磁场强度
- 气压计：绝对气压、气压高度、温度、数据延迟
- EKF：Estimator flags、本地位置、Pre-Arm 状态和诊断提示
- 传感器健康状态：正常 / 异常 / 待数据
- 四类校准：陀螺仪、六面加速度计、磁罗盘、气压零点
- “执行传感器检查”：真实模式刷新数据并运行 PX4 Pre-Arm；模拟模式执行教学检查
- 罗盘异常教学场景可通过“罗盘校准”完成故障排除并恢复评分

### PX4 Bridge
新增 MAVLink 数据流：
- `HIGHRES_IMU`
- `SCALED_IMU`
- `SCALED_PRESSURE`
- `SYS_STATUS` 的 sensor present/enabled/health 位

新增接口：
- `POST /api/px4/sensors/gyro/calibrate`
- `POST /api/px4/sensors/accelerometer/calibrate`
- `POST /api/px4/sensors/compass/calibrate`
- `POST /api/px4/sensors/barometer/calibrate`

校准使用 MAVLink `MAV_CMD_PREFLIGHT_CALIBRATION (241)`。真实模式下界面仅报告“命令已受理”并提示继续观察 PX4 `STATUSTEXT`，不会将 ACK 误报为“校准完成”。

## 依赖

没有新增第三方依赖。继续使用 PX4 Bridge V1 已要求的：

```bash
python -m pip install -r requirements.txt
```

核心新增依赖仍只有 `pymavlink>=2.4.49,<3`。

## 快速验证

### 不启动 PX4
1. 打开“系统调试” → “飞控与传感器”。
2. 页面应显示“教学模拟数据”。
3. 选择左侧“罗盘异常”。
4. 罗盘卡和 EKF 应显示异常。
5. 点击“磁罗盘校准”。
6. 教学流程完成后罗盘/EKF 恢复，调试分数恢复。

### 连接 PX4 SIH
1. 启动 PX4 SIH 和 `scripts/run_px4_bridge.*`（沿用上一版）。
2. 调试页右侧显示 PX4 SIH 已连接。
3. 飞控与传感器页应开始显示 MAVLink 实时值。
4. 点击“执行传感器检查”会请求数据流并运行 Pre-Arm Check。
5. 未解锁状态下可发起各传感器校准；加速度计/罗盘的完整校准仍需遵循 PX4 状态提示。
