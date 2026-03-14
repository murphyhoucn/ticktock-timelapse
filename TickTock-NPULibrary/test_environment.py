#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境测试脚本
检查必需的Python包是否已安装
"""

import sys
import os

def test_environment(data_dirs):
    """测试运行环境"""
    print("=" * 60)
    print("TickTock-Align-NPU Library 环境测试")
    print("=" * 60)
    
    # Python版本检查
    print(f"✅ Python版本: {sys.version}")
    
    # 核心包检查
    required_packages = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),  
        ('PIL', 'Pillow'),
        ('matplotlib', 'matplotlib'),
        ('pathlib', '内置模块'),
        ('os', '内置模块'),
        ('glob', '内置模块')
    ]
    
    missing_packages = []
    
    for package, pip_name in required_packages:
        try:
            if package == 'cv2':
                import cv2
                print(f"✅ OpenCV: {cv2.__version__}")
            elif package == 'numpy':
                import numpy as np
                print(f"✅ NumPy: {np.__version__}")
            elif package == 'PIL':
                from PIL import Image
                print(f"✅ Pillow: {Image.__version__}")
            else:
                __import__(package)
                print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装 (需要: {pip_name})")
            if pip_name != '内置模块':
                missing_packages.append(pip_name)
    
    # 可选包检查
    optional_packages = [
        ('pandas', 'pandas'),
    ]
    
    print("\n可选功能包:")
    for package, pip_name in optional_packages:
        try:
            if package == 'pandas':
                import pandas as pd
                print(f"✅ Pandas: {pd.__version__}")
            else:
                __import__(package)
                print(f"✅ {package}: 已安装")
        except ImportError as e:
            print(f"⚠️ {package}: 导入失败 - {str(e)[:50]}...")
            print(f"   建议重新安装: pip install --upgrade {pip_name}")
        except Exception as e:
            print(f"⚠️ {package}: 已安装但存在兼容性问题")
            print(f"   错误: {str(e)[:50]}...")
            print(f"   建议重新安装: pip install --upgrade {pip_name} numpy")
    
    # FFmpeg检查
    print("\n外部工具检查:")
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version_line}")
        else:
            print("❌ FFmpeg: 命令执行失败")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg: 未安装或未添加到PATH")
        print("   延时摄影功能需要FFmpeg支持")
    
    # 总结
    print("\n" + "=" * 60)
    if missing_packages:
        print("❌ 环境检查失败，缺少必需包:")
        for package in missing_packages:
            print(f"   pip install {package}")
    else:
        print("✅ 核心环境检查通过!")
        print("可以运行图像放缩和对齐功能")
    
    # 数据目录检查
    print("\n数据目录检查:")
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            # 统计图片数量
            image_count = 0
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                        image_count += 1
            print(f"✅ {data_dir}: 找到 {image_count} 个图片文件")
        else:
            print(f"⚠️ {data_dir}: 目录不存在")
    
    print("=" * 60)

if __name__ == "__main__":
    data_dirs = ['NPU-Everyday', 'NPU-Everyday-Sample']
    test_environment(data_dirs)