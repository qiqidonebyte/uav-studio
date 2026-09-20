# 起飞前检查 V1 验证报告

## 已验证

- Debugging.vue / FlightLab.vue TypeScript 脚本通过 TypeScript `transpileModule` 语法诊断（0 error）
- backend PX4 Bridge Python 文件 `py_compile` 通过
- preflight.ts 可独立编译为 JavaScript
- 六项全部通过时评分为 100
- 阻断项会降低评分并阻止生成飞行许可
- 飞行许可能够保存/读取
- aircraft fingerprint 改变后，旧许可失效
- 超过 1 小时后，旧许可失效
- FlightLab 已二次接入 preflight gate；无许可时 flightControlAvailability 收到 `assemblyReady=false`
- ZIP 根目录直接为 backend / frontend / docs / tests 等，没有额外包装目录

## 未声称完成

当前执行环境没有项目完整 `frontend/node_modules`，因此没有实际运行完整 `npm run build` / Vitest 套件；已做 TypeScript 语法级检查和独立工具逻辑测试。当前环境也没有正在运行的 PX4 SIH，因此未声称完成真实 Heartbeat + Pre-Arm + FlightLab 的整链路运行测试。
