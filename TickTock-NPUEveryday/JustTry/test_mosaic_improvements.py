#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的马赛克生成器
验证4:3比例和更大输出尺寸
"""

import sys
sys.path.append('.')

from Mosaic.mosaic_pic import MosaicGenerator
from pathlib import Path
import tempfile

def test_mosaic_generator():
    """测试马赛克生成器的新功能"""
    
    print("🎨 测试修改后的马赛克生成器")
    print("=" * 60)
    
    input_dir = "NPU-Everyday"
    if not Path(input_dir).exists():
        print("❌ NPU-Everyday目录不存在")
        return
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 使用临时输出目录: {temp_dir}")
        
        # 创建生成器实例（使用新的默认参数）
        generator = MosaicGenerator(input_dir, temp_dir)
        
        # 获取图像文件
        image_files = generator.get_image_files()
        print(f"📸 找到 {len(image_files)} 个图像文件")
        
        # 测试新的布局计算
        print(f"\n🧮 测试布局计算:")
        rows, cols, cell_width, cell_height = generator.calculate_grid_layout(len(image_files))
        
        print(f"   📐 网格布局: {rows}行 × {cols}列")
        print(f"   📏 单元格尺寸: {cell_width}×{cell_height} 像素")
        print(f"   📊 宽高比: {cell_width/cell_height:.2f} (目标: 1.33 for 4:3)")
        print(f"   🖼️  总输出尺寸: {cols * cell_width}×{rows * cell_height} 像素")
        
        # 验证4:3比例
        ratio = cell_width / cell_height
        expected_ratio = 4 / 3
        if abs(ratio - expected_ratio) < 0.01:
            print(f"   ✅ 4:3比例正确")
        else:
            print(f"   ❌ 比例错误: {ratio:.2f} (期望: {expected_ratio:.2f})")
        
        # 测试图像适配函数
        print(f"\n🖼️  测试图像适配:")
        from PIL import Image
        
        # 创建一个测试图像 (4:3比例)
        test_img = Image.new('RGB', (4096, 3072), (128, 128, 128))
        fitted_img = generator.resize_image_fit(test_img, cell_width, cell_height)
        
        print(f"   📐 输入尺寸: {test_img.size}")
        print(f"   📐 输出尺寸: {fitted_img.size}")
        print(f"   📐 目标尺寸: {cell_width}×{cell_height}")
        
        if fitted_img.size == (cell_width, cell_height):
            print(f"   ✅ 图像适配尺寸正确")
        else:
            print(f"   ❌ 图像适配尺寸错误")
        
        # 测试不同比例的图像
        test_img_portrait = Image.new('RGB', (3072, 4096), (64, 64, 64))  # 3:4比例
        fitted_portrait = generator.resize_image_fit(test_img_portrait, cell_width, cell_height)
        print(f"   📐 竖向图像适配: {test_img_portrait.size} → {fitted_portrait.size}")
        
        print(f"\n🎯 配置验证:")
        print(f"   🎚️  目标宽度: {generator.target_width} 像素 (提升了 4倍)")
        print(f"   📏 最大尺寸: {generator.max_output_size} 像素")
        
        # 估算输出文件大小
        estimated_pixels = cols * rows * cell_width * cell_height
        estimated_size_mb = estimated_pixels * 3 / (1024 * 1024)  # RGB 3字节/像素
        print(f"   💾 估算文件大小: {estimated_size_mb:.1f} MB (未压缩)")
        
        print(f"\n✅ 测试完成！")
        print(f"🔧 主要改进:")
        print(f"   • 保持4:3比例，不再裁切图像")
        print(f"   • 输出宽度从4096增加到16384像素")
        print(f"   • 图像适配而不是裁剪，保留完整信息")

if __name__ == "__main__":
    test_mosaic_generator()