# UAV Studio P0 Test-First 覆盖包

适配仓库：`qiqidonebyte/uav-studio`

制作基线提交：

`efa94f78f830be0e3e4bce79e6b72ae5f140cf23`

本包的目的不是实现 P0，而是先把 P0 的 UI / 3D / Asset 验收标准固化成文档和自动测试。

## 本包会修改

- `.gitignore`
- `README.md`
- `frontend/package.json`

## 本包会新增

- `docs/07_UI_VISUAL_ACCEPTANCE_SPEC_CN.md`
- `docs/09_P0_TEST_FIRST_PLAN.md`
- `docs/reports/P0_RED_BASELINE_TEMPLATE.md`
- `frontend/src/types/visual-test.d.ts`
- `frontend/tests/p0-helpers.mjs`
- `frontend/tests/p0-asset-contract.test.ts`
- `frontend/tests/p0-ui-contract.mjs`
- `frontend/tests/p0-scene-contract.mjs`
- `frontend/tests/p0-visual-capture.mjs`
- `frontend/tests/README_P0_TESTS.md`

## 本包明确不做

- 不修改 `Assembly.vue`
- 不修改 `DroneScene.vue`
- 不修改 `AircraftRenderer.ts`
- 不修改后端工程计算
- 不修改 SimpleSimulator
- 不修改 TelemetryFrame
- 不实现 Component visual 字段
- 不实现 mount_points
- 不实现组件卡片
- 不实现真正的 M1~M4 独立桨安装

因此，覆盖后出现一批 **预期 RED** 是正确结果。

## 运行顺序

先运行现有回归：

```bash
cd frontend
npm run test
npm run build
```

然后运行新契约测试：

```bash
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

UI/Scene 测试默认要求前端与后端已经启动，并使用：

```text
E2E_BASE_URL=http://127.0.0.1:5174
```

如你的端口不同：

Windows PowerShell：

```powershell
$env:E2E_BASE_URL="http://127.0.0.1:5173"
npm run test:p0:ui
```

macOS/Linux：

```bash
E2E_BASE_URL=http://127.0.0.1:5173 npm run test:p0:ui
```

可选：生成当前界面候选截图供人工对比：

```bash
npm run test:p0:capture
```

截图写入 `frontend/test-results/p0-visual-candidates/`，该目录已加入 `.gitignore`。

## RED 的意义

当前版本预期：

- 一部分 Asset 文件完整性测试为 GREEN；
- Component visual 单一数据源测试为 RED；
- 未知组件 silent fallback 测试为 RED；
- 组件卡 UI 测试为 RED；
- `window.__UAV_VISUAL_TEST__` 场景探针测试为 RED。

不要为了“0 failed”先去删这些测试。它们就是接下来 P0 的开发任务。
