# UAV Studio V1 中文系统与真实装配规格（冻结版）

版本：V1.1  
适用对象：Quad-X 四旋翼教学平台

## 1. 结论

UAV Studio V1 的组件体系必须尽量对应真实四旋翼无人机，但 V1 不追求把螺丝、线束、扎带等所有物料都建模。

采用“真实系统级组件 + 简化工程模型”的原则。

### V1 必需组件

1. 机架 Frame
2. 电机 Motor ×4
3. 电调 ESC ×4
4. 螺旋桨 Propeller ×4
5. 电池 Battery ×1
6. 电源模块 Power Module / PDB ×1
7. 飞控 Flight Controller ×1

### V1 可选组件

8. GNSS / Compass ×0~1
9. Payload ×0~1

### V1 暂不单独建模

- 遥控接收机
- 数传链路
- 图传链路
- 蜂鸣器
- LED
- 线束与连接器
- 脚架
- 螺丝与紧固件

这些真实存在，但 V1 不影响核心装配与基础飞行动力学，可在后续版本加入。

---

## 2. 为什么必须加入 Flight Controller 和 Power Module

### Flight Controller

真实四旋翼必须存在飞控。

V1 中即使不接 PX4，界面也必须存在“飞控”组件。

Python SimpleSimulator 中的教学 PID 控制器，可以被理解为运行在这个虚拟飞控上的控制算法。

这样 V2 接 PX4 时，产品概念不需要重做。

### Power Module / PDB

真实四旋翼需要把电池电能分配给四个 ESC，同时通常需要电压/电流测量。

V1 将：

- PDB
- Power Module
- 电流/电压检测

简化成一个 `power_module` 组件。

---

## 3. V1 组件分类

中文界面显示：

- 机架
- 电机
- 电调
- 螺旋桨
- 电池
- 电源模块
- 飞控
- GNSS/罗盘
- 任务载荷

代码和 API 内部字段仍保持英文：

- frame
- motor
- esc
- propeller
- battery
- power_module
- flight_controller
- gnss
- payload

禁止把数据库字段和 API key 改成中文。

原则：

> 中文只属于显示层，英文属于数据与代码层。

---

## 4. Quad-X 电机与螺旋桨方向

V1 冻结以下编号：

```text
                  机头 +X

              M1           M2
          前左                 前右
           CCW                 CW

                  [ FC ]

              M4           M3
          后左                 后右
            CW                 CCW
```

即：

- M1：前左，CCW
- M2：前右，CW
- M3：后右，CCW
- M4：后左，CW

对角电机旋向相同。

螺旋桨必须匹配电机旋向。

如果旋向不匹配：

- 装配检查必须报阻断错误；
- 不允许进入飞行实验。

注意：未来接 PX4 时，可以在 Adapter 层做编号映射；V1 不修改此冻结定义。

---

## 5. 真实且适合教学的装配流程

不采用“六个下拉框同时选完”的方式。

采用“装配步骤 + 3D 槽位”的交互。

### 第 1 步：选择机架

用户选择：

- Frame

系统建立：

- 四个电机槽位
- 电池槽位
- 飞控槽位
- 电源模块槽位
- GNSS 槽位
- 载荷槽位

中央 3D 模型出现空机架。

---

### 第 2 步：安装动力系统

选择：

- Motor
- ESC

默认一次应用到四个机臂。

中央 3D：

- M1~M4 出现电机与 ESC；
- 显示编号；
- 显示旋向。

用户可以点击 M1~M4 检查单个位置。

---

### 第 3 步：安装供电系统

选择：

- Power Module / PDB
- Battery

检查：

- 电池电压范围
- ESC 电压范围
- 电池最大持续放电电流
- 四个电机最大需求电流
- 电源模块最大电流

中央 3D：

- 显示电池；
- 显示电源模块；
- CG 立即更新。

---

### 第 4 步：安装飞控与导航

选择：

- Flight Controller
- 可选 GNSS / Compass

飞控默认安装在机体中心。

界面显示：

- 飞控方向箭头（机头方向）；
- GNSS 安装位置。

V1 不模拟 GNSS 信号，但其：

- 质量
- 安装位置

参与 CG 与惯量计算。

---

### 第 5 步：安装任务载荷

选择：

- Payload

支持固定安装槽位，至少：

- 前部槽位
- 底部中心槽位

V1 不需要自由拖拽。

安装后：

- 质量更新；
- CG 更新；
- 惯量更新；
- 预计续航更新。

---

### 第 6 步：安装螺旋桨与检查旋向

为了符合真实装调安全逻辑，螺旋桨放在最后一步。

用户选择 Propeller 型号。

系统根据 M1~M4 自动要求：

- M1：CCW Prop
- M2：CW Prop
- M3：CCW Prop
- M4：CW Prop

3D 中显示桨叶方向标记。

---

### 第 7 步：装配检查

进入飞行实验前必须执行：

**装配检查**

检查分两类：

#### 阻断错误

出现时不能进入 Flight Lab：

