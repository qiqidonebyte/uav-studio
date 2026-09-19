# P0 RED Baseline Report

基线提交：

```text
efa94f78f830be0e3e4bce79e6b72ae5f140cf23
```

执行日期：

```text
YYYY-MM-DD
```

环境：

```text
OS:
Browser:
Viewport: 1600x1000
Node:
Python:
```

## 1. 原有回归

```text
npm run test:
npm run build:
pytest:
```

要求：原有功能应保持 GREEN。若原有回归失败，先处理回归问题，不进入 P0。

## 2. P0 Asset Contract

命令：

```bash
npm run test:p0:asset
```

结果：

```text
PASS:
FAIL:
```

预期 RED：

- unknown component must fail loudly
- Component owns visual metadata

## 3. P0 UI Contract

命令：

```bash
npm run test:p0:ui
```

结果：

```text
PASS:
FAIL:
```

预期 RED：

- Component Card exists
- Component Card has thumbnail
- Component Card has name/mass/spec
- `<select>` is no longer primary selector

## 4. P0 Scene Contract

命令：

```bash
npm run test:p0:scene
```

结果：

```text
PASS:
FAIL:
```

预期 RED：

- `window.__UAV_VISUAL_TEST__` exists
- sceneReady
- loadedAssets
- aircraftBounds
- partBounds
- mounts
- cameraMode
- pixelRatio=1

## 5. 当前截图候选

命令：

```bash
npm run test:p0:capture
```

输出：

`frontend/test-results/p0-visual-candidates/`

这些截图仅供人工 review，**不是 Golden Screenshot**。

## 6. 禁止操作

不要：

- 删除失败测试；
- 改成 skip；
- 直接批准当前截图；
- 在测试中写假 Probe；
- 降低验收范围只为变绿。
