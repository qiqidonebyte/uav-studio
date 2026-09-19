# 爆炸视图测试计划

## 单元测试

`frontend/tests/exploded-view.test.ts`

验证：

- frame 爆炸偏移恒为 0；
- propeller 比 motor 位移更大、层级更高；
- ESC / motor / propeller 的动力组层级；
- GNSS / FC 向上；
- battery / payload 向下；
- progress 在 0~1 之间插值，并对越界值 clamp。

## Three.js Scene Contract

在现有 `p0-scene-contract.mjs` 增加：

- 整机 / 爆炸视图按钮存在；
- 进入爆炸视图后 `explosionProgress > 0.98`；
- frame 保持固定；
- battery 向下；
- flight controller 向上；
- motor 径向距离增加；
- propeller 垂直位移大于 motor；
- 爆炸提示面板显示；
- 默认不再显示 CW/CCW 标签；
- 只有螺旋桨步骤的整机模式显示旋向标签；
- 切回整机后所有组件恢复原 datum。

## 视觉回归候选

`p0-visual-capture.mjs` 新增：

`03-assembly-exploded-current.png`

正式验收后可以升级为 Golden Screenshot。
