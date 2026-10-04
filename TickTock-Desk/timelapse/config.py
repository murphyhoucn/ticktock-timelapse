"""集中配置：目录、摄像头参数、水印、每日解锁上限。

所有默认路径都基于项目根目录定位，不依赖进程工作目录，
因此任务计划程序即使没有正确设置"起始于"也能正常工作。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_STATE_FILE = PROJECT_ROOT / "unlock_count.txt"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_PHOTO_DIR = PROJECT_ROOT / "photos"
DEFAULT_ALIGNED_DIR = PROJECT_ROOT / "aligned_photos"


@dataclass(frozen=True)
class Config:
    """一次拍摄流程所需的全部参数。"""

    # 输出目录
    photo_dir: Path = DEFAULT_PHOTO_DIR
    aligned_dir: Path = DEFAULT_ALIGNED_DIR
    log_dir: Path = DEFAULT_LOG_DIR
    state_file: Path = DEFAULT_STATE_FILE

    # 每日解锁触发上限：每天最多成功拍摄 N 张（第 N+1 次起静默退出）
    daily_limit: int = 3

    # 摄像头
    camera_index: int = 0
    frame_width: int = 1920
    frame_height: int = 1080
    fps: int = 30
    buffersize: int = 1
    brightness: int = 128
    contrast: int = 140
    saturation: int = 145
    sharpness: int = 140
    warmup_frames: int = 10   # 开机预热帧数，让自动曝光/对焦收敛
    settle_seconds: float = 1.0  # 预热后额外稳定时间

    # 人脸对齐：眼睛中心对齐到目标画幅的 (0.5 * width, 0.4 * height)
    target_size: tuple[int, int] = (1920, 1080)
    eye_y_ratio: float = 0.4

    # 水印（右下角两行：版权 / 时间+地点）
    watermark_copyright: str = "Copyright Murphy"
    watermark_location: str = "Qingdao"
    watermark_alpha: float = 0.7
