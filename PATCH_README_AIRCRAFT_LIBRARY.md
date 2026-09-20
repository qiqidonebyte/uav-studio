# UAV Studio v1.5.1 — Aircraft Library / Design Save

本包解决 UAV Studio 当前一个关键产品缺口：

> 用户的装配修改虽然会写入 SQLite，但此前始终围绕默认 Aircraft #1 工作，无法真正保存和管理多架独立飞机设计。

v1.5.1 把“飞机设计”升级成正式作品对象。

## 云端基线

```text
Repository: qiqidonebyte/uav-studio
Branch:     main
HEAD:       61a9a82e5c49f039d9b741438b721fd04c5230ab
Commit:     feat: fix propeller overlap and update realistic assets
```

GitHub `main` 目前还没有上一轮本地生成的 v1.5 Digital Assembly 覆盖包。

因此这个 ZIP 是 **累计覆盖包**：

```text
云端 61a9...
  +
v1.5 Digital Assembly Edition
  +
v1.5.1 Aircraft Library
```

即使你还没有单独覆盖上一版 v1.5，也可以直接使用本包。

---

## 这次新增的产品能力

### 我的飞机

新增：

```text
/aircraft
```

并成为默认入口。

设计卡不是后台 CRUD 表，而是作品库：

```text
真实 3D 缩略图
飞机名称
设计说明
工程检查状态
总质量
推重比
预计续航
最近修改时间
实验次数
```

支持：

```text
打开 / 继续设计
复制方案
重命名
修改说明
安全删除
```

### 新建设计

提供三个稳定模板：

```text
EduQuad-650 Reference
空白 Quad-X
EduQuad-450 Chassis
```

450 模板只预装机架，因为当前 14/15 英寸桨与 450 轴距存在真实旋翼盘干涉；不会伪装成一个“可飞参考方案”。

### 真正独立的飞机 ID

前端不再写死：

```text
DEFAULT_AIRCRAFT_ID = 1
```

当前飞机 ID 会被记住。

飞机 A 与飞机 B 拥有不同 SQLite `AircraftRecord.id`。

### 自动保存

装配页正常修改继续自动：

```text
PUT /api/aircraft/{activeAircraftId}
```

状态栏明确显示：

```text
正在保存…
已保存
保存失败
```

不需要用户频繁按 Ctrl+S。

### 另存为 / 复制方案

装配页增加：

```text
我的飞机
另存为副本
```

复制的是完整方案，包括：

- 组件选择；
- M1–M4 Physical Assembly Instances；
- 桨叶方向；
- GNSS / Payload 位置；
- 设计说明。

复制后的方案拥有新的数据库 ID。

### Flight Lab 跟随当前飞机

飞行实验不再强制使用 Aircraft #1。

现在：

```text
My Aircraft
→ 打开某架飞机
→ Assembly
→ Flight Lab
```

Flight Lab 使用这架当前设计的 `activeAircraftId`。

### 实验可追溯性

如果一架飞机已经产生实验记录：

```text
DELETE /api/aircraft/{id}
```

会被阻止。

原因是实验记录已经引用该 Aircraft ID / Name，不能为了删除一个设计破坏历史可追溯性。

另外，系统永远至少保留一架飞机设计。

---

## 真实 3D 设计缩略图

飞机卡片不是使用通用占位图片。

它复用：

```text
AircraftRenderer
Component.visual
assembly_instances
GLB Asset Cache
```

生成当前设计真实的 3D 缩略图。

为了避免“每张卡一个 WebGL context”导致浏览器资源耗尽，这一版使用：

```text
一个共享 WebGLRenderer
        ↓
顺序生成缩略图
        ↓
缓存 Data URL
        ↓
普通 <img> 卡片
```

所以即使后续积累很多飞机设计，也不会因为卡片数量快速触碰 WebGL Context 限制。

---

## 后端 API

新增：

```text
GET    /api/aircraft
GET    /api/aircraft/templates
POST   /api/aircraft/from-template/{template_key}
POST   /api/aircraft/{id}/duplicate
PATCH  /api/aircraft/{id}/metadata
DELETE /api/aircraft/{id}
```

保留：

```text
GET /api/aircraft/{id}
PUT /api/aircraft/{id}
POST /api/aircraft/{id}/calculate
```

---

## SQLite Migration

`aircraft` 新增：

```text
description
created_at
updated_at
assembly_instances_json   # 来自累计 v1.5
```

全部为 additive migration。

不用删库。

老飞机第一次启动时自动补：

```text
description = ""
created_at
updated_at
```

---

## 覆盖方式

建议先提交当前本地代码：

```bash
git add .
git commit -m "checkpoint before aircraft library"
```

然后把 ZIP 内容直接解压到 `uav-studio` 项目根目录覆盖。

---

## 覆盖后建议执行

Backend：

```bash
pytest -q
```

Frontend：

```bash
cd frontend
npm run build
npm run test

npm run test:p0:scene
npm run e2e:digital-assembly
npm run e2e:aircraft-library
```

Aircraft Library E2E 会自动：

```text
新建设计
→ 保存
→ 页面切换后重新读取
→ 复制
→ 重命名
→ 删除副本
→ 删除测试原件
→ 恢复测试前设计数量
```

---

## 设计文档

```text
docs/18_DIGITAL_ASSEMBLY_2_0_CN.md
docs/19_DIGITAL_ASSEMBLY_TEST_PLAN.md
docs/20_AIRCRAFT_LIBRARY_SPEC_CN.md
docs/21_AIRCRAFT_LIBRARY_TEST_PLAN.md
```

---

## 下一阶段接口已经准备好

有了 Aircraft Library 后，下一阶段的：

```text
方案 A / B 对比
Engineering Diagnosis
Sensitivity Analysis
Design Explorer
```

才有真正的数据对象可以依附。

例如：

```text
长航时方案 A
        ↓ duplicate
长航时方案 B
        ↓
Compare
```

这就是这次“保存飞机”功能真正重要的地方。
