"""完整拍摄流程：拍照 → 原始照存档 → 人脸对齐 → 对齐照存档。

原始照与对齐照都带水印；对齐基于未打水印的原始帧。
拍摄成功（无论是否检测到人脸）返回 True，由调用方计数。
"""

from __future__ import annotations

import logging
from datetime import datetime

import cv2

from .alignment import FaceAligner
from .camera import Camera
from .config import Config
from .watermark import add_watermark

logger = logging.getLogger(__name__)

_TIME_FMT = "%Y/%m/%d %H:%M"
_FILE_FMT = "%Y%m%d_%H%M%S"


def run_once(config: Config) -> bool:
    """执行一次完整流程，返回拍摄是否成功。"""
    frame = Camera(config).capture()
    if frame is None:
        return False

    now = datetime.now()
    filename = f"photo_{now.strftime(_FILE_FMT)}.jpg"

    config.photo_dir.mkdir(parents=True, exist_ok=True)
    photo_path = config.photo_dir / filename
    cv2.imwrite(str(photo_path), add_watermark(
        frame, now.strftime(_TIME_FMT),
        config.watermark_copyright, config.watermark_location,
        config.watermark_alpha,
    ))
    logger.info("原始照片已保存: %s", photo_path)

    aligner = FaceAligner(config.target_size, config.eye_y_ratio)
    try:
        aligned = aligner.process(frame)
        if aligned is None:
            logger.warning("未检测到人脸，跳过对齐（原始照片已保存）")
        else:
            config.aligned_dir.mkdir(parents=True, exist_ok=True)
            aligned_path = config.aligned_dir / f"aligned_{filename}"
            cv2.imwrite(str(aligned_path), add_watermark(
                aligned, now.strftime(_TIME_FMT),
                config.watermark_copyright, config.watermark_location,
                config.watermark_alpha,
            ))
            logger.info("对齐照片已保存: %s", aligned_path)
    finally:
        aligner.close()

    return True
