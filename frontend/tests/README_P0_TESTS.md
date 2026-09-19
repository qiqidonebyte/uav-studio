# P0 Test-First Tests — Sprint 1

本组测试用于验证第一轮高优先级 P0 实现。

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
npm run test
npm run build
npm run test:p0:asset
npm run test:p0:ui
npm run test:p0:scene
```

## Sprint 1 应转为 GREEN 的契约

- Component 拥有 `visual` 数据契约；
- 3D 资产路径不再依赖前端 numeric-id registry；
- 未知已安装组件不允许 silent fallback；
- Assembly 使用 Component Card，不再以 `<select>` 为主要选件界面；
- Component Card 有缩略图 / 名称 / 质量 / 工程参数；
- `window.__UAV_VISUAL_TEST__` 可以读取真实场景状态；
- 450/650、10000/16000 更换后 3D 资产和 bounds 变化；
- 开发模式 Three.js pixelRatio 固定为 1，保证视觉测试稳定。

## 下一轮仍未解决

Sprint 1 **没有**完成：

- Frame mount_points 同时驱动 Engineering / Simulator / Renderer；
- M1~M4 独立螺旋桨安装语义；
- 故障组件库；
- 装配错误点击后自动高亮具体部件；
- Golden Screenshot 批准与 CI。

这些项目应该进入下一轮 RED Contract，而不是在本轮偷偷补成硬编码。
