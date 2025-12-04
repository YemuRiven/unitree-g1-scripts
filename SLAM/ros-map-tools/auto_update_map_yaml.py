#!/usr/bin/env python3
"""
自动根据原始PGM、裁剪后PGM和原yaml，生成新的yaml。

依赖：
    pip install opencv-python pillow pyyaml

用法示例：
    python auto_update_map_yaml.py \
        orig_map.yaml \
        orig_map.pgm \
        cropped_map.pgm \
        new_map.yaml
"""

import sys
import os
import yaml
import cv2
import numpy as np
from PIL import Image
import math   # <-- 新增，用于识别 nan


def read_size(path):
    """用 Pillow 读一下图像尺寸 (width, height)."""
    with Image.open(path) as im:
        return im.size  # (w, h)


def estimate_offset_by_template(orig_img, crop_img):
    """
    使用模板匹配估算裁剪偏移。
    orig_img: 原始大图 (H0, W0) uint8
    crop_img: 裁剪后小图 (H1, W1) uint8

    返回: (x0, y0)  —— 小图左上角在大图中的坐标
    """
    # OpenCV 要求 (H, W)，单通道
    # 使用 TM_SQDIFF_NORMED，值越小匹配越好
    res = cv2.matchTemplate(orig_img, crop_img, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    x0, y0 = min_loc
    print(f"[INFO] 模板匹配 min_val={min_val:.6f}, 估计偏移 (x={x0}, y={y0})")
    return x0, y0


def main():
    if len(sys.argv) != 5:
        print("用法：")
        print("  python auto_update_map_yaml.py "
              "orig_yaml orig_pgm cropped_pgm out_yaml")
        sys.exit(1)

    orig_yaml   = sys.argv[1]
    orig_pgm    = sys.argv[2]
    cropped_pgm = sys.argv[3]
    out_yaml    = sys.argv[4]

    if not os.path.isfile(orig_yaml):
        print("找不到 orig_yaml:", orig_yaml)
        sys.exit(1)
    if not os.path.isfile(orig_pgm):
        print("找不到 orig_pgm:", orig_pgm)
        sys.exit(1)
    if not os.path.isfile(cropped_pgm):
        print("找不到 cropped_pgm:", cropped_pgm)
        sys.exit(1)

    # 1. 读取原始 YAML
    with open(orig_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    resolution = float(data["resolution"])
    origin = data.get("origin", [0.0, 0.0, 0.0])
    if len(origin) < 3:
        origin = [origin[0], origin[1], 0.0]

    # === 新增：自动将 yaw 中的 nan 替换为 0.0 ===
    try:
        yaw = float(origin[2])
        if math.isnan(yaw):
            yaw = 0.0
    except:
        yaw = 0.0
    origin[2] = yaw
    # ================================================

    print("[INFO] 原 origin:", origin)
    print("[INFO] 分辨率 resolution:", resolution)

    # 2. 读取图像（灰度）
    orig_img = cv2.imread(orig_pgm, cv2.IMREAD_GRAYSCALE)
    crop_img = cv2.imread(cropped_pgm, cv2.IMREAD_GRAYSCALE)

    if orig_img is None:
        print("无法读取原始PGM:", orig_pgm)
        sys.exit(1)
    if crop_img is None:
        print("无法读取裁剪PGM:", cropped_pgm)
        sys.exit(1)

    H0, W0 = orig_img.shape
    H1, W1 = crop_img.shape
    print(f"[INFO] 原图尺寸:   {W0}x{H0}")
    print(f"[INFO] 裁剪后尺寸: {W1}x{H1}")

    if W1 > W0 or H1 > H0:
        print("[ERROR] 裁剪后图比原图还大，可能传反了？")
        sys.exit(1)

    # 3. 模板匹配估计偏移
    x0, y0 = estimate_offset_by_template(orig_img, crop_img)

    # 4. 计算每个方向裁掉多少像素
    left_px   = x0
    top_px    = y0
    right_px  = W0 - (x0 + W1)
    bottom_px = H0 - (y0 + H1)

    print(f"[INFO] 估计裁剪像素："
          f"left={left_px}, right={right_px}, "
          f"top={top_px}, bottom={bottom_px}")

    if min(left_px, right_px, top_px, bottom_px) < 0:
        print("[WARN] 有负数裁剪值，匹配可能不准确，请人工检查。")

    # 5. 依据 ROS 地图定义调整 origin
    # 图像坐标原点在左上角；origin 是“左下角”世界坐标。
    # 裁掉 left_px → x 增加 left_px * res
    # 裁掉 bottom_px → y 增加 bottom_px * res
    new_origin_x = origin[0] + left_px * resolution
    new_origin_y = origin[1] + bottom_px * resolution
    new_origin_yaw = origin[2]

    new_origin = [float(new_origin_x),
                  float(new_origin_y),
                  float(new_origin_yaw)]
    print("[INFO] 新 origin:", new_origin)

    # 6. 写出新的 YAML
    # === 新增：保持原 YAML 的 image 路径目录结构 ===
    orig_image_path = data["image"]
    orig_image_dir = os.path.dirname(orig_image_path)
    new_image_name = os.path.basename(cropped_pgm)

    if orig_image_dir == "":
        # 原 YAML 是相对路径
        data["image"] = new_image_name
    else:
        # 保持原目录不变
        data["image"] = os.path.join(orig_image_dir, new_image_name)
    # =================================================

    data["origin"] = new_origin

    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)

    print("[OK] 已生成新 YAML 文件:", out_yaml)
    print("[OK] image 路径:", data["image"])


if __name__ == "__main__":
    main()

