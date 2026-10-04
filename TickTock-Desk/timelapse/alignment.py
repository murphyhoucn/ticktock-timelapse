"""基于 MediaPipe FaceMesh 的人脸对齐。

只做旋转 + 平移（不缩放），把双眼中心对齐到目标画幅上部固定位置，
使每天的延时视频里头部位置稳定。无人脸时返回 None，由上层决定降级行为。
"""

from __future__ import annotations

import logging

import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

# FaceMesh 关键点索引：左右眼角、鼻尖
_LEFT_EYE, _RIGHT_EYE, _NOSE_TIP = 33, 263, 1


class FaceAligner:
    """延迟初始化 MediaPipe 模型（首次使用时加载，约 1-2 秒）。"""

    def __init__(self, target_size: tuple[int, int], eye_y_ratio: float):
        self.target_size = target_size
        self.eye_y_ratio = eye_y_ratio
        self._face_mesh = None

    def _ensure_model(self) -> None:
        if self._face_mesh is None:
            logger.info("初始化 MediaPipe FaceMesh 模型...")
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )

    def close(self) -> None:
        if self._face_mesh is not None:
            self._face_mesh.close()
            self._face_mesh = None

    def detect_landmarks(self, image: np.ndarray) -> dict | None:
        """检测人脸关键点，返回像素坐标；未检测到返回 None。"""
        self._ensure_model()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None

        h, w, _ = image.shape
        pts = [
            (int(lm.x * w), int(lm.y * h))
            for lm in results.multi_face_landmarks[0].landmark
        ]
        return {
            "left_eye": pts[_LEFT_EYE],
            "right_eye": pts[_RIGHT_EYE],
            "nose_tip": pts[_NOSE_TIP],
            "all_landmarks": pts,
        }

    def align(self, image: np.ndarray, landmarks: dict) -> np.ndarray:
        """以双眼中心为锚点旋转平移图像到目标位置，空白处填充黑色。"""
        target_w, target_h = self.target_size
        left_eye = np.array(landmarks["left_eye"], dtype=float)
        right_eye = np.array(landmarks["right_eye"], dtype=float)

        eye_center = (left_eye + right_eye) / 2
        eye_vector = right_eye - left_eye
        angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))

        matrix = cv2.getRotationMatrix2D(tuple(eye_center), angle, 1.0)
        matrix[0, 2] += target_w / 2 - eye_center[0]
        matrix[1, 2] += target_h * self.eye_y_ratio - eye_center[1]

        return cv2.warpAffine(
            image, matrix, (target_w, target_h),
            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0),
        )

    def process(self, image: np.ndarray) -> np.ndarray | None:
        """检测 + 对齐一步完成。"""
        landmarks = self.detect_landmarks(image)
        if landmarks is None:
            return None
        return self.align(image, landmarks)
