#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
马赛克拼图生成器

将对齐后的图像进行马赛克拼接，生成一张大图。
考虑到内存限制和输出分辨率，会对图像进行智能缩放处理。

功能特点：
- 智能网格布局计算
- 自适应图像缩放
- 内存优化处理
- 支持多种输出分辨率
- 日历马赛克（亮色/深色双主题）
"""

import os
import sys
import math
import re
import calendar
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
import logging
from datetime import datetime, date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MosaicGenerator:
    """马赛克拼图生成器"""

    def __init__(self, input_dir, output_dir, target_width=16384, max_output_size=32768):
        """
        初始化马赛克生成器

        Args:
            input_dir (str): 输入图像目录（通常是Aligned目录）
            output_dir (str): 输出目录
            target_width (int): 目标输出宽度（像素）
            max_output_size (int): 最大输出尺寸限制（像素）
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.target_width = target_width
        self.max_output_size = max_output_size

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"马赛克生成器初始化完成")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"目标输出宽度: {self.target_width}px")

    def get_image_files(self):
        """获取所有图像文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []

        for ext in image_extensions:
            image_files.extend(list(self.input_dir.rglob(f"*{ext}")))
            image_files.extend(list(self.input_dir.rglob(f"*{ext.upper()}")))

        # 去重并按时间顺序排序（先按文件夹，再按文件名）
        image_files = sorted(list(set(image_files)), key=lambda x: (str(x.parent), x.name))
        return image_files

    def calculate_grid_layout(self, image_count):
        """
        计算最优网格布局

        Args:
            image_count (int): 图像数量

        Returns:
            tuple: (rows, cols, cell_width, cell_height) 行数、列数、单元格宽度、单元格高度
        """
        # 计算接近正方形的网格
        cols = math.ceil(math.sqrt(image_count))
        rows = math.ceil(image_count / cols)

        # 计算单元格大小（保持4:3比例）
        cell_width = self.target_width // cols
        cell_height = int(cell_width * 3 / 4)  # 4:3比例

        # 检查输出尺寸是否超过限制
        output_height = rows * cell_height
        if output_height > self.max_output_size:
            # 重新计算以适应最大尺寸限制
            max_rows = self.max_output_size // cell_height
            if max_rows < rows:
                cell_height = self.max_output_size // rows
                cell_width = int(cell_height * 4 / 3)  # 保持4:3比例
                cols = self.target_width // cell_width
                rows = math.ceil(image_count / cols)

        logger.info(f"网格布局: {rows}行 × {cols}列")
        logger.info(f"单元格大小: {cell_width}×{cell_height} 像素 (4:3比例)")
        logger.info(f"输出尺寸: {cols * cell_width}×{rows * cell_height} 像素")

        return rows, cols, cell_width, cell_height

    def resize_image_fit(self, image, target_width, target_height):
        """
        智能缩放图像，保持宽高比并适配到目标尺寸（不裁切）

        Args:
            image (PIL.Image): 输入图像
            target_width (int): 目标宽度
            target_height (int): 目标高度

        Returns:
            PIL.Image: 缩放后的图像
        """
        # 计算缩放比例（确保图像完全适配在目标区域内）
        img_width, img_height = image.size
        scale_w = target_width / img_width
        scale_h = target_height / img_height
        scale = min(scale_w, scale_h)  # 使用较小的缩放比例确保不裁切

        # 缩放图像
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 创建目标大小的画布，居中放置图像
        canvas = Image.new('RGB', (target_width, target_height), (240, 240, 240))
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(resized, (x_offset, y_offset))

        return canvas

    def create_mosaic_grid(self, image_files, rows, cols, cell_width, cell_height):
        """
        创建网格马赛克

        Args:
            image_files (list): 图像文件列表
            rows (int): 行数
            cols (int): 列数
            cell_width (int): 单元格宽度
            cell_height (int): 单元格高度

        Returns:
            PIL.Image: 马赛克图像
        """
        # 创建空白画布
        output_width = cols * cell_width
        output_height = rows * cell_height
        mosaic = Image.new('RGB', (output_width, output_height), (255, 255, 255))

        logger.info(f"开始生成马赛克，画布尺寸: {output_width}×{output_height}")

        # 逐个处理图像
        for idx, img_file in enumerate(image_files):
            if idx >= rows * cols:
                break

            row = idx // cols
            col = idx % cols

            try:
                # 读取并缩放图像
                with Image.open(img_file) as img:
                    resized_img = self.resize_image_fit(img, cell_width, cell_height)

                    # 计算粘贴位置
                    x = col * cell_width
                    y = row * cell_height

                    # 粘贴到画布
                    mosaic.paste(resized_img, (x, y))

                    if (idx + 1) % 50 == 0:
                        logger.info(f"已处理 {idx + 1}/{len(image_files)} 张图像")

            except Exception as e:
                logger.warning(f"处理图像 {img_file.name} 失败: {e}")
                continue

        return mosaic

    def create_timeline_mosaic(self, image_files, cell_width=128):
        """
        创建时间线马赛克（按时间顺序排列）

        Args:
            image_files (list): 图像文件列表
            cell_width (int): 单元格宽度

        Returns:
            PIL.Image: 时间线马赛克图像
        """
        # 计算4:3比例的单元格尺寸
        cell_height = int(cell_width * 3 / 4)

        # 计算布局：时间线风格，固定列数
        cols = self.target_width // cell_width
        rows = math.ceil(len(image_files) / cols)

        output_width = cols * cell_width
        output_height = rows * cell_height

        logger.info(f"时间线马赛克布局: {rows}行 × {cols}列")
        logger.info(f"输出尺寸: {output_width}×{output_height}")

        # 创建画布
        mosaic = Image.new('RGB', (output_width, output_height), (240, 240, 240))

        # 添加时间标注
        try:
            font = ImageFont.truetype("arial.ttf", cell_width // 8)
        except:
            font = ImageFont.load_default()

        draw = ImageDraw.Draw(mosaic)

        # 逐个处理图像
        for idx, img_file in enumerate(image_files):
            row = idx // cols
            col = idx % cols

            try:
                with Image.open(img_file) as img:
                    resized_img = self.resize_image_fit(img, cell_width - 2, cell_height - 2)  # 留2px边距

                    # 计算位置
                    x = col * cell_width + 1
                    y = row * cell_height + 1

                    # 粘贴图像
                    mosaic.paste(resized_img, (x, y))

                    # 添加文件名标注（可选）
                    if cell_width >= 64:  # 只在较大尺寸时添加文字
                        text = img_file.stem[4:12]  # 只显示文件名的第5到第12个字符
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_x = x + (cell_width - 4 - text_width) // 2
                        text_y = y + cell_height - 16

                        # 添加文字
                        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

                    if (idx + 1) % 50 == 0:
                        logger.info(f"已处理 {idx + 1}/{len(image_files)} 张图像")

            except Exception as e:
                logger.warning(f"处理图像 {img_file.name} 失败: {e}")
                continue

        return mosaic

    def generate_mosaics(self):
        """生成多种风格的马赛克拼图"""
        # 获取图像文件
        image_files = self.get_image_files()

        if not image_files:
            logger.error("没有找到图像文件")
            return False

        logger.info(f"找到 {len(image_files)} 个图像文件")

        try:
            # 1. 生成网格马赛克
            logger.info("生成网格马赛克...")
            rows, cols, cell_width, cell_height = self.calculate_grid_layout(len(image_files))
            grid_mosaic = self.create_mosaic_grid(image_files, rows, cols, cell_width, cell_height)

            grid_output = self.output_dir / "mosaic_grid.jpg"
            grid_mosaic.save(grid_output, "JPEG", quality=90, optimize=True)
            logger.info(f"网格马赛克已保存: {grid_output}")

            # 2. 生成时间线马赛克（小尺寸）
            logger.info("生成时间线马赛克（小尺寸）...")
            timeline_small = self.create_timeline_mosaic(image_files, cell_width=64)
            timeline_small_output = self.output_dir / "mosaic_timeline_small.jpg"
            timeline_small.save(timeline_small_output, "JPEG", quality=90, optimize=True)
            logger.info(f"小尺寸时间线马赛克已保存: {timeline_small_output}")

            # 3. 生成时间线马赛克（中等尺寸）
            if len(image_files) <= 1000:  # 只在图像数量较少时生成大尺寸
                logger.info("生成时间线马赛克（中等尺寸）...")
                timeline_medium = self.create_timeline_mosaic(image_files, cell_width=128)
                timeline_medium_output = self.output_dir / "mosaic_timeline_medium.jpg"
                timeline_medium.save(timeline_medium_output, "JPEG", quality=90, optimize=True)
                logger.info(f"中等尺寸时间线马赛克已保存: {timeline_medium_output}")

            # 4. 生成缩略图概览
            logger.info("生成缩略图概览...")
            thumbnail_mosaic = self.create_timeline_mosaic(image_files, cell_width=32)
            thumbnail_output = self.output_dir / "mosaic_thumbnail.jpg"
            thumbnail_mosaic.save(thumbnail_output, "JPEG", quality=85, optimize=True)
            logger.info(f"缩略图概览已保存: {thumbnail_output}")

            # 5. 生成日历马赛克（亮色 + 深色双主题）
            logger.info("生成日历马赛克...")
            self.generate_calendar_mosaic(image_files)

            # 生成信息报告
            self.generate_info_report(image_files, rows, cols, cell_width, cell_height)

            return True

        except Exception as e:
            logger.error(f"生成马赛克失败: {e}")
            return False

    def generate_calendar_mosaic(self, image_files):
        """
        按日历形式生成马赛克，每年 × 每主题 各一张。
        - 周一开始，周日结束
        - 每天取最后一张图（时间戳最大）
        - 无图的日期保持空白
        - 同时生成亮色主题和深色主题
        """

        # ── 1. 从文件名解析日期，每天只保留最后一张 ──────────────────────────
        pattern = re.compile(r'IMG_(\d{4})(\d{2})(\d{2})_(\d{6})')
        date_to_file = {}  # date → Path（取时间戳最大的）

        for f in image_files:
            m = pattern.search(f.name)
            if not m:
                continue
            try:
                y, mo, d, t = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                key = date(y, mo, d)
                # 同一天多张：保留时间戳更大的
                if key not in date_to_file or t < pattern.search(date_to_file[key].name).group(4):
                    date_to_file[key] = f
            except ValueError:
                continue

        if not date_to_file:
            logger.error("没有解析到任何有效日期的图像")
            return False

        # ── 2. 确定各年的起止日期 ────────────────────────────────────────────
        year_ranges = {
            2023: (date(2023, 9,  1),  date(2023, 12, 31)),
            2024: (date(2024, 1,  1),  date(2024, 12, 31)),
            2025: (date(2025, 1,  1),  date(2025, 12, 31)),
            2026: (date(2026, 1,  1),  date(2026,  3, 31)),
        }

        # ── 3. 双主题定义 ─────────────────────────────────────────────────────
        THEMES = {
            "light": {
                "BG_COLOR":      (245, 245, 245),
                "BORDER_COLOR":  (200, 200, 200),
                "EMPTY_COLOR":   (225, 225, 225),
                "TEXT_COLOR":    (80,  80,  80 ),
                "TITLE_COLOR":   (30,  30,  30 ),
                "MONTH_COLOR":   (40,  40,  40 ),
                "WEEKDAY_COLOR": (90,  90,  90 ),
                "SUNDAY_COLOR":  (180, 50,  50 ),
            },
            "dark": {
                "BG_COLOR":      (20,  20,  20 ),
                "BORDER_COLOR":  (60,  60,  60 ),
                "EMPTY_COLOR":   (35,  35,  35 ),
                "TEXT_COLOR":    (200, 200, 200),
                "TITLE_COLOR":   (240, 240, 240),
                "MONTH_COLOR":   (230, 230, 230),
                "WEEKDAY_COLOR": (160, 160, 160),
                "SUNDAY_COLOR":  (180, 100, 100),
            },
        }

        # ── 4. 布局参数 ───────────────────────────────────────────────────────
        COLS        = 7    # 周一到周日
        CELL_W      = 320  # 单元格宽（原图 4:3）
        CELL_H      = 240  # 单元格高
        GAP         = 4    # 单元格间距
        BORDER      = 1    # 边框宽度
        TITLE_H     = 140  # 顶部年份标题行高
        HEADER_H    = 140  # 月份标题行高
        WEEKDAY_H   = 50   # 星期标题行高
        DAY_LABEL_H = 28   # 每格顶部日期数字高度

        WEEKDAYS_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        MONTHS_EN   = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        # ── 5. 加载字体 ───────────────────────────────────────────────────────
        font_paths_bold   = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        font_paths_regular = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

        def load_font(paths, size):
            for p in paths:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
            return ImageFont.load_default()

        font_title  = load_font(font_paths_bold,    80)
        font_large  = load_font(font_paths_bold,    66)
        font_medium = load_font(font_paths_bold,    28)
        font_small  = load_font(font_paths_regular, 22)

        # ── 6. 辅助函数 ───────────────────────────────────────────────────────
        def weeks_in_month(yr, mo):
            """该月在日历里占几行（周一起始）"""
            first_weekday = date(yr, mo, 1).weekday()  # 0=Mon
            days_in_month = calendar.monthrange(yr, mo)[1]
            return math.ceil((first_weekday + days_in_month) / 7)

        # ── 7. 逐年 × 逐主题 生成 ────────────────────────────────────────────
        for year, (start_date, end_date) in year_ranges.items():
            all_months = list(range(start_date.month, end_date.month + 1))

            # 计算画布宽高（与主题无关）
            row_width = COLS * (CELL_W + GAP) + GAP

            total_h = GAP + TITLE_H
            for month in all_months:
                weeks = weeks_in_month(year, month)
                total_h += HEADER_H + WEEKDAY_H + weeks * (CELL_H + GAP) + GAP * 2

            for theme_name, theme in THEMES.items():
                logger.info(f"生成 {year} 年日历马赛克（{theme_name}）...")

                BG_COLOR     = theme["BG_COLOR"]
                BORDER_COLOR = theme["BORDER_COLOR"]
                EMPTY_COLOR  = theme["EMPTY_COLOR"]
                TEXT_COLOR   = theme["TEXT_COLOR"]

                canvas = Image.new('RGB', (row_width, total_h), BG_COLOR)
                draw   = ImageDraw.Draw(canvas)

                # ── 顶部年份总标题 ────────────────────────────────────────
                title_str = f"NPU Everyday @ {year}"
                bbox = draw.textbbox((0, 0), title_str, font=font_title)
                tx = (row_width - (bbox[2] - bbox[0])) // 2
                ty = (TITLE_H  - (bbox[3] - bbox[1])) // 2
                draw.text((tx, ty), title_str, fill=theme["TITLE_COLOR"], font=font_title)

                current_y = TITLE_H + GAP

                # ── 逐月绘制 ──────────────────────────────────────────────
                for month in all_months:
                    days_in_month = calendar.monthrange(year, month)[1]
                    first_weekday = date(year, month, 1).weekday()  # 0=Mon, 6=Sun
                    weeks         = weeks_in_month(year, month)

                    # 月份标题（只写月份名，不写年份）
                    month_label = MONTHS_EN[month - 1]
                    bbox = draw.textbbox((0, 0), month_label, font=font_large)
                    tx = (row_width - (bbox[2] - bbox[0])) // 2
                    ty = current_y + (HEADER_H - (bbox[3] - bbox[1])) // 2
                    draw.text((tx, ty), month_label, fill=theme["MONTH_COLOR"], font=font_large)
                    current_y += HEADER_H

                    # 星期标题行 Mon ~ Sun
                    for col_idx, wd in enumerate(WEEKDAYS_EN):
                        x     = GAP + col_idx * (CELL_W + GAP)
                        color = theme["SUNDAY_COLOR"] if col_idx == 6 else theme["WEEKDAY_COLOR"]
                        bbox  = draw.textbbox((0, 0), wd, font=font_medium)
                        tx    = x + (CELL_W - (bbox[2] - bbox[0])) // 2
                        ty    = current_y + (WEEKDAY_H - (bbox[3] - bbox[1])) // 2
                        draw.text((tx, ty), wd, fill=color, font=font_medium)
                    current_y += WEEKDAY_H

                    # 日期格子
                    for day in range(1, days_in_month + 1):
                        d       = date(year, month, day)
                        slot    = first_weekday + day - 1
                        row_idx = slot // 7
                        col_idx = slot % 7

                        x = GAP + col_idx * (CELL_W + GAP)
                        y = current_y + row_idx * (CELL_H + GAP)

                        img_path = date_to_file.get(d)

                        if img_path:
                            # 有图：贴图
                            try:
                                with Image.open(img_path) as img:
                                    inner_w = CELL_W - BORDER * 2
                                    inner_h = CELL_H - BORDER * 2 - DAY_LABEL_H
                                    resized = self.resize_image_fit(img, inner_w, inner_h)
                                    canvas.paste(resized, (x + BORDER, y + BORDER + DAY_LABEL_H))
                            except Exception as e:
                                logger.warning(f"贴图失败 {img_path.name}: {e}")
                                draw.rectangle([x, y, x + CELL_W, y + CELL_H], fill=EMPTY_COLOR)
                        else:
                            # 无图：空白格
                            draw.rectangle([x, y, x + CELL_W, y + CELL_H], fill=EMPTY_COLOR)

                        # 边框
                        if BORDER > 0:
                            draw.rectangle(
                                [x, y, x + CELL_W - 1, y + CELL_H - 1],
                                outline=BORDER_COLOR, width=BORDER
                            )

                        # 日期数字（左上角）
                        is_sunday = (col_idx == 6)
                        day_color = theme["SUNDAY_COLOR"] if is_sunday else TEXT_COLOR
                        draw.text((x + 8, y + 5), str(day), fill=day_color, font=font_small)

                    current_y += weeks * (CELL_H + GAP) + GAP * 2

                # ── 保存 ──────────────────────────────────────────────────
                out_path = self.output_dir / f"calendar_mosaic_{year}_{theme_name}.jpg"
                canvas.save(out_path, "JPEG", quality=92, optimize=True)
                logger.info(
                    f"{year} 年日历马赛克（{theme_name}）已保存: {out_path} "
                    f"({canvas.width}×{canvas.height}px)"
                )

        return True

    def generate_info_report(self, image_files, rows, cols, cell_width, cell_height):
        """生成马赛克信息报告"""
        report_path = self.output_dir / "mosaic_info.md"

        # 统计信息
        total_images = len(image_files)
        used_images  = min(total_images, rows * cols)

        # 计算文件大小
        def get_file_size(filepath):
            try:
                size = os.path.getsize(filepath)
                if size > 1024 * 1024:
                    return f"{size / (1024 * 1024):.1f} MB"
                else:
                    return f"{size / 1024:.1f} KB"
            except Exception:
                return "未知"

        report_content = f"""# 马赛克拼图生成报告

