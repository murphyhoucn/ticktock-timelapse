#!/usr/bin/env python3
"""摄像头能力探测与画质检查（手动工具）。

探测支持的分辨率列表、打印当前全部参数，并拍一张测试照分析清晰度/亮度。
    python check_camera.py [--camera 0]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

import cv2
import numpy as np

RESOLUTIONS = [(3840, 2160), (2560, 1440), (1920, 1080),
               (1280, 720), (640, 480)]

PROPERTIES = [
    (cv2.CAP_PROP_FRAME_WIDTH, "宽度"),
    (cv2.CAP_PROP_FRAME_HEIGHT, "高度"),
    (cv2.CAP_PROP_FPS, "帧率"),
    (cv2.CAP_PROP_BRIGHTNESS, "亮度"),
    (cv2.CAP_PROP_CONTRAST, "对比度"),
    (cv2.CAP_PROP_SATURATION, "饱和度"),
    (cv2.CAP_PROP_HUE, "色调"),
    (cv2.CAP_PROP_GAIN, "增益"),
    (cv2.CAP_PROP_EXPOSURE, "曝光"),
    (cv2.CAP_PROP_SHARPNESS, "锐度"),
    (cv2.CAP_PROP_AUTOFOCUS, "自动对焦"),
    (cv2.CAP_PROP_AUTO_WB, "自动白平衡"),
    (cv2.CAP_PROP_AUTO_EXPOSURE, "自动曝光"),
]


def probe_capabilities(cap: cv2.VideoCapture) -> None:
    print("=== 支持的分辨率 ===")
    supported = []
    for width, height in RESOLUTIONS:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        actual = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        mark = "支持" if actual == (width, height) else f"不支持 (实际 {actual[0]}x{actual[1]})"
        print(f"  {width}x{height}: {mark}")
        if actual == (width, height):
            supported.append((width, height))

    print("\n=== 当前参数 ===")
    for prop, name in PROPERTIES:
        value = cap.get(prop)
        if prop in (cv2.CAP_PROP_AUTOFOCUS, cv2.CAP_PROP_AUTO_WB):
            shown = "开启" if value > 0 else "关闭"
        else:
            shown = f"{value:.2f}"
        print(f"  {name}: {shown}")


def capture_and_analyze(cap: cv2.VideoCapture) -> bool:
    print("\n=== 拍摄测试照 ===")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    for _ in range(10):  # 预热
        cap.read()
    ret, frame = cap.read()
    if not ret:
        print("拍摄失败")
        return False

    filename = f"camera_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(filename, frame)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray))
    print(f"测试照已保存: {filename} ({frame.shape[1]}x{frame.shape[0]})")
    print(f"清晰度分数: {blur_score:.2f} (>100 为清晰)")
    print(f"平均亮度: {brightness:.2f} (理想 50-200)")
    if blur_score <= 100:
        print("提示：图像偏模糊，检查对焦或光线")
    if not 50 < brightness < 200:
        print("提示：亮度异常，检查环境光")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="摄像头能力探测与画质检查")
    parser.add_argument("--camera", type=int, default=0, help="摄像头索引")
    args = parser.parse_args(argv)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"无法打开摄像头 {args.camera}（被占用或不存在）")
        return 1
    try:
        probe_capabilities(cap)
        capture_and_analyze(cap)
    finally:
        cap.release()
    print("\n测试完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
