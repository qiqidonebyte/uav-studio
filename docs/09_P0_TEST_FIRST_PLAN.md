# UAV Studio P0 — Test-First Sprint

基线：3D Asset System V1.1 已接入。

目标：在修改 P0 业务实现之前，先建立 UI / Asset / Scene Contract。

---

## Phase T0 — 冻结 UI 视觉规范

完成：

- `docs/07_UI_VISUAL_ACCEPTANCE_SPEC_CN.md`

输出：

- 可量化布局；
- 组件卡契约；
- 3D构图要求；
- 相机要求；
- Telemetry单一数据源要求；
- Visual Test Probe 契约；
- Golden Screenshot 规则。

---

## Phase T1 — 建立 UI Contract 测试

新增：

- `frontend/tests/p0-ui-contract.mjs`

当前应同时包含 GREEN 与 RED：

GREEN 代表旧系统已经满足的基本布局。

RED 代表下一阶段必须实现的产品要求，例如：

- Component Card；
- 缩略图；
- 组件工程参数卡；
- 稳定 `data-testid`。

---

## Phase T2 — 建立 Three.js Scene Contract

新增：

- `frontend/src/types/visual-test.d.ts`
- `frontend/tests/p0-scene-contract.mjs`

当前版本没有暴露：

```text
window.__UAV_VISUAL_TEST__
```

因此这些测试应该 RED。

后续实现 Probe 时，只允许读取真实场景状态，不得伪造状态让测试通过。

---

## Phase T3 — Asset Contract

新增：

- `frontend/tests/p0-asset-contract.test.ts`

重点验证：

- Manifest引用的文件真实存在；
- GLB为合法 binary glTF v2；
- PNG缩略图真实存在；
- 450/650不是同一资产；
- 5010/4008不是同一资产；
- 10000/16000电池不是同一资产；
- CW/CCW不是同一资产；
- Registry和Manifest当前映射一致；
- 未知组件不能 silent fallback；
- Component 最终应拥有 visual metadata。

---

## P0后续实现顺序

在保存 RED Baseline 后，依次实现：

1. Component Visual 单一事实源；
2. Frame Mount Points；
3. Assembly Component Card；
4. 真实 CW/CCW 装配语义；
5. 故障组件库；
6. 工程检查 ↔ 3D联动；
7. 视觉人工验收；
8. Golden Screenshot；
9. CI。

不要同时修改全部模块。

---

## RED Baseline 规则

第一次运行后记录：

```text
总测试数：
PASS：
FAIL：
```

并保存失败名称。

RED 不是“当前项目失败”，而是：

> 尚未实现的 P0 产品契约已经被自动化表达。

只有实现完成后这些测试才应逐项转绿。
