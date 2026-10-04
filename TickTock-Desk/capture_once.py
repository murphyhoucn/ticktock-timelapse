#!/usr/bin/env python3
"""TimeLapse@Desk 主入口：解锁触发的一次性拍摄。

Windows 任务计划程序通过 pythonw.exe 调用本脚本（完全无窗口）：
每次解锁都会启动，程序先查每日计数，未达上限才真正开摄像头拍照。

手动测试（带控制台输出）：
    python capture_once.py --verbose
强制拍摄（忽略每日计数，不消耗额度）：
    python capture_once.py --force --verbose
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from timelapse import __version__
from timelapse.config import Config
from timelapse.counter import DailyCounter
from timelapse.logging_setup import setup_logging
from timelapse.pipeline import run_once


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TimeLapse@Desk 解锁自动拍照（受每日次数限制）")
    parser.add_argument("--camera", type=int, default=None, help="摄像头索引 (默认 0)")
    parser.add_argument("--photos", type=Path, default=None, help="原始照片目录")
    parser.add_argument("--aligned", type=Path, default=None, help="对齐照片目录")
    parser.add_argument("--limit", type=int, default=None,
                        help="每日拍摄上限 (默认 3)")
    parser.add_argument("--state", type=Path, default=None,
                        help="计数状态文件 (默认 unlock_count.txt)")
    parser.add_argument("--force", action="store_true",
                        help="跳过每日计数直接拍摄，也不写入计数")
    parser.add_argument("--verbose", action="store_true", help="同时输出到控制台")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    config = Config()
    overrides = {}
    if args.camera is not None:
        overrides["camera_index"] = args.camera
    if args.photos is not None:
        overrides["photo_dir"] = args.photos
    if args.aligned is not None:
        overrides["aligned_dir"] = args.aligned
    if args.limit is not None:
        overrides["daily_limit"] = args.limit
    if args.state is not None:
        overrides["state_file"] = args.state
    if overrides:
        config = dataclasses.replace(config, **overrides)

    logger = setup_logging(config.log_dir, verbose=args.verbose)
    logger.info("=== TimeLapse@Desk v%s 解锁触发 ===", __version__)

    if not args.force:
        counter = DailyCounter(config.state_file, config.daily_limit)
        if not counter.allow_run():
            return 0  # 达到每日上限属正常情况，任务计划程序不应记为失败
    else:
        logger.info("--force 模式：跳过计数，不计入当日额度")

    success = run_once(config)
    if success and not args.force:
        DailyCounter(config.state_file, config.daily_limit).record_success()

    if not success:
        logger.error("本次拍摄失败（额度未消耗）")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
