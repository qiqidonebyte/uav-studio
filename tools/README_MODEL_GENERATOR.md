# 3D 教学模型生成器

`generate_uav_v1_1_models.py` 是本模型包的可复现生成脚本，方便后续学生扩展资产。

它不是项目运行依赖；前端运行只读取已经生成好的 `.glb` 文件。

如需重新生成模型：

```bash
python -m pip install numpy trimesh matplotlib
python tools/generate_uav_v1_1_models.py
```

脚本会写入：

`frontend/public/models/uav/v1_1/`

建模坐标固定为：+X 机头、+Y 向上、+Z 机体右侧，单位 m。
