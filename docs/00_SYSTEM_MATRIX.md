# 无人机软件产品矩阵（冻结版）

## 1. 三系统划分

### 1. UAV Studio — 无人机数字设计与飞行验证平台

回答：**这架飞机怎么组成？这个设计基本合理吗？它能不能稳定完成基础飞行？**

本学期开发。

职责：
- 系统级组件数字装配
- 重量、CG、惯量、动力、电气、续航计算
- 装配检查
- 基础 3D 飞行验证
- Local Flight Map
- 数据分析与 Replay

明确不做：PX4 / Gazebo / ROS2 / AI / SLAM / 复杂环境。

### 2. Autonomy Studio — 无人机自主飞行与仿真开发平台

回答：**一架已经定义好的飞机，怎样在复杂世界中感知、规划并自主飞行？**

后续开发。

职责：
- 导入 UAV Studio 的 AircraftDefinition
- PX4 SITL
- Gazebo 环境
- ROS2
- Camera / LiDAR
- AI / SLAM / Planner / Avoidance
- 自主飞行算法验证

Autonomy Studio 不重复做无人机组件选型与装配。

### 3. UAV Operations — 无人机智能作业平台

回答：**无人机怎样完成真实行业任务，并形成业务闭环？**

后续产业化。

职责：
- 校园巡检
- 工业巡检
- 海上搜索救援
- 应急任务
- 实时视频与数据
- AI异常事件
- 工单 / 报告 / 闭环

## 2. 系统之间的核心关系

```text
UAV Studio
  │
  │ AircraftDefinition
  ▼
Autonomy Studio
  │
  │ Mission / Algorithm / Simulation Result
  ▼
UAV Operations
```

真实作业数据未来可反向用于算法优化和 UAV Studio 工程模型校准。

## 3. 当前学期边界

本仓库只实现 `UAV Studio V1`。

一句话边界：

> UAV Studio 止于基础飞行验证，不承担复杂环境仿真与自主飞行算法开发。
