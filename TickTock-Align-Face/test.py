#!/usr/bin/env python3
"""
测试脚本 - 验证各个组件是否正常工作
"""

import os
import sys
import importlib.util
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """测试必要的库是否安装"""
    logger.info("测试Python库导入...")
    
    required_modules = [
        'cv2', 'numpy', 'dlib', 'imutils', 'pathlib'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except ImportError:
            logger.error(f"✗ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"缺少以下库: {', '.join(missing_modules)}")
        logger.info("请运行: pip install -r requirements.txt")
        return False
    
    return True

def test_predictor_file():
    """测试人脸关键点检测器文件是否存在"""
    logger.info("测试人脸关键点检测器...")
    
    predictor_file = "shape_predictor_68_face_landmarks.dat"
    
    if os.path.exists(predictor_file):
        file_size = os.path.getsize(predictor_file) / (1024 * 1024)  # MB
        logger.info(f"✓ 检测器文件存在，大小: {file_size:.1f}MB")
        return True
    else:
        logger.error("✗ 检测器文件不存在")
        logger.info("请运行: python face_align.py --download")
        return False

def test_folders():
    """测试文件夹结构"""
    logger.info("测试文件夹结构...")
    
    folders = ['Everyday', 'Everyday_align']
    
    for folder in folders:
        if os.path.exists(folder):
            logger.info(f"✓ {folder} 文件夹存在")
            return True
        else:
            logger.warning(f"! {folder} 文件夹不存在，将自动创建")
            os.makedirs(folder, exist_ok=True)
            return True

def test_face_aligner():
    """测试人脸对齐器是否能正常初始化"""
    logger.info("测试人脸对齐器...")
    
    try:
        from face_align_dlib import FaceAligner
        aligner = FaceAligner()
        logger.info("✓ 人脸对齐器初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ 人脸对齐器初始化失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("=== TickTock Face Alignment 系统测试 ===")
    
    tests = [
        ("Python库导入", test_imports),
        ("人脸检测器文件", test_predictor_file),
        ("文件夹结构", test_folders),
        ("人脸对齐器", test_face_aligner),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    logger.info("\n=== 测试结果汇总 ===")
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n通过率: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    
    if passed == len(results):
        logger.info("🎉 所有测试通过！系统准备就绪。")
        logger.info("现在可以将照片放入 Everyday 文件夹并运行 python face_align.py")
    else:
        logger.warning("⚠️  部分测试失败，请根据上面的提示修复问题。")

if __name__ == "__main__":
    run_all_tests()