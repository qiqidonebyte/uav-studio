# UAV Studio — 组件库 + 系统设置实现包

本包按当前对话中的最新开发状态制作，直接解压到 `uav-studio` 项目根目录覆盖。

## 本轮新增

### 1. 组件库

新增一级模块：`组件库`

包含：

- 九类组件分类浏览；
- 名称 / ID 搜索；
- 完整缩略图卡片；
- 基本信息；
- 工程参数；
- 电机性能曲线；
- Three.js 单组件 3D 预览；
- 适配关系；
- 组件复制；
- 组件编辑；
- 备注与标签；
- 保存前工程参数验证。

组件库与装配页使用同一 `components` 表。复制或编辑组件以后，
Assembly Store 会刷新组件列表，不另外维护第二套组件数据。

### 2. 系统设置

新增一级模块：`系统设置`

包含：

- 账户与密码；
- 通用设置；
- 3D 显示；
- 飞行实验；
- 关于。

本地用户：

```text
username: admin
initial password: 123456
```

密码使用 PBKDF2-SHA256 哈希保存，不保存明文。

设置保存在 SQLite `users.settings_json`。

### 3. 设置实际生效

不是只做设置表单：

- 3D质量 → renderer pixel ratio；
- 阴影质量 → shadow 开关/尺寸；
- 环境反射 → scene.environment；
- 网格 / 坐标轴 → 显示开关；
- CG / 推力 / 重力 / 风 / 轨迹 → 3D显示开关；
- 轨迹点数 → DroneScene 历史轨迹长度；
- 默认相机 → DroneScene 初始化；
- 默认高度 / 风速 / 风向 → FlightLab 初始化；
- 默认 3D/Map/Split → FlightLab 初始化；
- 图表窗口 → RealtimeCharts 时间窗口；
- 自动连接遥测 → Simulation Store；
- 自动创建仿真 → FlightLab（默认关闭）。

安全状态机继续固定：

`开始 → 解锁 → 起飞 → 降落`

没有自动解锁、自动起飞设置。

## 新增 API

```text
GET  /api/user/me
PUT  /api/user/password

GET  /api/settings
PUT  /api/settings

GET  /api/library/components
GET  /api/library/components/{id}
POST /api/library/components/{id}/clone
PUT  /api/library/components/{id}
```

## 测试

本包制作时已实际运行：

```text
11 backend/service/API tests passed
19 UI source-contract checks passed
TypeScript core contracts: tsc PASS
2 new E2E scripts: node syntax PASS
```

详细见 `VERIFICATION_REPORT.md`。

完整浏览器 E2E 仍需在你的项目安装好 `node_modules`、启动前后端后运行：

```bash
cd frontend
npm run build
npm run test
npm run e2e:component-library
npm run e2e:settings
npm run e2e:flight-controls
npm run e2e:flight
```

## 覆盖注意

这份包包含当前版本的：

- `DroneScene.vue`（保留飞行平滑插值，并增加设置联动）
- `FlightLab.vue`（保留开始→解锁→起飞→降落状态机）
- `App.vue`（加入组件库、系统设置导航）
- `assembly.ts`（加入组件库刷新）

因此不要只挑页面文件覆盖，建议整个 ZIP 按目录覆盖。