## 基本信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **输入目录**: {self.input_dir}
- **输出目录**: {self.output_dir}
- **总图像数**: {total_images}
- **使用图像数**: {used_images}

## 生成的马赛克文件

### 1. 网格马赛克 (mosaic_grid.jpg)
- **布局**: {rows}行 × {cols}列
- **单元格大小**: {cell_width}×{cell_height} 像素 (4:3比例)
- **输出尺寸**: {cols * cell_width}×{rows * cell_height} 像素
- **文件大小**: {get_file_size(self.output_dir / "mosaic_grid.jpg")}

### 2. 时间线马赛克 - 小尺寸 (mosaic_timeline_small.jpg)
- **单元格大小**: 64×48 像素
- **特点**: 适合快速预览，文件较小
- **文件大小**: {get_file_size(self.output_dir / "mosaic_timeline_small.jpg")}

### 3. 时间线马赛克 - 中等尺寸 (mosaic_timeline_medium.jpg)
- **单元格大小**: 128×96 像素
- **特点**: 平衡质量和文件大小
- **文件大小**: {get_file_size(self.output_dir / "mosaic_timeline_medium.jpg") if (self.output_dir / "mosaic_timeline_medium.jpg").exists() else "未生成"}

### 4. 缩略图概览 (mosaic_thumbnail.jpg)
- **单元格大小**: 32×24 像素
- **特点**: 超小尺寸，适合网页显示
- **文件大小**: {get_file_size(self.output_dir / "mosaic_thumbnail.jpg")}

