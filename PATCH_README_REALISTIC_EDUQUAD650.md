# UAV Studio — EduQuad-650 Realistic Edition 2.0

基线检查：GitHub `qiqidonebyte/uav-studio` main，最新 HEAD：

`df88d9e3e4cb02138cbda1cbf631c7fdc2bad4d2`

## 覆盖方式

把 ZIP 解压到项目根目录覆盖即可。

本包主要覆盖：

`frontend/public/models/uav/v1_1/`

没有覆盖 Vue 页面、后端业务代码、组件库、设置、飞行状态机或你已经做好的爆炸视图代码。

## 为什么仍然使用 v1_1 路径

这是兼容性设计。当前数据库与 Component.visual 已经引用 v1_1 文件名。保持路径和文件名不变，可以在不做数据库迁移的前提下直接把模型质量升级。

## 生成器

`tools/generate_uav_realistic_edition.py`

可以完全重新生成所有 GLB、缩略图和参考整机模型。

## 验证

```bash
python tools/verify_realistic_assets.py
```

详见 `VERIFICATION_REPORT_REALISTIC.md`。
