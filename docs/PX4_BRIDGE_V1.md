# PX4 Bridge V1 架构

```text
Browser / Vue3
    |
    | HTTP 8001 (polling 300 ms)
    v
UAV-Studio PX4 Bridge (FastAPI)
    |
    | pymavlink / UDP 14540
    v
PX4 SITL + SIH
    |
    | ATTITUDE / LOCAL_POSITION_NED / GPS / SYS_STATUS / ACTUATOR
    v
Three.js DroneScene
```

## 为什么 V1 用 pymavlink 单连接

PX4 SITL 单实例默认 offboard API 端口为 UDP 14540。MAVSDK-Python 和 pymavlink 都作为独立消费者直接绑定同一端口时，部署容易出现端口争用或消息分配不确定。V1 的目标是先打通最小闭环，因此只用 pymavlink。

后续如果要引入 MAVSDK，可采用：

```text
PX4 -> mavlink-router -> MAVSDK endpoint
                   -> pymavlink endpoint
```

## 坐标转换

PX4 `LOCAL_POSITION_NED`：

- X: North
- Y: East
- Z: Down

UAV-Studio 当前仿真契约采用 Z 向上，因此 Bridge 返回：

```text
x = NED.x
y = NED.y
z = -NED.z
vz = -NED.vz
```

## Motor Test

PX4 `MAV_CMD_ACTUATOR_TEST`：

- command: 310
- param1: normalized test value
- param2: timeout seconds
- param5: output function
- Motor1..Motor4 output functions: 101..104

V1 UI 限制输出最大 0.35，默认 0.25，测试 1.5 s。

## 参数工具

参数名限制为 PX4 MAVLink parameter protocol 的 16 字符名称。写入前 Bridge 会先读取参数，从 PX4 返回值中保留 `param_type`，再发送 `PARAM_SET`。
