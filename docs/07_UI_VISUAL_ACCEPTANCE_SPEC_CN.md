# UAV Studio V1 UI / 3D 视觉验收规范

状态：**P0 冻结规范**

本文件用于把“更像工程软件”“模型更真实”“UI效果更好”转换成可以验证的产品标准。  
本文件优先级高于临时效果图。效果图只能作为参考，不能替代本规范。

---

## 1. 测试环境

视觉验收使用固定环境：

- 浏览器：Chromium / Edge Chromium
- 视口：`1600 × 1000`
- locale：`zh-CN`
- 页面主题：Light
- 页面缩放：100%
- Three.js 测试模式 `pixelRatio = 1`
- 后端：固定 seed 数据
- 不允许随机组件、随机姿态、随机背景
- 截图前关闭 CSS 动画或等待动画稳定

1280px 宽度用于补充响应式验收，但 Golden Screenshot 统一使用 1600×1000。

---

## 2. 无人机装配页布局

在 1600×1000 下必须同时看到：

1. 左侧装配流程；
2. 中央 3D 工程工作区；
3. 右侧部件/工程检查器；
4. 底部装配进度/提示区。

要求：

- Topbar 高度：`56 ± 1 px`
- 左侧栏宽度：`240 ~ 300 px`
- 右侧栏宽度：`280 ~ 360 px`
- 中央工作区宽度 ≥ 工作台可用宽度的 `45%`
- 主页面不得出现水平滚动条
- `body` 不得因为主工作台产生额外纵向滚动
- 右侧 Inspector 不得出现水平滚动
- 面板间距保持统一，当前设计基准为 `12 px`

---

## 3. 组件选择必须是“数字装配”，不是纯表单

P0 完成后，`<select>` 不得作为组件选择的主要交互。

每个候选组件必须以 Component Card 呈现，至少包含：

- 组件缩略图；
- 中文名称；
- 质量；
- 至少 2 项该类别的核心工程参数；
- 当前是否已安装；
- 安装 / 更换操作。

建议稳定测试标识：

```text
data-testid="component-card"
data-component-id="10"
data-component-type="motor"
data-testid="component-name"
data-testid="component-mass"
data-testid="component-primary-spec"
data-testid="component-install"
```

同一类别有多个候选时，必须能在同一界面比较。

---

## 4. 3D飞机构图

完整 EduQuad-650 默认等距视角：

- 整机必须完整进入 Canvas；
- 不允许裁掉电机、桨叶、起落架或载荷；
- 飞机 2D 投影包围盒宽度应占 Canvas 宽度约 `45% ~ 75%`；
- 默认相机不能把飞机缩成很小的图标；
- 不能因为更换 450 / 650 机架导致模型跑出画面；
- 模型必须自动重新居中/适配。

3D工作区必须可见：

- Frame；
- M1~M4 电机；
- CW/CCW 螺旋桨；
- ESC；
- Battery；
- Power Module；
- Flight Controller；
- GNSS（安装时）；
- Payload（安装时）。

---

## 5. 配置变化必须同时产生“视觉变化 + 工程变化”

### 5.1 650 → 450 Frame

必须：

- 加载不同 GLB；
- 整机视觉尺寸发生明显变化；
- 3D重新构图；
- 后端总质量重新计算；
- 后端惯量重新计算。

### 5.2 Motor 5010 → 4008

必须：

- 加载不同 GLB；
- 电机外形/尺寸可区分；
- 工程性能曲线重新选择；
- 推重比/悬停油门等相关结果重新计算。

### 5.3 Battery 10000 → 16000

必须：

- 加载不同 GLB；
- 电池模型体积可区分；
- 总质量变化；
- CG变化或重新计算；
- 惯量重新计算；
- 功率/续航重新计算。

### 5.4 Propeller 15 → 14

必须：

- 加载不同尺寸桨模型；
- 视觉直径可区分；
- 性能曲线重新匹配；
- CW / CCW 资产必须为不同模型文件。

---

## 6. 选中、高亮和 Ghost

