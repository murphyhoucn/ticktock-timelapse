#!/usr/bin/env python3
"""
简化版人脸对齐工具 - 使用OpenCV进行基本对齐
"""

import cv2
import os
import numpy as np
from pathlib import Path
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFaceAligner:
    """简化的人脸对齐器，使用OpenCV"""
    
    def __init__(self):
        """初始化人脸检测器"""
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if self.face_cascade.empty():
            raise RuntimeError("无法加载人脸检测器")
        if self.eye_cascade.empty():
            logger.warning("无法加载眼部检测器，将使用简化对齐")
    
    def detect_face_and_eyes(self, image: np.ndarray):
        """
        检测人脸和眼睛
        Args:
            image: 输入图像
        Returns:
            (face_rect, left_eye, right_eye) 或 None
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # 选择最大的人脸
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face
        
        # 在人脸区域内检测眼睛
        face_roi = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3)
        
        if len(eyes) < 2:
            # 如果检测不到眼睛，使用估算位置
            left_eye = (x + int(w * 0.3), y + int(h * 0.4))
            right_eye = (x + int(w * 0.7), y + int(h * 0.4))
        else:
            # 排序眼睛（左眼和右眼）
            eyes = sorted(eyes, key=lambda e: e[0])
            
            # 转换回原图坐标
            left_eye = (x + eyes[0][0] + eyes[0][2]//2, y + eyes[0][1] + eyes[0][3]//2)
            right_eye = (x + eyes[1][0] + eyes[1][2]//2, y + eyes[1][1] + eyes[1][3]//2)
        
        return ((x, y, w, h), left_eye, right_eye)
    
    def align_face(self, image: np.ndarray, output_size: tuple = None, keep_original_size: bool = True):
        """
        对齐人脸
        Args:
            image: 输入图像
            output_size: 输出尺寸，如果为None且keep_original_size=True则使用原始尺寸
            keep_original_size: 是否保持原始图像尺寸
        Returns:
            对齐后的图像或None
        """
        result = self.detect_face_and_eyes(image)
        
        if result is None:
            return None
        
        face_rect, left_eye, right_eye = result
        
        # 如果要保持原始尺寸，使用输入图像的尺寸
        if keep_original_size and output_size is None:
            output_size = (image.shape[1], image.shape[0])  # (width, height)
        elif output_size is None:
            output_size = (256, 256)  # 默认尺寸
        
        # 计算眼睛中心点（确保是float类型）
        eye_center = (float(left_eye[0] + right_eye[0]) / 2, float(left_eye[1] + right_eye[1]) / 2)
        
        # 计算旋转角度
        dy = float(right_eye[1] - left_eye[1])
        dx = float(right_eye[0] - left_eye[0])
        angle = np.degrees(np.arctan2(dy, dx))
        
        if keep_original_size:
            # 保持原始尺寸时，只进行旋转对齐，不缩放
            # 计算旋转矩阵（scale=1.0，不缩放）
            M = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
            
            # 调整平移，使眼睛保持在合适的位置
            # 可以选择保持眼睛在原位置，或者移动到理想位置
            desired_eye_x = output_size[0] * 0.5  # 水平居中
            desired_eye_y = output_size[1] * 0.4  # 眼睛在上部1/3处
            
            M[0, 2] += (desired_eye_x - eye_center[0])
            M[1, 2] += (desired_eye_y - eye_center[1])
        else:
            # 原来的缩放逻辑
            eye_distance = np.sqrt((dx ** 2) + (dy ** 2))
            desired_eye_distance = output_size[0] * 0.35
            scale = desired_eye_distance / eye_distance
            
            # 计算旋转矩阵
            M = cv2.getRotationMatrix2D(eye_center, angle, scale)
            
            # 调整平移，使眼睛在输出图像的理想位置
            desired_eye_y = output_size[1] * 0.4
            M[0, 2] += (output_size[0] * 0.5 - eye_center[0])
            M[1, 2] += (desired_eye_y - eye_center[1])
        
        # 应用变换
        aligned = cv2.warpAffine(image, M, output_size)
        
        return aligned
    
    def process_folder(self, input_folder: str, output_folder: str, output_size: tuple = None, keep_original_size: bool = True):
        """
        处理文件夹中的所有图片
        Args:
            input_folder: 输入文件夹
            output_folder: 输出文件夹
            output_size: 输出尺寸，如果为None且keep_original_size=True则保持原始尺寸
            keep_original_size: 是否保持原始图像尺寸
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            logger.error(f"输入文件夹不存在: {input_folder}")
            return
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        # 获取所有图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_path.glob(f'*{ext}'))
            image_files.extend(input_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            logger.warning(f"在 {input_folder} 中未找到图片文件")
            return
        
        image_files.sort()
        logger.info(f"找到 {len(image_files)} 张图片，开始处理...")
        
        success_count = 0
        for i, image_file in enumerate(image_files):
            logger.info(f"处理第 {i+1}/{len(image_files)} 张图片: {image_file.name}")
            
            try:
                # 读取图片
                image = cv2.imread(str(image_file))
                if image is None:
                    logger.warning(f"无法读取图片: {image_file}")
                    continue
                
                # 对齐人脸
                aligned_face = self.align_face(image, output_size, keep_original_size)
                
                if aligned_face is not None:
                    # 保存对齐后的图片
                    output_file = output_path / image_file.name
                    cv2.imwrite(str(output_file), aligned_face)
                    success_count += 1
                    logger.info(f"成功保存: {output_file}")
                else:
                    logger.warning(f"人脸对齐失败: {image_file}")
                    
            except Exception as e:
                logger.error(f"处理图片时出错 {image_file}: {e}")
        
        logger.info(f"处理完成！成功对齐 {success_count}/{len(image_files)} 张图片")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版人脸对齐工具')
    parser.add_argument('--input', '-i', default='Everyday',
                       help='输入文件夹路径 (默认: Everyday)')
    parser.add_argument('--output', '-o', default='Everyday_align_opencv',
                       help='输出文件夹路径 (默认: Everyday_align_opencv)')
    parser.add_argument('--size', '-s', nargs=2, type=int, default=None,
                       help='输出图像大小，不指定则保持原始尺寸 (例如: --size 256 256)')
    parser.add_argument('--keep-original-size', action='store_true', default=True,
                       help='保持原始图像尺寸 (默认: True)')
    parser.add_argument('--resize', action='store_true',
                       help='强制调整到指定尺寸，覆盖 --keep-original-size')
    
    args = parser.parse_args()
    
    # 处理参数逻辑
    keep_original_size = args.keep_original_size and not args.resize
    output_size = tuple(args.size) if args.size else None
    
    try:
        # 创建简化人脸对齐器
        aligner = SimpleFaceAligner()
        
        # 处理图片
        aligner.process_folder(args.input, args.output, output_size, keep_original_size)
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()