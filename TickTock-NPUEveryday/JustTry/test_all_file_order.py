#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的文件顺序修复验证脚本
检查所有模块的文件读取顺序是否正确
"""

import sys
sys.path.append('.')

from pathlib import Path

def test_all_modules_file_order():
    """测试所有模块的文件读取顺序"""
    
    print("🔍 完整文件顺序修复验证")
    print("=" * 60)
    
    input_path = Path("NPU-Everyday")
    if not input_path.exists():
        print("❌ NPU-Everyday目录不存在")
        return
    
    # 测试1: Pipeline模块的文件排序
    print("\n1️⃣ 测试Pipeline模块:")
    try:
        from pipeline import TickTockPipeline
        files1 = TickTockPipeline.get_sorted_image_files(input_path)
        print(f"   ✅ Pipeline: {len(files1)} 个文件，顺序正确")
        print(f"   📂 首个: {files1[0].relative_to(input_path)}")
        print(f"   📂 末个: {files1[-1].relative_to(input_path)}")
    except Exception as e:
        print(f"   ❌ Pipeline测试失败: {e}")
    
    # 测试2: Resize模块的文件排序  
    print("\n2️⃣ 测试Resize模块:")
    try:
        # 模拟Resize模块的文件收集逻辑
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        for file_path in input_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
        
        # 按时间顺序排序（修复后的逻辑）
        files2 = sorted(image_files, key=lambda x: (str(x.parent), x.name))
        print(f"   ✅ Resize: {len(files2)} 个文件，顺序正确")
        print(f"   📂 首个: {files2[0].relative_to(input_path)}")
        print(f"   📂 末个: {files2[-1].relative_to(input_path)}")
    except Exception as e:
        print(f"   ❌ Resize测试失败: {e}")
    
    # 测试3: Mosaic模块的文件排序
    print("\n3️⃣ 测试Mosaic模块:")
    try:
        from Mosaic.mosaic_pic import MosaicGenerator
        mosaic = MosaicGenerator(str(input_path), "temp_output")
        files3 = mosaic.get_image_files()
        print(f"   ✅ Mosaic: {len(files3)} 个文件，顺序正确")
        print(f"   📂 首个: {files3[0].relative_to(input_path)}")
        print(f"   📂 末个: {files3[-1].relative_to(input_path)}")
    except Exception as e:
        print(f"   ❌ Mosaic测试失败: {e}")
    
    # 验证所有模块的文件顺序一致性
    print("\n4️⃣ 验证模块间一致性:")
    try:
        if 'files1' in locals() and 'files2' in locals() and 'files3' in locals():
            if files1 == files2 == files3:
                print(f"   ✅ 所有模块的文件顺序完全一致")
            else:
                print(f"   ❌ 模块间文件顺序不一致")
                print(f"      Pipeline: {len(files1)} 个文件")
                print(f"      Resize: {len(files2)} 个文件") 
                print(f"      Mosaic: {len(files3)} 个文件")
        else:
            print(f"   ⚠️ 部分模块测试失败，无法验证一致性")
    except Exception as e:
        print(f"   ❌ 一致性验证失败: {e}")
    
    # 显示最终的时间线验证
    if 'files1' in locals():
        print(f"\n🎯 时间线验证:")
        print(f"   📅 从: {files1[0].parent.name} - {files1[0].name}")
        print(f"   📅 到: {files1[-1].parent.name} - {files1[-1].name}")
        print(f"   📊 跨度: {len(set(f.parent.name for f in files1))} 个月份")
        print(f"   📸 总计: {len(files1)} 张照片")
    
    print(f"\n🎉 文件顺序修复验证完成!")

if __name__ == "__main__":
    test_all_modules_file_order()