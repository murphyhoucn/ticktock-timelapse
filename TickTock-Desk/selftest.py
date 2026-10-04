#!/usr/bin/env python3
"""环境自检（手动工具）：Python 版本、依赖包、MediaPipe 模型、摄像头。

部署或迁移环境后先跑一遍这个，确认链路完好：
    python selftest.py
"""

from __future__ import annotations

import sys

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, func) -> bool:
    print(f"\n=== {name} ===")
    try:
        ok = func()
    except Exception as exc:  # noqa: BLE001 - 自检工具需要吞掉任何错误继续
        print(f"异常: {exc}")
        ok = False
    print(f"{'通过' if ok else '未通过'}: {name}")
    return ok


def check_python() -> bool:
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    return version >= (3, 8)


def check_packages() -> bool:
    import cv2
    import mediapipe
    import numpy

    print(f"OpenCV {cv2.__version__}")
    print(f"MediaPipe {mediapipe.__version__}")
    print(f"NumPy {numpy.__version__}")
    return True


def check_face_model() -> bool:
    import mediapipe as mp

    mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.5)
    mesh.close()
    print("FaceMesh 模型加载成功")
    return True


def check_camera() -> bool:
    import cv2

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("摄像头 0 无法打开（被占用或不存在）")
        return False
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"摄像头 0: {width}x{height}")
        ret, _ = cap.read()
        print("读取测试帧" + ("成功" if ret else "失败"))
        return ret
    finally:
        cap.release()


def main() -> int:
    print("TimeLapse@Desk 环境自检")
    results = [
        check("Python 版本", check_python),
        check("依赖包", check_packages),
        check("MediaPipe 模型", check_face_model),
        check("摄像头", check_camera),
    ]
    failed = results.count(False)
    print(f"\n结果: {len(results) - failed}/{len(results)} 项通过")
    if failed:
        print("请先解决未通过项，再运行 capture_once.py")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
