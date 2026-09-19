# UAV Studio — Component Image + Flight Command Regression Fix

本补丁只修复两个回归，不重做整体 UI，不覆盖 `DroneScene.vue`，因此保留上一轮飞行平滑优化。

## 1. 机架组件图片显示不全

`ComponentCard.vue` 改为显式 containment：

- 图片容器高度从 92px 调整为 136px；
- 容器增加 8px 安全边距；
- 图片使用 `width:auto / height:auto`；
- `max-width/max-height:100%`；
- `object-fit: contain`；
- 禁止 transform 导致裁切；
- 增加 `data-testid=component-media/component-thumbnail`。

这意味着图片无论长宽比如何，都必须完整落在 media viewport 中。

## 2. Flight Lab 按钮状态机恢复

新增：

`frontend/src/utils/flightControlGuards.ts`

飞行按钮不再散落写多个布尔表达式，而是由一个状态机统一计算。

正常流程：

```text
装配通过
  ↓
开始
  ↓
解锁
  ↓
起飞
  ↓
降落
```

状态要求：

- 初始：只有“开始”可用；解锁/起飞/降落灰色。
- 开始后：解锁可用；起飞仍灰色。
- 解锁后：起飞可用；解锁灰色；降落仍灰色。
- 起飞中/悬停：起飞灰色；降落可用。
- 暂停：飞行命令全部锁定，“开始”用于继续。
- 装配未通过：开始也不可用。

Flight Lab 内新增显式 disabled 样式，避免科技主题把 disabled 按钮看起来画成“仍可点击”。

## 3. 新增测试

- `frontend/tests/flight-control-guards.test.ts`
- `frontend/tests/e2e-flight-controls.mjs`
- `frontend/tests/e2e-component-card-image.mjs`

新增 npm 命令：

```bash
npm run e2e:flight-controls
npm run e2e:component-card
```

## 4. 本地验证建议

```bash
cd frontend
npm run test
npm run build
```

启动前后端后：

```bash
npm run e2e:flight-controls
npm run e2e:component-card
npm run e2e:flight
```

## 5. 本补丁不会覆盖

- `DroneScene.vue`
- Three.js 平滑动画
- Header 品牌样式
- 后端工程计算
- TelemetryFrame
