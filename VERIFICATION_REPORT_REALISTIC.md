# Realistic Asset Verification Report

## GitHub baseline

`qiqidonebyte/uav-studio` `main`

`df88d9e3e4cb02138cbda1cbf631c7fdc2bad4d2`

本实现刻意不覆盖 Vue/后端业务代码，只替换现有 `v1_1` 模型文件，因此与本地已实现的爆炸视图、小标签、组件库和设置模块兼容。

## 实际执行验证

执行：

```bash
python tools/verify_realistic_assets.py
```

结果：

```text
174 / 174 checks passed
```

验证范围：

- 所有 19 个 GLB 均为可解析的 binary glTF 2.0；
- 所有几何节点均使用 PBRMaterial；
- 关键组件达到设定三角面复杂度下限；
- 650 机架、电机、15 寸桨、电池物理尺寸范围合理；
- 14/15 寸 CW 与 CCW 螺旋桨文件和几何不同；
- 所有组件缩略图均为 >=400px PNG；
- 完整参考整机 > 5 万三角形且 < 2 MiB；
- 整个运行时资产目录 < 5 MiB。

## 复杂度与文件量变化

以下旧文件尺寸来自本轮开发开始时 GitHub `main` 的对应资产；新文件为本包实测：

| 资产 | 云端旧版 | Realistic Edition | 体积倍率 | 新版三角形 |
|---|---:|---:|---:|---:|
| frame_650.glb | 37.1 KiB | 90.8 KiB | 2.45× | 6,092 |
| motor_5010_360kv.glb | 23.6 KiB | 103.1 KiB | 4.36× | 7,672 |
| esc_40a.glb | 8.8 KiB | 32.5 KiB | 3.71× | 1,296 |
| battery_6s_10000.glb | 8.0 KiB | 25.8 KiB | 3.23× | 852 |
| fc_v1.glb | 11.6 KiB | 24.2 KiB | 2.09× | 1,152 |
| gnss_m8n.glb | 7.9 KiB | 19.0 KiB | 2.40× | 872 |
| payload_camera_300g.glb | 13.1 KiB | 52.6 KiB | 4.03× | 2,664 |
| eduquad650_reference.glb | 194.0 KiB | 690.7 KiB | 3.56× | 54,056 |

## 性能控制

完整 `eduquad650_reference.glb`：

- 54,056 triangles
- 593 geometry nodes
- 27 种 PBR 材质
- 约 691 KiB

它不是制造级 CAD，也不是百万面离线模型；目标是浏览器实时工程可视化。

## 没有声称执行的测试

本包没有修改现有 Vue/Three.js 运行代码，因此没有为了这次资产升级伪造浏览器 E2E 结果。需要你本地覆盖后继续跑现有：

```bash
cd frontend
npm run build
npm run test
npm run test:p0:asset
npm run test:p0:scene
npm run e2e
```

现有组件 ID、文件名和 `asset_manifest` 结构保持兼容，原 P0 Asset Contract 的核心假设不变。