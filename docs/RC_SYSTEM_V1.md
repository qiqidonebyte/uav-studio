# 遥控系统调试模块 V1

## 教学闭环

观察输入 → 判断通道 → 配置映射 → 采集端点/中位 → 检查方向 → 应用参数 → 验证 RC Loss 策略。

## 数据源

真实模式：PX4 MAVLink `RC_CHANNELS` / `MANUAL_CONTROL`。

教学模式：浏览器本地虚拟 CH1–CH18 数据。虚拟输入不会下发到 PX4，不具备真机遥控能力。

## 参数

- RC_MAP_ROLL
- RC_MAP_PITCH
- RC_MAP_THROTTLE
- RC_MAP_YAW
- RC1..18_MIN
- RC1..18_TRIM
- RC1..18_MAX
- RC1..18_REV

每通道“教学死区”只用于网页归一化，不写入当前 PX4 main。
