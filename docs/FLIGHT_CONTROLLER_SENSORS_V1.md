# Flight Controller & Sensors Workbench V1

## 设计目标

让 UAV-Studio 的“飞控与传感器”从占位页变成真正的调试工作台。页面同时支持两种数据源：

- **PX4 Live**：读取 PX4 SIH/SITL 的 MAVLink 数据并发送真实校准/检查命令。
- **Teaching Demo**：没有 PX4 时仍可练习读数、故障判断和校准流程，但界面明确标注为教学模拟。

## 数据契约

`GET /api/px4/telemetry` 新增：

- `imu.accel_m_s2`
- `imu.gyro_rad_s`
- `imu.temperature_c`
- `magnetometer.*`
- `barometer.*`
- `sensor_health.*`
- `sensor_data_age_s.*`

## 校准边界

`MAV_CMD_PREFLIGHT_CALIBRATION` 的 ACK 只表示 PX4 接受/处理命令。特别是加速度计和磁罗盘，完整校准包含多姿态操作，因此前端状态使用“已发起/等待 PX4 提示”，不会直接标记真实校准成功。

## 下一步

本模块完成后，再开发“安全设置”更顺：可以直接复用 PX4 参数读写和 Pre-Arm/STATUSTEXT 诊断能力。
