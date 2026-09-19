# 组件库 + 系统设置测试计划

## 后端 / API

- admin 自动初始化。
- 默认密码不是明文存储。
- PBKDF2 密码验证。
- 修改密码验证当前密码。
- 设置保存后再次读取保持一致。
- 默认设置补全。
- 组件分类 / 搜索。
- 组件视觉资产存在。
- 电机兼容关系由性能曲线推导。
- Clone 产生新组件 ID，复用 GLB 但拥有独立 asset key。
- 编辑组件保留 3D 资产。
- 非法工程参数拒绝保存。
- Settings / Component Library HTTP API CRUD。

## 前端 / E2E

- 顶栏存在组件库 / 系统设置入口。
- 组件库分类、搜索、详情、3D Preview、适配关系。
- 设置页 admin 信息。
- 3D 设置保存后刷新仍保留。
- 飞行安全状态机测试继续执行。
- Settings 不允许自动 arm / takeoff。

## 回归要求

新增功能不得改变：

- 装配 → 检查 → Flight Lab 主链。
- 开始 → 解锁 → 起飞 → 降落 状态机。
- `TelemetryFrame` 单一数据源。
- 3D 平滑插值。
- ComponentCard 图片 `contain` 完整显示。