- 必需组件缺失
- 总推力不足以悬停
- ESC 最大电流小于 Motor 最大电流
- Battery 最大持续放电能力不足
- 电压明显不兼容
- Propeller 旋向错误
- Motor / Propeller 组合没有可用性能数据且无法安全估算

#### 警告

可以进入 Flight Lab，但必须显示：

- 推重比 < 1.5
- CG 偏移较大
- 预计续航较短
- 载荷余量过低

---

## 6. 交互方式

### 左侧

标题：

**装配流程**

使用步骤列表：

1. 机架
2. 动力系统
3. 供电系统
4. 飞控与导航
5. 任务载荷
6. 螺旋桨
7. 装配检查

每步状态：

- 未配置
- 已配置
- 警告
- 错误

点击步骤切换当前组件选择器。

### 中央

持续显示同一架 3D 数字无人机。

当前可安装槽位发光。

用户操作：

1. 点击槽位；
2. 左侧选择组件；
3. 点击“安装”。

V1 不需要自由拖拽。

这是比自由拖拽更稳定、也更符合教学步骤的交互。

### 右侧

标题根据上下文改变：

- 整机参数
- 电机 M1
- 电池
- 飞控
- 任务载荷
- 装配检查

用户点击 3D 部件后，右侧显示对应组件参数。

---

## 7. 动力系统不能只看 Motor.max_thrust

真实无人机推力由：

> 电机 + 螺旋桨 + 电池电压

共同决定。

因此 V1 不应让“换螺旋桨后最大推力完全不变”。

### 推荐 V1 方案

在 Motor 的 `parameters_json` 中保存少量教学测试曲线：

```json
{
  "kv": 360,
  "profiles": [
    {
      "battery_voltage_v": 22.2,
      "propeller_id": 3,
      "points": [
        {"throttle": 0.25, "thrust_n": 3.5, "current_a": 2.8, "power_w": 62},
        {"throttle": 0.50, "thrust_n": 9.8, "current_a": 8.5, "power_w": 189},
        {"throttle": 0.75, "thrust_n": 16.2, "current_a": 15.5, "power_w": 344},
        {"throttle": 1.00, "thrust_n": 22.0, "current_a": 22.0, "power_w": 488}
      ]
    }
  ]
}
```

仿真时做线性插值。

这样：

- 换 Propeller 会影响推力；
- 换 Battery 电压会影响可用性能；
- 功率与电流有真实数据来源；
- 不需要实现复杂螺旋桨空气动力学。

所有示例曲线必须标记：

`Educational Sample Data`

---

## 8. 中文系统规则

所有用户可见文本必须为中文。

例如：

| Internal | 中文显示 |
|---|---|
| Assembly | 无人机装配 |
| Flight Lab | 飞行实验 |
| History | 实验记录 |
| Components | 组件 |
| Aircraft | 整机 |
| Attitude | 姿态 |
| Power | 动力/电源 |
| Motors | 电机 |
| Start Simulation | 开始仿真 |
| Arm | 解锁 |
| Takeoff | 起飞 |
| Land | 降落 |
| Reset | 复位 |
| RUNNING | 运行中 |
| HOVERING | 悬停 |
| ARMED | 已解锁 |
| IDLE | 待机 |
| TAKING_OFF | 起飞中 |
| LANDING | 降落中 |

内部 enum 仍使用英文。

---

## 9. 当前前端原型必须修正的问题

### 9.1 当前组件不完整

目前仅：

Frame / Motor / ESC / Propeller / Battery / Payload

必须加入：

- Power Module
- Flight Controller

建议加入：

- GNSS

### 9.2 当前示例单位错误

Telemetry 协议规定姿态使用 rad。

当前 Demo 中：

```text
roll = -0.8
pitch = 1.2
yaw = 89.6
```

却又在 UI 中按 rad 转为 degree。

这是错误的。

Demo 必须改成例如：

```text
roll = -0.8° = -0.01396 rad
pitch = 1.2° = 0.02094 rad
yaw = 89.6° = 1.5638 rad
```

### 9.3 当前质量与重力示例不一致

任何：

- Total Mass
- Gravity
- T/W

禁止分别硬编码。

必须全部由同一份 Aircraft 工程计算结果产生。

### 9.4 Three.js 姿态转换需要集中处理

当前位置转换已有 `toThree()`，
但姿态转换仍为手写 Euler 映射。

最终必须建立统一：

```text
simulationPoseToThree()
```

同时处理：

- Position
- Orientation

避免坐标系显示错误。

---

## 10. V1 最终教学闭环

```text
真实系统组件认知
        ↓
按真实顺序数字装配
        ↓
电气/动力兼容检查
        ↓
CG / 惯量 / 推重比
        ↓
进入飞行实验
        ↓
四旋翼独立推力
        ↓
风扰动
        ↓
姿态变化
        ↓
飞控补偿
        ↓
实时曲线
        ↓
Replay 分析
```

这才是 UAV Studio V1 的完整产品逻辑。
