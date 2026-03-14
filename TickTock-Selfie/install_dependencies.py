#!/usr/bin/env python3
"""
TickTock Face Alignment Tool - 智能安装脚本
自动检测环境并安装合适的依赖包
"""

import subprocess
import sys
import os

def run_command(command):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_package(package):
    """安装Python包"""
    print(f"正在安装 {package}...")
    success, stdout, stderr = run_command(f"pip install {package}")
    if success:
        print(f"✅ {package} 安装成功")
        return True
    else:
        print(f"❌ {package} 安装失败: {stderr}")
        return False

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package.replace('-', '_'))
        return True
    except ImportError:
        return False

def main():
    print("🚀 TickTock Face Alignment Tool - 智能安装器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 安装核心依赖
    core_packages = [
        "numpy>=1.21.0",
        "opencv-python>=4.5.0"
    ]
    
    print("\n📦 安装核心依赖...")
    for package in core_packages:
        install_package(package)
    
    # 尝试安装dlib
    print("\n🎯 尝试安装dlib（高精度人脸对齐支持）...")
    dlib_installed = False
    
    # 方法1: 直接安装dlib
    if install_package("dlib>=19.22.0"):
        dlib_installed = True
    else:
        print("⚠️ 标准dlib安装失败，尝试预编译版本...")
        
        # 方法2: 使用项目中的预编译版本
        whl_file = "dlib-19.22.99-cp310-cp310-win_amd64.whl"
        if os.path.exists(whl_file):
            if install_package(whl_file):
                dlib_installed = True
            else:
                print("⚠️ 预编译dlib安装也失败")
        else:
            print("⚠️ 未找到预编译dlib文件")
    
    # 安装结果总结
    print("\n" + "=" * 50)
    print("📋 安装结果总结:")
    
    if check_package("numpy"):
        print("✅ NumPy - 已安装")
    else:
        print("❌ NumPy - 安装失败")
    
    if check_package("cv2"):
        print("✅ OpenCV - 已安装")
    else:
        print("❌ OpenCV - 安装失败")
    
    if check_package("dlib"):
        print("✅ dlib - 已安装（支持高精度对齐）")
        print("🎯 推荐使用: python face_align_smart.py")
    else:
        print("⚠️ dlib - 未安装（仅支持OpenCV对齐）")
        print("🎯 推荐使用: python face_align_opencv.py")
    
    print("\n🚀 安装完成！快速开始:")
    print("1. 将照片放入 Everyday 文件夹")
    if dlib_installed:
        print("2. 运行: python face_align_smart.py --keep-original-size")
    else:
        print("2. 运行: python face_align_opencv.py --keep-original-size")
    print("3. 生成视频: python create_video.py")

if __name__ == "__main__":
    main()