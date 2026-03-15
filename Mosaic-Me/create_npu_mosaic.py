#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
NPU-Everyday 图片拼接脚本
基于 mosaic-library.py 的 MosaicGenerator 类
处理 D:\DevProj\TickTock-NPUEveryday\NPU-Everyday 下 2025 年的图片
"""
import os
import sys
from pathlib import Path

# 导入 mosaic-library 中的 MosaicGenerator 类
try:
    # 方式1: 如果在同一目录
    from mosaic_library import MosaicGenerator
except ImportError:
    # 方式2: 手动添加路径
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    # 重命名导入（因为文件名包含连字符）
    import importlib.util
    spec = importlib.util.spec_from_file_location("mosaic_library", current_dir / "mosaic-library.py")
    mosaic_library = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mosaic_library)
    MosaicGenerator = mosaic_library.MosaicGenerator

# NPU-Everyday 项目路径配置
NPU_EVERYDAY_BASE = Path(r"D:\DevProj\TickTock-NPUEveryday\NPU-Everyday")

# 2025年的月份文件夹
MONTH_FOLDERS_2025 = [
    "2025.01", "2025.02", "2025.03", "2025.04",
    "2025.05", "2025.06", "2025.07", "2025.08",
    "2025.09", "2025.10", "2025.11", "2025.12"
]

def prepare_images_for_mosaic():
    """
    从2025年的12个月份文件夹中收集图片到临时目录
    或者创建一个自定义的生成器
    """
    import shutil
    import tempfile
    
    # 创建临时目录存放2025年的所有图片
    temp_dir = Path(tempfile.mkdtemp(prefix="npu_2025_"))
    print(f"创建临时目录: {temp_dir}")
    
    total_images = 0
    for month_folder in MONTH_FOLDERS_2025:
        month_path = NPU_EVERYDAY_BASE / month_folder
        
        if not month_path.exists():
            print(f"  ⚠ 文件夹不存在: {month_folder}")
            continue
        
        # 获取该月份的所有图片（Windows下glob不区分大小写，只需匹配一次）
        month_images = list(month_path.glob("*.jpg")) + list(month_path.glob("*.jpeg"))
        
        print(f"  {month_folder}: 找到 {len(month_images)} 张图片")
        
        # 复制图片到临时目录（保留原文件名）
        for img in month_images:
            dest = temp_dir / img.name
            # 如果文件名冲突，添加前缀
            if dest.exists():
                dest = temp_dir / f"{month_folder}_{img.name}"
            shutil.copy2(img, dest)
            total_images += 1
    
    print(f"\n总共收集 {total_images} 张图片")
    return temp_dir, total_images

def main():
    """主函数"""
    print("="*70)
    print("NPU-Everyday 2025年图片马赛克生成器")
    print("="*70)
    print(f"源目录: {NPU_EVERYDAY_BASE}")
    print(f"处理月份: 2025.01 ~ 2025.12 (共12个月)\n")
    
    # 准备图片
    temp_dir, total_images = prepare_images_for_mosaic()
    
    if total_images == 0:
        print("❌ 没有找到图片，程序退出")
        return
    
    # 设置输出目录（在当前工程下）
    output_dir = Path(__file__).parent / "NPU_Mosaic_Output"
    
    # 创建马赛克生成器（带白边）
    # target_width: 目标输出宽度（像素）- 降低以减小文件大小
    # max_output_size: 最大输出尺寸限制（像素）
    # white_border: 白边宽度（像素）
    print(f"\n初始化马赛克生成器...")
    generator = MosaicGenerator(
        input_dir=str(temp_dir),
        output_dir=str(output_dir),
        target_width=6144,       # 降低分辨率（原12288）
        max_output_size=16384,   # 降低最大尺寸（原32768）
        white_border=20          # 白边宽度20像素（原30）
    )
    
    # 生成马赛克（16:9竖向布局）
    print("\n开始生成马赛克拼图（16:9竖向布局）...\n")
    
    # 直接调用底层方法生成单个16:9布局的马赛克
    image_files = generator.get_image_files()
    
    # 计算16:9竖向布局（高:宽 = 16:9）
    rows, cols, cell_width, cell_height = generator.calculate_grid_layout(
        len(image_files), 
        aspect_ratio=16/9  # 竖向16:9
    )
    
    # 确保最后一行必须填满，否则舍弃最后一行
    total_images = len(image_files)
    full_rows_needed = total_images // cols  # 能完整填满的行数
    incomplete_last_row = total_images % cols  # 最后一行的图片数
    
    if incomplete_last_row > 0:
        # 最后一行不满，舍弃最后一行
        rows = full_rows_needed
        images_needed = rows * cols
        print(f"📝 最后一行仅有 {incomplete_last_row} 张图片（需要 {cols} 张），舍弃最后一行")
        print(f"📝 最终使用: {rows}行 × {cols}列 = {images_needed} 张图片（舍弃 {total_images - images_needed} 张）\n")
    else:
        # 最后一行恰好填满
        images_needed = rows * cols
        print(f"✓ 所有行都已填满: {rows}行 × {cols}列 = {images_needed} 张图片\n")
    
    image_files_to_use = image_files[:images_needed]
    
    # 生成马赛克
    grid_mosaic = generator.create_mosaic_grid(image_files_to_use, rows, cols, cell_width, cell_height)
    
    # 保存结果
    from datetime import datetime
    grid_output = output_dir / f"mosaic_16x9_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    grid_mosaic.save(grid_output, "JPEG", quality=85, optimize=True)  # 降低质量到85%以减小文件
    
    success = True
    
    # 清理临时目录
    print(f"\n清理临时目录: {temp_dir}")
    import shutil
    shutil.rmtree(temp_dir)
    
    # 输出结果
    print("\n" + "="*70)
    if success:
        print("✅ 马赛克生成完成！")
        print(f"输出文件: {grid_output}")
        
        # 计算文件大小
        file_size_mb = os.path.getsize(grid_output) / (1024 * 1024)
        print(f"文件大小: {file_size_mb:.2f} MB")
        print(f"布局: {rows}行 × {cols}列 = {rows * cols} 张图片")
        print(f"实际高宽比: {rows/cols:.2f}:1 (目标16:9 ≈ 1.78:1)")
    else:
        print("❌ 马赛克生成失败！")
        sys.exit(1)
    print("="*70)

if __name__ == "__main__":
    main()
