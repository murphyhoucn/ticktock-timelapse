#!/usr/bin/env python3
"""
简单的人脸对齐演示脚本
"""

import cv2
import os
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_images():
    """创建一些演示图片（使用摄像头或示例图片）"""
    
    # 检查是否有摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.warning("无法打开摄像头，请手动添加图片到 Everyday 文件夹")
        return
    
    everyday_folder = "Everyday"
    os.makedirs(everyday_folder, exist_ok=True)
    
    logger.info("按空格键拍照，按ESC键退出")
    
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 显示预览
        cv2.imshow('拍照预览 - 按空格键拍照，ESC键退出', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键
            break
        elif key == 32:  # 空格键
            count += 1
            filename = f"{everyday_folder}/photo_{count:03d}.jpg"
            cv2.imwrite(filename, frame)
            logger.info(f"保存照片: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    logger.info(f"总共拍摄了 {count} 张照片")

if __name__ == "__main__":
    print("=== TickTock Face Alignment Demo ===")
    print("1. 首先会尝试使用摄像头拍摄一些照片")
    print("2. 然后对这些照片进行人脸对齐")
    print("=====================================")
    
    # 创建演示图片
    create_demo_images()