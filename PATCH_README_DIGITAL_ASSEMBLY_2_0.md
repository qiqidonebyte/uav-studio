# UAV Studio v1.5 — Digital Assembly Edition

基线：

- Repository: `qiqidonebyte/uav-studio`
- Branch: `main`
- HEAD: `61a9a82e5c49f039d9b741438b721fd04c5230ab`
- Commit: `feat: fix propeller overlap and update realistic assets`

本覆盖包把当前装配页从“组件配置 + 3D 展示”升级为 **受约束的无人机数字装配工作台**。

## 这次的核心变化

### 1. 18 个 Semantic Mount Anchors

参考 Quad-X 现在拥有明确的物理安装点：

```text
frame:main

motor:M1  motor:M2  motor:M3  motor:M4
esc:M1    esc:M2    esc:M3    esc:M4
propeller:M1 ... propeller:M4

battery:main
power_module:main
flight_controller:main
gnss:main
payload:main
```

M1-M4 不再只是视觉复制，而是独立的物理装配实例。

### 2. 真正的 3D 装配模式

组件卡保留“快速配置”，同时增加“3D装配”。

3D 装配流程：

```text
选组件
→ 合法 Mount Anchor 发光
→ 真实候选 GLB 作为半透明 Ghost
→ Hover 确认 Snap
→ 点击安装
→ 沿安装轴动画进入
→ 独立 Mount 状态持久化
```

不是自由 CAD 拖拽，而是无人机专用的约束式装配。

### 3. 独立安装 / 拆卸

可以单独选中：

```text
motor:M1
motor:M2
motor:M3
motor:M4
```

右侧 Inspector 显示精确 Mount ID 与 XYZ。

“拆卸此安装位”先播放拆卸动画，再持久化数据库。
如果持久化失败，视觉状态会自动回滚。

### 4. 一套坐标同时驱动装配与爆炸视图

```text
final transform
= assembly datum
+ explosion transform
+ installation transform
```

避免安装动画、爆炸视图、正常整机各维护一套 magic number。

### 5. 空间工程检查

V1.5 加入基础 Spatial Engineering：

- Rotor Disc Collision；
- 电池 GLB Envelope vs 教学 Battery Bay；
- 旋翼干涉时 3D 红色半透明旋翼盘；
- 电池检查时显示安装包络。

已有后端 `PROPELLER_FRAME_OVERLAP` 仍保留并通过回归测试。

### 6. 后端正式保存物理装配状态

SQLite 新增：

```text
aircraft.assembly_instances_json
```

这是 additive migration，不删除旧数据。

旧数据库第一次启动时 NULL 状态自动解释为原来的“已完整装配”状态，保证兼容。

### 7. 飞行门禁升级

只选择了组件但没有完成必需 Mount 安装，会产生：

```text
ASSEMBLY_MOUNT_INCOMPLETE
```

物理实例与组件选择不一致：

```text
ASSEMBLY_INSTANCE_MISMATCH
```

因此未完成的数字装配不能直接进入飞行实验。

## 覆盖方式

建议先提交或备份你的本地修改，然后把本 ZIP **解压到项目根目录覆盖**。

本包基于上面的精确 GitHub HEAD 制作。

## 新增/修改测试

新增：

```text
tests/test_digital_assembly_instances.py
tests/test_digital_assembly_migration.py

frontend/tests/assembly-semantics.test.ts
frontend/tests/assembly-transforms.test.ts
frontend/tests/digital-assembly-workflow.test.ts
frontend/tests/e2e-digital-assembly.mjs
```

并扩展：

```text
frontend/tests/p0-scene-contract.mjs
```

## 在你的完整开发环境运行

```bash
pytest -q

cd frontend
npm install
npm run build
npm run test

npm run test:p0:asset
npm run test:p0:scene

npm run e2e:digital-assembly
npm run e2e
npm run e2e:flight
npm run e2e:flight-controls
```

完整设计说明：

- `docs/18_DIGITAL_ASSEMBLY_2_0_CN.md`
- `docs/19_DIGITAL_ASSEMBLY_TEST_PLAN.md`
