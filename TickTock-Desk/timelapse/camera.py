"""摄像头采集：打开 → 应用画质参数 → 预热稳定 → 拍一帧 → 立即释放。"""

from __future__ import annotations

import logging
import time

import cv2
import numpy as np

from .config import Config

logger = logging.getLogger(__name__)


class Camera:
    def __init__(self, config: Config):
        self.config = config

    def _apply_settings(self, cap: cv2.VideoCapture) -> None:
        cfg = self.config
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, cfg.buffersize)
        cap.set(cv2.CAP_PROP_FPS, cfg.fps)

        # 画质参数：部分驱动不支持某项时 set 会静默失败，记录实际值即可
        for prop, value, name in (
            (cv2.CAP_PROP_BRIGHTNESS, cfg.brightness, "亮度"),
            (cv2.CAP_PROP_CONTRAST, cfg.contrast, "对比度"),
            (cv2.CAP_PROP_SATURATION, cfg.saturation, "饱和度"),
            (cv2.CAP_PROP_SHARPNESS, cfg.sharpness, "锐度"),
            (cv2.CAP_PROP_AUTO_WB, 1, "自动白平衡"),
            (cv2.CAP_PROP_AUTOFOCUS, 1, "自动对焦"),
        ):
            cap.set(prop, value)
            logger.debug("%s: 设置=%s 实际=%.2f", name, value, cap.get(prop))

    def _log_state(self, cap: cv2.VideoCapture) -> None:
        cfg = self.config
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(
            "摄像头 %d 就绪: %dx%d @ %.1f FPS (目标 %dx%d)",
            cfg.camera_index, actual_w, actual_h, cap.get(cv2.CAP_PROP_FPS),
            cfg.frame_width, cfg.frame_height,
        )

    def capture(self) -> np.ndarray | None:
        """拍一帧 BGR 图像；任何失败返回 None。返回后摄像头已释放。"""
        cfg = self.config
        cap = cv2.VideoCapture(cfg.camera_index)
        try:
            if not cap.isOpened():
                logger.error("无法打开摄像头 %d（被占用或不存在）", cfg.camera_index)
                return None

            self._apply_settings(cap)
            self._log_state(cap)

            logger.info("预热 %d 帧 + 稳定 %.1f 秒...", cfg.warmup_frames, cfg.settle_seconds)
            for i in range(cfg.warmup_frames):
                ret, _ = cap.read()
                if not ret:
                    logger.warning("预热第 %d 帧读取失败", i + 1)
                    break
            time.sleep(cfg.settle_seconds)

            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("拍摄失败：最终帧读取失败")
                return None
            return frame
        finally:
            cap.release()
