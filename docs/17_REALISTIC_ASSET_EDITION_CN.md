# UAV Studio — EduQuad-650 Realistic Edition 2.0

## 目标

把现有 V1.1 教学示意模型升级为“教学级工程数字样机”，但不改变组件 ID、文件名、数据库 visual contract 和现有装配/爆炸/Replay 逻辑。

因此本包直接覆盖：

`frontend/public/models/uav/v1_1/`

即可生效。

## 本轮真实感升级

- **机架**：碳纤维上下板、圆管机臂、阳极氧化夹具、紧固件、电子设备导轨、电池托盘、绑带、落地架和橡胶脚。
- **5010 / 4008 外转子电机**：通风式钟罩、定子结构、铜绕组、轴承座、桨夹、六角桨帽、安装耳和三相线。
- **ESC**：PCB、MOSFET 阵列、散热底板、散热鳍片、电容、状态灯、三相线、电源线和信号插头。
- **螺旋桨**：不再是平板桨；使用多截面叶片，沿半径方向改变弦长和桨距，CW / CCW 为不同真实几何。
- **LiPo**：电芯筋、热缩外皮、端盖、双绑带、平衡头、红黑主电源线、XT90 和标签层。
- **电源模块**：PCB、霍尔传感器、分流器、大电流端子、遥测口和线束。
- **飞控**：MCU、IMU、气压计、Flash、USB、JST、排针、减震柱、安装垫片、方向箭头和状态灯。
- **GNSS**：上下壳、陶瓷贴片天线、方向箭头、线缆出口和线束。
- **相机载荷**：三轴云台结构、关节电机、相机机身、握柄、后屏、镜头筒、对焦环和前镜片。

## 材质

所有几何采用 glTF 2.0 metallic-roughness PBR 材质，而不是简单 face color：

- CarbonFiber
- MachinedAluminium
- Red / Blue Anodized Aluminium
- Copper
- PCB
- Rubber
- Connector Plastic / Gold Contacts
- Lens Glass
- Battery Wrap
- Emissive Status LED

现有 `DroneScene.vue` 已经使用 ACES tone mapping、环境反射和主辅光，因此覆盖后会自动利用这些材质信息。

## 性能边界

完整 EduQuad-650 参考样机约 **5.4 万三角形**、GLB 约 **0.7 MB**。这是刻意控制后的工程可视化模型，不是百万面离线渲染资产，学校普通电脑仍有较好的 WebGL 余量。

## 兼容性

本包没有修改：

- 后端工程计算；
- Component.visual 数据结构；
- 组件 ID；
- 文件名；
- 装配页接口；
- 爆炸视图；
- 组件标签；
- Replay；
- Flight Lab 状态机。

所以如果你本地已经覆盖了之前的“爆炸视图 + 小标签”版本，这次不会冲掉那些代码，只会升级模型资产。

## 真实性声明

这些模型是根据常见 650 级多旋翼、电调、外转子电机、LiPo、飞控和云台的工程结构制作的**通用教学模型**。在没有具体厂家 STEP/CAD/尺寸图的情况下，不宣称孔位、公差、内部结构与某一商业产品完全一致。
