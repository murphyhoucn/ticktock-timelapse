import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
 


def preprocess_add_timestamp(source_dir, font_size=100, position="top_center",
                              text_color=(255, 255, 255), shadow_color=(0, 0, 0)):
    """
    对齐图像预处理：在固定位置叠加时间戳，输出到 {source_dir}_date 目录。
    支持 YYYY.MM 子目录结构，输出时保留原始目录结构。
 
    Args:
        source_dir (str|Path): 对齐图像根目录（如 NPU-Everyday）
        font_size (int):       时间戳字体大小
        position (str):        位置，可选 bottom_left / bottom_right / top_left / top_right
        text_color (tuple):    文字颜色 RGB
        shadow_color (tuple):  阴影颜色 RGB（用于增强可读性）
 
    Returns:
        Path: 输出目录路径，失败返回 None
    """
    source_dir = Path(source_dir).resolve()
    output_dir = Path(str(source_dir) + "_date")
    output_dir.mkdir(parents=True, exist_ok=True)
 
    # ── 文件名解析：IMG_20260301_103948.jpg → "2026-03-01  10:39" ──────────
    pattern = re.compile(r'IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})')
 
    def parse_timestamp(filename):
        m = pattern.search(filename)
        if not m:
            return None
        year, mon, day, hh, mm, ss = m.groups()
        return f"{year}-{mon}-{day}  {hh}:{mm}"
 
    # ── 字体加载（自动回退）──────────────────────────────────────────────
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
 
    font = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
        print("⚠️  未找到系统字体，使用默认字体（字号固定，可能较小）")
 
    # ── 递归扫描所有图像文件（保留子目录顺序）───────────────────────────
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = sorted([
        f for f in source_dir.rglob("*")
        if f.suffix.lower() in image_extensions
    ])
 
    if not image_files:
        print(f"❌ 目录 {source_dir} 中没有找到图像文件")
        return None
 
    print(f"🖼️  找到 {len(image_files)} 张图像，开始添加时间戳...")
    print(f"📁 输出目录: {output_dir}")
 
    # ── 计算文字位置 ─────────────────────────────────────────────────────
    MARGIN = 50  # 距边缘距离（像素）
 
    def get_text_xy(draw, text, img_w, img_h, pos):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
        if pos == "bottom_left":
            return MARGIN, img_h - th - MARGIN
        elif pos == "bottom_right":
            return img_w - tw - MARGIN, img_h - th - MARGIN
        elif pos == "bottom_center":
            return (img_w - tw) // 2, img_h - th - MARGIN
        elif pos == "top_left":
            return MARGIN, MARGIN
        elif pos == "top_right":
            return img_w - tw - MARGIN, MARGIN
        elif pos == "top_center":
            return (img_w - tw) // 2, MARGIN   # ← 新增
        else:
            return MARGIN, img_h - th - MARGIN
 
    # ── 逐图处理 ─────────────────────────────────────────────────────────
    success_count = 0
    skip_count    = 0
    SHADOW_OFFSET = max(2, font_size // 24)
 
    for idx, img_file in enumerate(image_files):
        # 保持相对路径结构：2023.09/IMG_xxx.jpg
        relative_path = img_file.relative_to(source_dir)
        out_path      = output_dir / relative_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
 
        timestamp = parse_timestamp(img_file.name)
 
        if not timestamp:
            # 文件名不含时间戳，原样复制
            shutil.copy2(img_file, out_path)
            skip_count += 1
            continue
 
        try:
            with Image.open(img_file) as img:
                img   = img.convert("RGB")
                draw  = ImageDraw.Draw(img)
                img_w, img_h = img.size
 
                x, y = get_text_xy(draw, timestamp, img_w, img_h, position)
 
                # 阴影（增强可读性）
                draw.text((x + SHADOW_OFFSET, y + SHADOW_OFFSET),
                          timestamp, fill=shadow_color, font=font)
                # 主文字
                draw.text((x, y), timestamp, fill=text_color, font=font)
 
                img.save(out_path, "JPEG", quality=95, optimize=True)
                success_count += 1
 
        except Exception as e:
            print(f"⚠️  处理失败 {img_file.name}: {e}")
            continue
 
        if (idx + 1) % 100 == 0:
            print(f"   已处理 {idx + 1}/{len(image_files)} 张...")
 
    print(f"✅ 时间戳预处理完成！成功 {success_count} 张，跳过（无时间戳）{skip_count} 张")
    print(f"📁 结果保存至: {output_dir}")
    return output_dir