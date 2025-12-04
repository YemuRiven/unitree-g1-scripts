# 🗺️ ROS2 Map Tools — 自动裁剪 ROS 地图 & 自动生成 YAML

一个用于 ROS2 / Nav2 环境下，方便地 **裁剪地图（PGM）并自动计算新 origin、生成新 YAML 文件** 的脚本

标准流程：

- 手动清理 SLAM 采集生成的地图  
- 使用 GIMP 等裁剪地图后重新生成正确 YAML  

---

## 📌 功能特性

### ✔ 自动读取原始地图尺寸

从原始 `.pgm` 和裁剪后的 `.pgm` 中读取高度和宽度

### ✔ 使用模板匹配自动计算裁剪偏移

采用 `cv2.matchTemplate` 自动估计裁剪区域在原图中的位置，得到：

- `left_px`  
- `right_px`  
- `top_px`  
- `bottom_px`  
### ✔ 自动生成新的 YAML

根据裁剪偏移与 resolution 自动计算新 origin：

```text
new_origin_x = origin[0] + left_px   * resolution  
new_origin_y = origin[1] + bottom_px * resolution
```
### ✔ 自动处理 origin 中的 nan → 0.0

避免 map_server 解析失败

### 保留原始 YAML 的所有字段
如：
- negate
- free_thresh
- occupied_thresh
- mode（trinary）
- image 字段自动更新为裁剪后的文件名
---
## 📦 安装环境（Conda）
```text
conda env create -f environment.yaml
conda activate ros-map-tools
```
---
## 🚀 使用示例
输入：
- 原地图：dataset/original_map.pgm
- 原 YAML：dataset/original_map.yaml
- 裁剪后的 PGM：dataset/cropped_map.pgm
- 想输出的新 YAML：dataset/new_map.yaml

运行：
```text
python auto_update_map_yaml.py \
    dataset/original_map.yaml \
    dataset/original_map.pgm \
    dataset/cropped_map.pgm \
    dataset/new_map.yaml
```
输出：
- 原图尺寸
- 裁剪后尺寸
- 模板匹配偏移
- 自动计算的新 origin
- 输出的新 YAML 路径


