"""右下角半透明水印：版权行 + 时间/地点行。"""

from __future__ import annotations

import cv2
import numpy as np

_FONT = cv2.FONT_HERSHEY_DUPLEX
_FONT_SCALE = 0.6
_THICKNESS = 1
_MARGIN_RIGHT = 30
_MARGIN_BOTTOM = 30
_LINE_SPACING = 8


def add_watermark(image: np.ndarray, time_text: str, copyright_text: str,
                  location: str, alpha: float = 0.7) -> np.ndarray:
    """在副本上绘制水印，不修改原图。

    第二行文字为 time_text + location，如 '2026/10/04 09:35 Qingdao'。
    """
    canvas = image.copy()
    time_line = f"{time_text} {location}".strip()
    h, w = canvas.shape[:2]
    color = (255, 255, 255)

    (copy_w, copy_h), _ = cv2.getTextSize(copyright_text, _FONT, _FONT_SCALE, _THICKNESS)
    (time_w, time_h), _ = cv2.getTextSize(time_line, _FONT, _FONT_SCALE, _THICKNESS)

    copyright_x = w - copy_w - _MARGIN_RIGHT
    copyright_y = h - time_h - _MARGIN_BOTTOM - _LINE_SPACING
    time_x = w - time_w - _MARGIN_RIGHT
    time_y = h - _MARGIN_BOTTOM

    overlay = canvas.copy()
    cv2.putText(overlay, copyright_text, (copyright_x, copyright_y),
                _FONT, _FONT_SCALE, color, _THICKNESS, cv2.LINE_AA)
    cv2.putText(overlay, time_line, (time_x, time_y),
                _FONT, _FONT_SCALE, color, _THICKNESS, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
    return canvas
