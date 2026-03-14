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
"""

import os
import sys
import math
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
import logging
from datetime import datetime

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
                        
                        # 添加文字背景
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
            
            # 生成信息报告
            self.generate_info_report(image_files, rows, cols, cell_width, cell_height)
            
            return True
            
        except Exception as e:
            logger.error(f"生成马赛克失败: {e}")
            return False
    
    def generate_info_report(self, image_files, rows, cols, cell_width, cell_height):
        """生成马赛克信息报告"""
        report_path = self.output_dir / "mosaic_info.md"
        
        # 统计信息
        total_images = len(image_files)
        used_images = min(total_images, rows * cols)
        
        # 计算文件大小
        def get_file_size(filepath):
            try:
                size = os.path.getsize(filepath)
                if size > 1024 * 1024:
                    return f"{size / (1024 * 1024):.1f} MB"
                else:
                    return f"{size / 1024:.1f} KB"
            except:
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
- **单元格大小**: 64×64 像素
- **特点**: 适合快速预览，文件较小
- **文件大小**: {get_file_size(self.output_dir / "mosaic_timeline_small.jpg")}

### 3. 时间线马赛克 - 中等尺寸 (mosaic_timeline_medium.jpg)
- **单元格大小**: 128×128 像素
- **特点**: 平衡质量和文件大小
- **文件大小**: {get_file_size(self.output_dir / "mosaic_timeline_medium.jpg") if (self.output_dir / "mosaic_timeline_medium.jpg").exists() else "未生成"}

### 4. 缩略图概览 (mosaic_thumbnail.jpg)
- **单元格大小**: 32×32 像素
- **特点**: 超小尺寸，适合网页显示
- **文件大小**: {get_file_size(self.output_dir / "mosaic_thumbnail.jpg")}

## 使用建议

- **网格马赛克**: 适合打印和高质量展示
- **时间线马赛克**: 适合查看图像的时间顺序
- **缩略图概览**: 适合快速浏览和网页展示

## 技术参数

- **目标输出宽度**: {self.target_width} 像素
- **最大输出尺寸**: {self.max_output_size} 像素
- **图像缩放算法**: LANCZOS（高质量重采样）
- **输出格式**: JPEG
- **压缩质量**: 85-90%

---
*由 TickTock-Align-NPU Library 马赛克生成器创建*
"""
        
        report_path.write_text(report_content, encoding='utf-8')
        logger.info(f"马赛克信息报告已保存: {report_path}")

def main():
    """主函数 - 用于独立运行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='马赛克拼图生成器')
    parser.add_argument('input_dir', help='输入图像目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--width', type=int, default=16384, help='目标输出宽度（默认16384）')
    parser.add_argument('--max-size', type=int, default=32768, help='最大输出尺寸（默认32768）')
    
    args = parser.parse_args()
    
    # 创建生成器并执行
    generator = MosaicGenerator(args.input_dir, args.output_dir, args.width, args.max_size)
    success = generator.generate_mosaics()
    
    if success:
        print("✅ 马赛克生成完成！")
    else:
        print("❌ 马赛克生成失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
