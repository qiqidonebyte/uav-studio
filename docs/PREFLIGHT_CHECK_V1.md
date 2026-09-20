# 起飞前检查 V1

系统调试最终门禁，汇总六类状态：

1. 数字装配 / 工程校核
2. 飞控与传感器检查
3. 遥控系统检查
4. 动力系统 M1-M4 单电机验证
5. 安全 / Failsafe 设置
6. PX4 Pre-Arm

全部通过后生成本机飞行许可。许可与 aircraft id + aircraft JSON fingerprint 绑定，有效期 1 小时。FlightLab 会再次检查许可，未通过时锁定开始、解锁、起飞等飞行控制。
