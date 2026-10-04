"""每日解锁计数器。

任务计划程序在每次解锁时都会触发本程序，由这里判断今天是否还需要拍照。
状态文件格式（首行）：`YYYY-MM-DD N`，N 为当天已成功拍摄的次数；
日期不是当天时自动清零。文件缺失或损坏视为 0。

语义：**拍摄成功才计数**。摄像头被占用等原因导致失败时不消耗当日额度，
避免一天下来一张照片都没有。
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


class DailyCounter:
    def __init__(self, path: Path, limit: int):
        self.path = path
        self.limit = limit

    def _load(self) -> tuple[str, int]:
        """返回 (日期字符串, 已用次数)；任何异常都归零。"""
        try:
            first_line = self.path.read_text(encoding="utf-8").strip().splitlines()[0]
            day, count = first_line.split()
            int(count)
            return day, int(count)
        except (OSError, ValueError, IndexError):
            return "", 0

    def _store(self, day: str, count: int) -> None:
        """先写临时文件再原子替换，避免写一半留下坏文件。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".unlock_count_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"{day} {count}\n")
            os.replace(tmp_name, self.path)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def used_today(self) -> int:
        day, count = self._load()
        return count if day == date.today().isoformat() else 0

    def allow_run(self) -> bool:
        used = self.used_today()
        allowed = used < self.limit
        if not allowed:
            logger.info("今日已拍摄 %d/%d 张，跳过本次解锁", used, self.limit)
        else:
            logger.info("今日已拍摄 %d/%d 张，本次执行", used, self.limit)
        return allowed

    def record_success(self) -> None:
        used = self.used_today() + 1
        self._store(date.today().isoformat(), used)
        logger.info("计数写入 %s: %d/%d", self.path.name, used, self.limit)
