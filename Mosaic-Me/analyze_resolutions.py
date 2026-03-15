#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分辨率统计工具
读取指定文件夹下所有图片的分辨率并进行统计
"""

import os
from pathlib import Path
from PIL import Image
from collections import Counter

# 目标文件夹
# TARGET_FOLDER = Path(r"C:\Users\cosmi\Nutstore\1\AInBox\MYYEAR2025")
TARGET_FOLDER = Path(r"D:\DevProj\Mosaic-Me\Douyin-Size")

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.JPG', '.JPEG', '.PNG'}

def get_image_resolution(image_path):
    """
    获取图片分辨率
    
    Args:
        image_path: 图片路径
        
    Returns:
        tuple: (width, height) 或 None（如果读取失败）
    """
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        print(f"⚠ 无法读取图片 {image_path.name}: {e}")
        return None

def scan_images():
    """扫描文件夹并统计图片分辨率"""
    print("="*70)
    print("图片分辨率统计工具")
    print("="*70)
    print(f"目标文件夹: {TARGET_FOLDER}\n")
    
    if not TARGET_FOLDER.exists():
        print(f"❌ 错误: 文件夹不存在！")
        return
    
    # 收集所有图片文件
    print("正在扫描图片文件...")
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(list(TARGET_FOLDER.glob(f"*{ext}")))
    
    # 去重（Windows文件系统不区分大小写）
    image_files = list(set(image_files))
    
    total_images = len(image_files)
    print(f"找到 {total_images} 张图片\n")
    
    if total_images == 0:
        print("没有找到图片文件")
        return
    
    # 读取所有图片的分辨率
    print("正在读取图片分辨率...")
    resolutions = []
    failed_count = 0
    
    for idx, img_path in enumerate(image_files, 1):
        resolution = get_image_resolution(img_path)
        if resolution:
            resolutions.append(resolution)
        else:
            failed_count += 1
        
        # 显示进度
        if idx % 50 == 0 or idx == total_images:
            print(f"进度: {idx}/{total_images}")
    
    print(f"\n成功读取: {len(resolutions)} 张")
    if failed_count > 0:
        print(f"失败: {failed_count} 张")
    
    # 统计分辨率
    print("\n" + "="*70)
    print("分辨率统计结果")
    print("="*70)
    
    resolution_counter = Counter(resolutions)
    
    # 按数量排序（从多到少）
    sorted_resolutions = sorted(resolution_counter.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n共发现 {len(sorted_resolutions)} 种不同的分辨率：\n")
    print(f"{'序号':<6}{'分辨率 (宽×高)':<25}{'数量':<10}{'比例':<10}{'方向'}")
    print("-"*70)
    
    for idx, (resolution, count) in enumerate(sorted_resolutions, 1):
        width, height = resolution
        percentage = (count / len(resolutions)) * 100
        
        # 计算宽高比
        gcd = lambda a, b: a if b == 0 else gcd(b, a % b)
        divisor = gcd(width, height)
        ratio_w = width // divisor
        ratio_h = height // divisor
        
        # 判断方向
        if width > height:
            orientation = "横向"
        elif width < height:
            orientation = "竖向"
        else:
            orientation = "正方形"
        
        print(f"{idx:<6}{width}×{height:<20}{count:<10}{percentage:.1f}%{' ':<5}{orientation} ({ratio_w}:{ratio_h})")
    
    # 总体统计
    print("\n" + "="*70)
    print("总体统计")
    print("="*70)
    
    # 方向统计
    landscape = sum(1 for w, h in resolutions if w > h)
    portrait = sum(1 for w, h in resolutions if w < h)
    square = sum(1 for w, h in resolutions if w == h)
    
    print(f"\n方向分布:")
    print(f"  横向图片: {landscape} 张 ({landscape/len(resolutions)*100:.1f}%)")
    print(f"  竖向图片: {portrait} 张 ({portrait/len(resolutions)*100:.1f}%)")
    print(f"  正方形: {square} 张 ({square/len(resolutions)*100:.1f}%)")
    
    # 最常见的分辨率
    most_common = sorted_resolutions[0]
    print(f"\n最常见的分辨率:")
    print(f"  {most_common[0][0]}×{most_common[0][1]} - {most_common[1]} 张 ({most_common[1]/len(resolutions)*100:.1f}%)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    scan_images()
