#!/usr/bin/env python3
"""
测试纯dlib版本的人脸对齐效果
"""

import cv2
import numpy as np
from pathlib import Path

def compare_alignment_results():
    """比较不同版本的对齐结果"""
    
    # 测试文件夹
    original_folder = Path("Everyday")
    dlib_folder = Path("dlib_aligned")
    
    if not original_folder.exists():
        print("❌ 原始图片文件夹不存在")
        return
    
    if not dlib_folder.exists():
        print("❌ dlib对齐结果文件夹不存在")
        return
    
    # 获取一张图片进行对比
    test_image = "WIN_20250926_14_39_27_Pro.jpg"
    
    original_path = original_folder / test_image
    dlib_path = dlib_folder / test_image
    
    if not original_path.exists() or not dlib_path.exists():
        print(f"❌ 测试图片不存在: {test_image}")
        return
    
    # 读取图片
    original = cv2.imread(str(original_path))
    dlib_aligned = cv2.imread(str(dlib_path))
    
    if original is None or dlib_aligned is None:
        print("❌ 无法读取测试图片")
        return
    
    print(f"✅ 原始图片尺寸: {original.shape}")
    print(f"✅ dlib对齐后尺寸: {dlib_aligned.shape}")
    
    # 检查尺寸是否保持
    if original.shape == dlib_aligned.shape:
        print("✅ 成功保持原始图像尺寸！")
    else:
        print("❌ 图像尺寸发生了变化")
    
    # 创建对比图
    if original.shape == dlib_aligned.shape:
        # 水平拼接
        comparison = np.hstack([original, dlib_aligned])
        
        # 添加分割线
        line_x = original.shape[1]
        cv2.line(comparison, (line_x, 0), (line_x, comparison.shape[0]), (0, 255, 0), 3)
        
        # 添加文字标签
        cv2.putText(comparison, "Original", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.putText(comparison, "dlib Aligned", (line_x + 50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        
        # 保存对比图
        cv2.imwrite("dlib_alignment_comparison.jpg", comparison)
        print("✅ 保存对比图: dlib_alignment_comparison.jpg")
        
        # 缩放预览图
        scale = 0.3
        preview = cv2.resize(comparison, None, fx=scale, fy=scale)
        cv2.imwrite("dlib_alignment_preview.jpg", preview)
        print("✅ 保存预览图: dlib_alignment_preview.jpg")

if __name__ == "__main__":
    compare_alignment_results()