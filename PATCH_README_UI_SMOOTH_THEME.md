# UAV Studio UI Smooth + Theme Patch

本包完成两类优化：

1. **飞行三维视图顺滑化**
   - 位置、姿态、重心、风场、推力读数改为平滑插值
   - 跟随相机改为时间相关平滑跟踪
   - 显著减少飞行测试时“抖动、抽动、跟不上”的视觉问题

2. **头部品牌与科技配色**
   - Header 左侧加入“浙江工贸”校园标记
   - 保持 56px 顶栏高度，不破坏现有布局测试
   - 顶栏改为深色科技风，主体使用蓝 + 青强调色
   - 面板、按钮、分屏控件统一为更现代的硅谷风格 UI 语言

## 覆盖文件

- `frontend/src/App.vue`
- `frontend/src/components/DroneScene.vue`
- `frontend/src/styles/workbench.css`
- `frontend/public/branding/zjitc-campus-mark.svg`

## 说明

- 校园标记采用“浙江工贸 / ZJITC”风格化 SVG，用于系统品牌头部展示。
- 3D顺滑优化不改变后端遥测协议，只改善前端显示层，因此对既有接口兼容。
- 如果你后续拿到了学校官方矢量 Logo，只需要替换：

`frontend/public/branding/zjitc-campus-mark.svg`

其余页面结构无需修改。
