#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeLapse@Desk 测试脚本
用于测试摄像头和依赖包是否正常工作
"""

import cv2
import sys

def test_camera():
    """测试摄像头"""
    print("=== 摄像头测试 ===")
    
    # 尝试打开摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 摄像头无法打开")
        print("请检查：")
        print("1. 摄像头是否连接正常")
        print("2. 摄像头是否被其他程序占用")
        print("3. 尝试使用不同的摄像头索引（如 1, 2）")
        return False
    
    print("✅ 摄像头打开成功")
    
    # 获取摄像头信息
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"摄像头分辨率: {width}x{height}")
    print(f"帧率: {fps} FPS")
    
    # 尝试拍摄一帧
    ret, frame = cap.read()
    if ret:
        print("✅ 成功拍摄测试帧")
    else:
        print("❌ 无法拍摄测试帧")
        cap.release()
        return False
    
    cap.release()
    return True

def test_dependencies():
    """测试依赖包"""
    print("\n=== 依赖包测试 ===")
    
    # 测试OpenCV
    try:
        import cv2
        print(f"✅ OpenCV 版本: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV 未安装")
        return False
    
    # 测试MediaPipe
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe 版本: {mp.__version__}")
    except ImportError:
        print("❌ MediaPipe 未安装")
        return False
    
    # 测试NumPy
    try:
        import numpy as np
        print(f"✅ NumPy 版本: {np.__version__}")
    except ImportError:
        print("❌ NumPy 未安装")
        return False
    
    return True

def test_face_detection():
    """测试人脸检测功能"""
    print("\n=== 人脸检测测试 ===")
    
    try:
        import mediapipe as mp
        
        # 初始化人脸检测
        mp_face_detection = mp.solutions.face_detection
        face_detection = mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5)
        
        print("✅ 人脸检测模型加载成功")
        
        # 测试人脸网格
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5)
        
        print("✅ 人脸关键点检测模型加载成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 人脸检测测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("TimeLapse@Desk 系统测试")
    print("="*50)
    
    # 测试Python版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ Python版本过低，建议使用Python 3.7或更高版本")
        return False
    
    print("✅ Python版本符合要求")
    
    # 依赖包测试
    deps_ok = test_dependencies()
    if not deps_ok:
        print("\n请运行以下命令安装依赖包：")
        print("pip install -r requirements.txt")
        return False
    
    # 人脸检测测试
    face_ok = test_face_detection()
    if not face_ok:
        return False
    
    # 摄像头测试
    camera_ok = test_camera()
    if not camera_ok:
        return False
    
    print("\n" + "="*50)
    print("🎉 所有测试通过！系统准备就绪！")
    print("现在可以运行 timelapse_demo.py 开始拍照了！")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\n按Enter键退出...")
    sys.exit(0 if success else 1)