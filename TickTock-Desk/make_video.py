#!/usr/bin/env python3
"""用 FFmpeg 把 aligned_photos/ 下的对齐照片合成为延时视频。

默认一次性生成三档（preview 30fps / standard 15fps / hq 10fps），
也可以用 --fps/--crf/--name 只生成一个自定义版本。

    python make_video.py                      # 三档全出
    python make_video.py --fps 12 --crf 20 --name timelapse_12fps.mp4
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PRESETS = [
    ("timelapse_preview.mp4", 30, 23),
    ("timelapse_standard.mp4", 15, 20),
    ("timelapse_hq.mp4", 10, 18),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FFmpeg 延时视频合成")
    parser.add_argument("--source", type=Path, default=None,
                        help="照片目录 (默认 aligned_photos)")
    parser.add_argument("--name", type=str, default=None,
                        help="输出文件名；指定后只生成这一个视频")
    parser.add_argument("--fps", type=int, default=15, help="帧率，越大播放越快")
    parser.add_argument("--crf", type=int, default=20,
                        help="质量 0-51，越小质量越高")
    return parser.parse_args(argv)


def build_video(photo_dir: Path, output: Path, fps: int, crf: int,
                ffmpeg: str) -> bool:
    photos = sorted(photo_dir.glob("*.jpg"))
    if len(photos) < 2:
        print(f"照片数量不足: {photo_dir} 中找到 {len(photos)} 张，至少需要 2 张")
        return False

    # concat 文件列表方式，兼容所有 FFmpeg 版本（不依赖 glob 模式）
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in photos:
            f.write(f"file '{p.resolve().as_posix()}'\n")
        list_path = f.name

    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-r", str(fps),
        "-c:v", "libx264", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        str(output),
    ]
    print(f"生成 {output.name}: {len(photos)} 张照片 @ {fps}fps crf={crf}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=600, errors="replace")
    except subprocess.TimeoutExpired:
        print(f"  失败：FFmpeg 超时（10 分钟）")
        return False
    finally:
        os.unlink(list_path)

    if result.returncode != 0:
        print("  失败，FFmpeg 错误信息（末尾）：")
        print("\n".join(result.stderr.splitlines()[-10:]))
        return False

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"  完成: {output} ({size_mb:.1f} MB)")
    return True


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    photo_dir = args.source or Path(__file__).resolve().parent / "aligned_photos"

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("未找到 ffmpeg，请安装并加入 PATH（https://ffmpeg.org/download.html）")
        return 1
    if not photo_dir.exists():
        print(f"照片目录不存在: {photo_dir}")
        return 1

    if args.name:
        jobs = [(args.name, args.fps, args.crf)]
    else:
        jobs = PRESETS

    ok = 0
    for name, fps, crf in jobs:
        if build_video(photo_dir, Path(name), fps, crf, ffmpeg):
            ok += 1
    print(f"完成：成功生成 {ok}/{len(jobs)} 个视频")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