装配模式：

- 已安装组件显示正常材质；
- 未安装槽位可使用半透明 Ghost；
- 当前选中组件使用统一蓝色高亮；
- 同一时刻只应存在一个“当前检查类别”；
- 点击 3D 部件后右侧 Inspector 必须切换到对应组件类别。

未来工程错误联动要求：

- 点击某条 ERROR/WARNING；
- 3D 高亮对应部件；
- Inspector 定位对应类别。

---

## 7. 相机模式

以下按钮必须是真功能：

- 跟随
- 俯视
- 侧视
- 自由

要求：

- 点击后相机状态真实改变；
- `free` 模式允许 OrbitControls；
- `follow` 随飞机位置移动；
- `top` 为近似正俯视；
- `side` 提供明确侧向观察；
- 切换模式不能改变真实 Telemetry 数据。

---

## 8. 飞行实验视觉

飞行时必须由同一 `TelemetryFrame` 驱动：

- 3D飞机位置；
- 3D姿态；
- M1~M4 推力；
- 旋翼动画；
- CG；
- 重力；
- 风向/风速；
- 3D轨迹；
- Local Flight Map；
- RealtimeCharts。

禁止：

- `Math.random()` 生成飞行状态；
- 前端 `setInterval` 自行增加高度；
- 3D / Map / Charts 使用不同的模拟数据源。

---

## 9. Local Flight Map

必须显示：

- Home；
- UAV；
- X/Y 本地坐标；
- 飞行轨迹；
- Target；
- Waypoints；
- Wind；
- Flight Boundary；
- Scale。

分屏状态下 3D 与 Map 必须同时可读，不能互相挤压到无法操作。

---

## 10. Replay

Replay 固定时间点必须同步：

- 3D姿态/位置；
- Local Map当前位置与历史轨迹；
- 图表时间位置；
- 电机输出；
- 电池状态。

拖动 Replay 时间轴后，三种视图必须基于同一历史 `TelemetryFrame`。

---

## 11. 3D测试探针契约

P0实现阶段应在测试/开发模式暴露：

```ts
window.__UAV_VISUAL_TEST__
```

建议结构：

```ts
{
  version: '1.0',
  sceneReady: true,
  pixelRatio: 1,
  cameraMode: 'free',
  selectedSlot: 'motor',
  loadedAssets: [
    {
      slot: 'frame',
      componentId: 1,
      url: '/models/uav/v1_1/frame_650.glb'
    }
  ],
  aircraftBounds: {
    width: 0.9,
    height: 0.4,
    depth: 0.9
  },
  partBounds: {
    battery: { width: 0.16, height: 0.06, depth: 0.07 }
  },
  mounts: {
    M1: { x: 0.23, y: 0.23, z: 0.06 },
    M2: { x: 0.23, y: -0.23, z: 0.06 },
    M3: { x: -0.23, y: -0.23, z: 0.06 },
    M4: { x: -0.23, y: 0.23, z: 0.06 }
  }
}
```

此接口只服务自动验收，不参与业务计算。

---

## 12. Golden Screenshot 计划

**当前阶段不批准任何 Golden Screenshot。**

只有在结构测试通过并完成人工验收后，才批准下列 8 张基线：

1. `assembly-empty.png`
2. `assembly-complete-650.png`
3. `assembly-motor-selected.png`
4. `assembly-invalid.png`
5. `flight-3d-idle.png`
6. `flight-local-map.png`
7. `flight-split.png`
8. `replay-midflight.png`

Golden Screenshot 是“第一次合格实现后的批准结果”，不是设计输入。

---

## 13. 禁止为了过测试做的事情

- 不得把失败测试改为 `skip`；
- 不得放宽布局范围只为当前页面通过；
- 不得在 Probe 中伪造不存在的 GLB；
- 不得截图后把截图当成 Canvas 背景冒充3D；
- 不得把当前错误UI直接批准为 Golden；
- 不得让未知组件静默显示另一个组件的默认模型；
- 不得复制一套假工程数据只供 UI 测试。
