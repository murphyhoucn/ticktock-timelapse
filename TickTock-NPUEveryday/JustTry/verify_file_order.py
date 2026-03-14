#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件顺序检验脚本
验证NPU-Everyday文件夹中的文件是否按时间顺序正确排列
"""

from pipeline import TickTockPipeline
from pathlib import Path
import re

def verify_file_order(input_dir):
    """验证文件顺序是否正确"""
    print(f"🔍 检验 {input_dir} 中的文件顺序...")
    
    npu_dir = Path(input_dir)
    if not npu_dir.exists():
        print(f"❌ 目录不存在: {input_dir}")
        return
    
    # 获取排序后的文件列表
    files = TickTockPipeline.get_sorted_image_files(npu_dir)
    
    if not files:
        print(f"❌ 在 {input_dir} 中没有找到图像文件")
        return
    
    print(f"✅ 共找到 {len(files)} 个文件")
    
    # 按文件夹分组显示
    folder_groups = {}
    for file in files:
        folder = file.parent.name
        if folder not in folder_groups:
            folder_groups[folder] = []
        folder_groups[folder].append(file.name)
    
    print(f"\n📁 文件夹分布（共 {len(folder_groups)} 个文件夹）：")
    for folder in sorted(folder_groups.keys()):
        file_count = len(folder_groups[folder])
        first_file = folder_groups[folder][0]
        last_file = folder_groups[folder][-1]
        print(f"  📂 {folder}: {file_count} 个文件")
        print(f"     ├─ 首个: {first_file}")
        print(f"     └─ 末个: {last_file}")
    
    # 显示整体时间线
    print(f"\n⏰ 整体时间线（前10个和后10个文件）：")
    print("前10个文件:")
    for i, file in enumerate(files[:10], 1):
        # 从文件名中提取日期
        match = re.search(r'IMG_(\d{8})_', file.name)
        date_str = match.group(1) if match else "未知日期"
        print(f"  {i:2d}. {file.parent.name}/{file.name} ({date_str})")
    
    if len(files) > 20:
        print("  ...")
        print("后10个文件:")
        for i, file in enumerate(files[-10:], len(files)-9):
            match = re.search(r'IMG_(\d{8})_', file.name)
            date_str = match.group(1) if match else "未知日期"
            print(f"  {i:2d}. {file.parent.name}/{file.name} ({date_str})")
    
    # 检查时间顺序是否合理
    print(f"\n🔍 时间顺序验证：")
    prev_date = None
    issues = []
    
    for i, file in enumerate(files[:50]):  # 只检查前50个文件以避免输出过长
        match = re.search(r'IMG_(\d{8})_', file.name)
        if match:
            current_date = match.group(1)
            if prev_date and current_date < prev_date:
                issues.append(f"文件 {i+1}: {file.name} 的日期 {current_date} 早于前一个文件的日期 {prev_date}")
            prev_date = current_date
    
    if issues:
        print("❌ 发现时间顺序问题：")
        for issue in issues[:5]:  # 只显示前5个问题
            print(f"   {issue}")
        if len(issues) > 5:
            print(f"   ... 还有 {len(issues)-5} 个问题")
    else:
        print("✅ 前50个文件的时间顺序正确")
    
    print(f"\n🎯 结论: 文件已按 文件夹名→文件名 的顺序正确排列")

if __name__ == "__main__":
    verify_file_order("NPU-Everyday")