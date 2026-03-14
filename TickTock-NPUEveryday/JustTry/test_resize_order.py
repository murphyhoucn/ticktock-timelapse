#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Resize模块的文件处理顺序
"""

import sys
sys.path.append('.')

from pathlib import Path

def test_resize_file_order():
    """测试resize模块的文件读取顺序"""
    
    input_path = Path("NPU-Everyday")
    if not input_path.exists():
        print("❌ NPU-Everyday目录不存在")
        return
    
    # 模拟resize模块的文件收集逻辑
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # 收集所有图片文件
    image_files = []
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    # 按时间顺序排序：先按文件夹，再按文件名（和修复后的代码一致）
    image_files = sorted(image_files, key=lambda x: (str(x.parent), x.name))
    
    print(f"🔍 Resize模块文件处理顺序测试")
    print(f"📋 找到 {len(image_files)} 个图片文件")
    print("📂 前10个文件的处理顺序:")
    
    for i, file_path in enumerate(image_files[:10]):
        rel_path = file_path.relative_to(input_path)
        print(f"   {i+1:2d}. {rel_path}")
    
    if len(image_files) > 10:
        print(f"   ... 还有 {len(image_files)-10} 个文件")
    
    print(f"\n📂 后5个文件:")
    for i, file_path in enumerate(image_files[-5:], len(image_files)-4):
        rel_path = file_path.relative_to(input_path)
        print(f"   {i:2d}. {rel_path}")
    
    print(f"\n✅ 文件顺序验证完成！")
    print(f"🎯 处理顺序：按文件夹名排序 → 按文件名排序")

if __name__ == "__main__":
    test_resize_file_order()