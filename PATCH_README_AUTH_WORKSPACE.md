# UAV Studio v1.5.2 — Accounts & Workspace

本覆盖包基于当前 GitHub `main`：

```text
Repository: qiqidonebyte/uav-studio
HEAD:       cdd316c938242905cbd4a363eb6fe1d2ac14af29
Commit:     style: rename aircraft entry to my aircraft
```

这是**增量覆盖包**，已经以你修复后的当前 GitHub 为基线，不再覆盖回旧版 App / delete 行为。

## 这次解决的问题

旧版本虽然有 `admin / 123456` 和密码哈希，但没有真正登录鉴权。

实际是：

```text
所有浏览器
   ↓
同一个 admin
   ↓
同一批飞机 / 设置 / 实验
```

v1.5.2 改为：

```text
用户账号
  ↓
自己的飞机（最多 10 架）
  ↓
自己的装配 / 工程设计
  ↓
自己的飞行实验
  ↓
自己的设置
```

## 新增功能

### 登录 / 注册 / 退出

新增：

```text
/login
/register
```

API：

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

登录使用服务端 Session + HttpOnly Cookie。

数据库只保存随机 session token 的 SHA-256，不保存原始 token。

### 每个用户最多 10 架飞机

后端常量：

```text
AIRCRAFT_LIMIT_PER_USER = 10
```

以下所有创建入口都由后端强制限制：

```text
新建设计
从模板创建
复制方案
另存为副本
POST /api/aircraft
```

达到 10 架以后返回 HTTP 409。

前端同时：

```text
显示 8 / 10
10 / 10 后禁用新建设计
禁用复制方案
禁用另存为副本
账户设置显示当前配额
```

前端限制只是 UX；真正的约束在后端。

### 用户飞机完全隔离

`AircraftRecord` 新增：

```text
owner_user_id
```

所有飞机 CRUD 都检查当前用户。

用户 B 即使猜到用户 A 的 Aircraft ID：

```text
GET
PATCH
DELETE
Duplicate
Flight Simulation
```

也拿不到 A 的飞机，统一按不存在处理。

### 老数据不丢

升级已有 SQLite 后：

```text
原 admin
    ↓ 保留

原来没有 owner 的所有 Aircraft
    ↓
自动归属 admin
```

所以你现在 GitHub 里的飞机不会因为加入登录系统而消失。

### 个人设置

以前 `/api/settings` 永远操作 admin。

现在设置跟当前登录用户绑定。

每个账号独立保存：

```text
通用设置
3D 设置
飞行设置
密码
```

### 实验记录隔离

History / Replay 会通过飞机所有权过滤。

学生只能看到自己的飞机产生的实验。

### 飞行仿真并发隔离

退出账号时，前端也会清空旧账号的 simulation ID、遥测历史和飞行状态，避免同一浏览器切换账号后看到前一个用户的飞行状态。

原 `SimulationManager` 只有一个全局 `_session`。

多用户之后那会出现：

```text
学生 A 启动仿真
学生 B 启动仿真
→ A 的 session 被 B 替换
```

本版改为：

```text
simulation_id → SimulationSession
```

并且每条飞行控制 API、WebSocket 都检查该仿真对应的飞机是否属于当前用户。

## Session 安全属性

Cookie：

```text
HttpOnly
SameSite=Lax
Path=/
7 天有效期
```

HTTPS 部署可以设置：

```bash
UAV_SESSION_SECURE_COOKIE=1
```

### admin 密码

已有数据库：

```text
保持现有 admin 密码不变
```

新数据库首次启动可以设置：

```bash
UAV_ADMIN_PASSWORD=你的管理员密码
```

如果没有设置，为兼容现有项目仍会使用历史默认 `123456`。

实际部署后建议立即修改管理员密码。

## 当前边界

这版专门完成：

```text
账号
登录注册
Session
用户飞机隔离
10 架飞机限制
个人设置
实验隔离
飞行 session 隔离
```

暂时没有继续扩展：

```text
教师创建学生账号
班级 / 邀请码
找回密码
SSO
用户私有组件库
组件库角色权限
```

**当前 Component Library 仍是登录后的共享系统资源。**

## 覆盖方式

先保存你本地当前修改，然后将 ZIP 解压到仓库根目录覆盖。

数据库不需要删除。

第一次启动时会执行 additive migration。

## 建议运行

Backend：

```bash
pytest -q
```

Frontend：

```bash
cd frontend
npm install
npm run build
npm run test
npm run e2e:auth
npm run e2e:aircraft-library
npm run e2e:digital-assembly
```

## 新增测试

```text
tests/test_auth_workspace.py
tests/test_auth_migration.py

tools/verify_auth_workspace.py
tools/verify_auth_runtime.py

frontend/tests/e2e-auth.mjs
```

完整设计与测试说明：

```text
docs/22_AUTH_WORKSPACE_SPEC_CN.md
docs/23_AUTH_WORKSPACE_TEST_PLAN.md
```
