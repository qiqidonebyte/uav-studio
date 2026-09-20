# UAV Studio — 遥控系统调试 V1

这是在 `V2 + PX4 Bridge V1 + 飞控与传感器 V1 + 安全设置 V1` 基线上增加的“遥控系统”直接覆盖补丁。

## 主要功能

- 真实 PX4 模式读取 `RC_CHANNELS`：CH1–CH18 原始 PWM、通道数量、RSSI、数据年龄。
- 同时监听 `MANUAL_CONTROL` 作为手动输入状态参考，但网页不会发送手动控制消息。
- 虚拟遥控教学输入：双摇杆可视化 + CH1–CH4 滑杆，只改变浏览器教学状态，不控制真实飞机。
- 主通道映射：`RC_MAP_ROLL / PITCH / THROTTLE / YAW`。
- 通道校准：`RCx_MIN / RCx_TRIM / RCx_MAX / RCx_REV`。
- 支持 PX4 当前合法的映射值 `0 = 未分配`，并在教学检查中判定为待处理错误。
- 行程采集：从实时/虚拟 RC 输入采集 Min/Max，中位采集后仅进入本地草稿，点击应用才写 PX4。
- 映射重复、行程异常、Trim 超范围、方向参数非法等自动诊断。
- 与安全设置联动显示 `COM_RC_LOSS_T` 与 `NAV_RCL_ACT`。
- 调试 JSON 报告增加 RC 输入、映射、校准、评分与问题列表。

## PX4 main 兼容说明

当前 PX4 main 参数参考保留 `RCx_MIN/MAX/TRIM/REV` 与 `RC_MAP_*`。历史上的每通道 `RCx_DZ` 已不在当前 main 参数表，因此本页的“教学死区”只用于网页输入归一化，不向 PX4 写入，避免出现无效参数写入。

## 使用

直接把 ZIP 解压到当前 `uav-studio` 根目录并覆盖同名文件。

不新增第三方依赖。继续使用已有 `pymavlink` PX4 Bridge。

真实接收机接入并由 PX4 发布 `RC_CHANNELS` 后，可切换“真实 RC 输入”。PX4 SIH 默认没有物理接收机时，使用“虚拟教学输入”进行通道映射与校准练习。
