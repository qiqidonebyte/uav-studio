# UAV Studio V1 — 第二轮验收 Prompt

不要增加任何新功能，不要大规模重构。

重新阅读 `docs/` 全部冻结规格，然后对当前项目进行真实验收与修复：

1. 运行全部 pytest；
2. 运行 frontend production build；
3. 启动后端和前端；
4. 验证真实组件装配与装配检查；
5. 验证 CG 与工程参数来自后端真实计算；
6. 验证解锁 → 起飞10m → 悬停；
7. 验证 5m/s 侧风导致位置、姿态、M1~M4 推力变化；
8. 验证 3D 视图和 Local Flight Map 使用同一 TelemetryFrame；
9. 验证降落；
10. 验证 telemetry JSON、History、Replay。

发现问题直接修复并重测。禁止增加 PX4/Gazebo/ROS2/AI。

最终输出 PASS/FAIL 表，禁止声称未实际验证的内容成功。
