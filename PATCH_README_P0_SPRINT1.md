# UAV Studio P0 Sprint 1 — 直接覆盖包

适配仓库：`qiqidonebyte/uav-studio`

制作基线：

`efa94f78f830be0e3e4bce79e6b72ae5f140cf23`

这是上一轮 Test-First 的第一批高优先级实现包。

## 直接使用

把 ZIP 解压到 `uav-studio` 项目根目录，允许覆盖同名文件。

本包不会删除你现有的 GLB / PNG 资产，直接使用已经提交到仓库的：

`frontend/public/models/uav/v1_1/`

## 本轮实现

1. Component 新增 `visual` API 数据契约；
2. `asset_manifest.json` 成为资产文件名源头，前端不再按 numeric id 硬映射正式组件；
3. 未知/缺失视觉资产 fail loudly，不再偷偷显示另一种默认组件；
4. Assembly `<select>` 改为可视化 Component Card；
5. Component Card 显示真实缩略图、质量、核心参数和安装状态；
6. Three.js 增加 `window.__UAV_VISUAL_TEST__` 自动验收 Probe；
7. 450/650、10000/16000 等视觉变体可以自动检查 bounds 与加载资产；
8. 旧 Replay 自动补视觉元数据，历史工程参数不变；
9. 包含上一轮 P0 Asset / UI / Scene tests 与视觉验收文档。

## 覆盖后先做什么

项目根目录：

```bash
pytest
```

前端：

```bash
cd frontend
npm install
npm run test
npm run build
```

启动后端和前端，再运行：

```bash
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

如果你的前端不是 5174：

PowerShell：

```powershell
$env:E2E_BASE_URL="http://127.0.0.1:5173"
npm run test:p0:ui
npm run test:p0:scene
```

## 本轮故意没有继续做

- Engineering / Simulator / Renderer 统一 Frame mount_points；
- M1~M4 独立 CW/CCW 桨安装；
- 故障组件库；
- 点击装配错误自动高亮具体3D部件；
- Golden Screenshot；
- GitHub Actions CI。

这些应该在 Sprint 1 验收后再写下一批 RED tests。

## 推荐提交

```bash
git add .
git commit -m "feat: implement P0 visual contract and component cards"
git push
```

push 后再让 ChatGPT review 最新 GitHub 版本。
