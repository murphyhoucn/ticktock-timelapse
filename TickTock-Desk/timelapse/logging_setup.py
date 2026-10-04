"""日志配置。

静默运行（pythonw）下没有任何控制台可看，文件日志是唯一的观测手段，
所以哪怕最简单的一次运行也要留下一行记录。
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "timelapse"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _ensure_streams() -> None:
    """pythonw 下 sys.stdout/stderr 是 None，第三方库若 print 会崩，兜底指向空设备。"""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def setup_logging(log_dir: Path, verbose: bool = False) -> logging.Logger:
    """初始化项目 logger：始终写文件，verbose 时同时输出到控制台。"""
    _ensure_streams()

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "timelapse.log"

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    # 进程级单例：重复调用（如 import 后又手动 setup）不叠加 handler
    if logger.handlers:
        return logger

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(file_handler)

    if verbose:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(console)

    return logger
