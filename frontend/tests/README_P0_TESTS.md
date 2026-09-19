# P0 Test-First Tests

这组测试故意包含 RED。

## 运行前

启动后端和前端，例如：

```bash
# terminal 1, repository root
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# terminal 2
cd frontend
npm run dev -- --host 127.0.0.1 --port 5174
```

然后：

```bash
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

## 当前应该通过的方向

Asset：

- 文件存在；
- GLB格式；
- PNG格式；
- 当前变体资产不同；
- Manifest和Registry当前映射一致。

UI：

- 三栏工作台；
- 56px Topbar；
- 中央 Canvas 尺寸；
- 无水平溢出。

## 当前应该失败的方向

Asset：

- 未知 Component 必须 fail loudly；
- `Component` 数据契约拥有 visual metadata。

UI：

- 组件卡替代 `<select>`；
- 卡片缩略图；
- 卡片 name/mass/spec。

Scene：

- `window.__UAV_VISUAL_TEST__` 尚未实现，因此 Scene Contract 应 RED。

## 重要

不要把这些失败测试改成 `skip`。  
下一阶段业务实现应该逐项使它们变绿。

## Browser

如果自动找不到浏览器，可以：

```powershell
$env:P0_BROWSER_PATH="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

或设置为本机 Chrome/Chromium。