### 5. 日历马赛克
- **格式**: 每年独立一张，亮色 + 深色各一张，共 8 张
- **命名**: calendar_mosaic_YYYY_light.jpg / calendar_mosaic_YYYY_dark.jpg
- **布局**: 7列（Mon~Sun），每格 320×240 像素（4:3）
- **范围**: 2023年9-12月 / 2024年全年 / 2025年全年 / 2026年1-3月

## 使用建议

- **网格马赛克**: 适合打印和高质量展示
- **时间线马赛克**: 适合查看图像的时间顺序
- **缩略图概览**: 适合快速浏览和网页展示
- **日历马赛克**: 适合按日期回顾，亮色版适合打印，深色版适合屏幕展示

## 技术参数

- **目标输出宽度**: {self.target_width} 像素
- **最大输出尺寸**: {self.max_output_size} 像素
- **图像缩放算法**: LANCZOS（高质量重采样）
- **输出格式**: JPEG
- **压缩质量**: 85-92%

---
*由 TickTock-Align-NPU Library 马赛克生成器创建*
"""

        report_path.write_text(report_content, encoding='utf-8')
        logger.info(f"马赛克信息报告已保存: {report_path}")


def main():
    """主函数 - 用于独立运行"""
    import argparse

    parser = argparse.ArgumentParser(description='马赛克拼图生成器')
    parser.add_argument('input_dir',  help='输入图像目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--width',    type=int, default=16384, help='目标输出宽度（默认16384）')
    parser.add_argument('--max-size', type=int, default=32768, help='最大输出尺寸（默认32768）')

    args = parser.parse_args()

    generator = MosaicGenerator(args.input_dir, args.output_dir, args.width, args.max_size)
    success   = generator.generate_mosaics()

    if success:
        print("✅ 马赛克生成完成！")
    else:
        print("❌ 马赛克生成失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()