# UAV Studio UI Layout Fix

这是上一轮科技风主题的修复补丁。

## 修复内容

1. 保留已经改善的 `DroneScene.vue` 飞行平滑动画，不覆盖它。
2. 恢复冻结的 V1 布局尺寸：
   - Header 56px
   - 260 / fluid / auto 顶栏布局
   - 276 / fluid / 320 工作台
   - 12px padding / gap
   - 原来的字号、按钮高度、图表高度
3. 恢复上一轮主题文件误删的：
   - `assembly-grid`
   - `flight-grid`
   - `replay-grid`
   - slot picker / stage title / inspector / replay 等布局规则
4. 科技主题只放在新的 `tech-theme-safe.css`，以后换颜色不会再动布局。
5. 增加 ComponentCard 图片保护：
   - `object-fit: contain`
   - `object-position: center`
   - 保证完整图片显示，不允许 cover 裁切。
6. Header 的浙江工贸标记缩小为 28×28，并把标题控制在原 260px 品牌栏内，避免挤压导航。

## 覆盖文件

- `frontend/src/App.vue`
- `frontend/src/main.ts`
- `frontend/src/styles/tech-theme-safe.css`
- `frontend/public/branding/zjitc-campus-mark.svg`

注意：这个补丁**不覆盖 `DroneScene.vue`**，所以你上一轮已经改善的飞行动画会保留。

## 推荐测试

```bash
cd frontend
npm run build
npm run test
```

启动前后端后，重点人工检查：

- 1600×1000：装配、飞行、历史页面
- 1366×768：Header 是否挤压
- 组件缩略图是否完整显示
- Flight 3D / Map / Split 是否完整
- 所有文字字号是否回到原设计尺度
