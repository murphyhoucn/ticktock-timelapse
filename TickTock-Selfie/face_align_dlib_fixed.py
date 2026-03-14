#!/usr/bin/env python3
"""
TickTock Face Alignment Tool - dlib修复版本（使用PIL读取）
每天一张自拍照，时间长了就能拼成一个延时视频
本工具用于对齐人脸照片，使制作延时视频更加流畅

使用PIL读取图像，避免OpenCV与dlib的兼容性问题
"""

import os
import numpy as np
from pathlib import Path
import argparse
from typing import List, Tuple, Optional
import logging
import dlib
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaceAligner:
    """
    人脸对齐器 - dlib实现（使用PIL读取图像）
    使用dlib的人脸检测器和68点关键点预测器进行高精度人脸对齐
    """
    
    def __init__(self, predictor_path="shape_predictor_68_face_landmarks.dat"):
        """
        初始化人脸对齐器
        Args:
            predictor_path: dlib 68点关键点预测器模型路径
        """
        # 初始化dlib人脸检测器
        self.detector = dlib.get_frontal_face_detector()
        logger.info("✅ dlib人脸检测器初始化成功")
        
        # 初始化dlib关键点预测器
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"dlib预测器模型文件不存在: {predictor_path}")
        
        self.predictor = dlib.shape_predictor(predictor_path)
        logger.info("✅ dlib关键点预测器加载成功")
        
        # 标准人脸模板关键点（5个关键点：双眼、鼻尖、嘴角）
        self.template_landmarks = np.array([
            [0.31556875000000000, 0.4615741071428571],   # 左眼中心
            [0.68262291666666670, 0.4615741071428571],   # 右眼中心
            [0.50026249999999990, 0.6405053571428571],   # 鼻尖
            [0.34947187500000004, 0.8246919642857142],   # 左嘴角
            [0.65343645833333330, 0.8246919642857142]    # 右嘴角
        ], dtype=np.float32)

    def load_image(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用PIL加载图像，并转换为dlib兼容格式
        Args:
            image_path: 图像路径
        Returns:
            (rgb_array, bgr_array): RGB数组（用于dlib）和BGR数组（用于保存）
        """
        # 使用PIL加载图像
        pil_image = Image.open(image_path)
        
        # 转换为RGB模式（如果不是）
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # 转换为numpy数组 - PIL返回的是RGB格式
        rgb_array = np.array(pil_image, dtype=np.uint8)
        
        # 创建BGR版本（用于保存）
        bgr_array = rgb_array[:, :, ::-1].copy()
        
        logger.debug(f"图像加载: shape={rgb_array.shape}, dtype={rgb_array.dtype}, mode=RGB")
        
        return rgb_array, bgr_array

    def detect_faces(self, rgb_image: np.ndarray) -> List[dlib.rectangle]:
        """
        使用dlib检测人脸
        Args:
            rgb_image: RGB格式的输入图像（从PIL加载）
        Returns:
            检测到的人脸区域列表
        """
        # dlib可以直接处理RGB图像或灰度图
        # 先尝试RGB
        try:
            faces = self.detector(rgb_image, 1)
            logger.debug(f"使用RGB检测到 {len(faces)} 个人脸")
            if len(faces) > 0:
                return faces
        except Exception as e:
            logger.warning(f"RGB检测失败: {e}")
        
        # 如果RGB失败，尝试灰度图
        try:
            # 手动转换为灰度（避免使用OpenCV）
            gray = np.dot(rgb_image[...,:3], [0.299, 0.587, 0.114])
            gray = gray.astype(np.uint8)
            
            faces = self.detector(gray, 1)
            logger.debug(f"使用灰度检测到 {len(faces)} 个人脸")
            return faces
        except Exception as e:
            logger.error(f"灰度检测也失败: {e}")
            return []
    
    def get_landmarks(self, rgb_image: np.ndarray, face_rect: dlib.rectangle) -> np.ndarray:
        """
        获取68个人脸关键点
        Args:
            rgb_image: RGB格式的输入图像
            face_rect: 人脸区域
        Returns:
            68个关键点坐标 (68, 2)
        """
        # 先尝试RGB
        try:
            landmarks = self.predictor(rgb_image, face_rect)
        except Exception as e:
            logger.warning(f"RGB关键点检测失败: {e}")
            # 尝试灰度图
            gray = np.dot(rgb_image[...,:3], [0.299, 0.587, 0.114])
            gray = gray.astype(np.uint8)
            landmarks = self.predictor(gray, face_rect)
        
        # 转换为numpy数组
        coords = np.zeros((68, 2), dtype=np.float32)
        for i in range(68):
            coords[i] = (landmarks.part(i).x, landmarks.part(i).y)
        
        return coords
    
    def get_5_landmarks_from_68(self, landmarks_68: np.ndarray) -> np.ndarray:
        """
        从68个关键点中提取5个用于对齐的关键点
        Args:
            landmarks_68: 68个关键点
        Returns:
            5个关键点（左眼、右眼、鼻尖、左嘴角、右嘴角）
        """
        # 左眼：点36-41的中心
        left_eye = landmarks_68[36:42].mean(axis=0)
        # 右眼：点42-47的中心
        right_eye = landmarks_68[42:48].mean(axis=0)
        # 鼻尖：点30
        nose = landmarks_68[30]
        # 左嘴角：点48
        left_mouth = landmarks_68[48]
        # 右嘴角：点54
        right_mouth = landmarks_68[54]
        
        return np.array([left_eye, right_eye, nose, left_mouth, right_mouth], dtype=np.float32)
    
    def align_face(self, bgr_image: np.ndarray, landmarks_5: np.ndarray, 
                   output_size: Tuple[int, int]) -> np.ndarray:
        """
        对齐人脸
        Args:
            bgr_image: BGR格式的输入图像
            landmarks_5: 5个关键点
            output_size: 输出图像尺寸 (width, height)
        Returns:
            对齐后的人脸图像
        """
        # 导入cv2用于仿射变换（只在这里用，不用于读取）
        import cv2
        
        # 计算目标关键点位置
        target_landmarks = self.template_landmarks * np.array([output_size[0], output_size[1]])
        
        # 计算仿射变换矩阵
        transform_matrix = cv2.estimateAffinePartial2D(landmarks_5, target_landmarks)[0]
        
        # 应用仿射变换
        aligned_face = cv2.warpAffine(bgr_image, transform_matrix, output_size)
        
        return aligned_face
    
    def process_image(self, image_path: str, output_path: str, keep_original_size: bool = False) -> bool:
        """
        处理单张图片
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            keep_original_size: 是否保持原始图片尺寸
        Returns:
            是否成功
        """
        try:
            # 使用PIL加载图像
            rgb_image, bgr_image = self.load_image(image_path)
            h, w = rgb_image.shape[:2]
            
            # 检测人脸
            faces = self.detect_faces(rgb_image)
            
            if len(faces) == 0:
                logger.warning("未检测到人脸")
                return False
            
            # 使用第一个检测到的人脸
            face = faces[0]
            
            # 获取68个关键点
            landmarks_68 = self.get_landmarks(rgb_image, face)
            
            # 提取5个关键点
            landmarks_5 = self.get_5_landmarks_from_68(landmarks_68)
            
            # 确定输出尺寸
            if keep_original_size:
                output_size = (w, h)
            else:
                output_size = (256, 256)
            
            # 对齐人脸
            aligned_face = self.align_face(bgr_image, landmarks_5, output_size)
            
            # 保存结果 - 使用PIL保存
            output_pil = Image.fromarray(aligned_face[:, :, ::-1])  # BGR转RGB
            output_pil.save(output_path, quality=95)
            
            return True
            
        except Exception as e:
            logger.error(f"处理图片时出错: {e}", exc_info=True)
            return False
    
    def process_directory(self, input_dir: str, output_dir: str, keep_original_size: bool = False):
        """
        批量处理目录中的所有图片
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            keep_original_size: 是否保持原始图片尺寸
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # 获取所有图片文件
        image_files = [f for f in input_path.iterdir() 
                      if f.is_file() and f.suffix.lower() in image_extensions]
        
        if not image_files:
            logger.warning(f"未在 {input_dir} 中找到图片文件")
            return
        
        logger.info(f"找到 {len(image_files)} 张图片")
        
        # 处理每张图片
        success_count = 0
        for i, image_file in enumerate(image_files, 1):
            logger.info(f"处理第 {i}/{len(image_files)} 张图片: {image_file.name}")
            
            output_file = output_path / image_file.name
            
            if self.process_image(str(image_file), str(output_file), keep_original_size):
                success_count += 1
                logger.info(f"✅ 成功对齐: {image_file.name}")
            else:
                logger.warning(f"人脸对齐失败: {image_file.name}")
        
        logger.info(f"处理完成！成功对齐 {success_count}/{len(image_files)} 张图片")


def main():
    parser = argparse.ArgumentParser(description='TickTock人脸对齐工具 - dlib修复版本')
    parser.add_argument('--input', type=str, required=True, help='输入目录路径')
    parser.add_argument('--output', type=str, required=True, help='输出目录路径')
    parser.add_argument('--predictor', type=str, default='shape_predictor_68_face_landmarks.dat',
                       help='dlib关键点预测器模型路径')
    parser.add_argument('--keep-original-size', action='store_true',
                       help='保持原始图片尺寸（默认输出256x256）')
    
    args = parser.parse_args()
    
    try:
        # 初始化人脸对齐器
        aligner = FaceAligner(predictor_path=args.predictor)
        
        # 处理目录
        aligner.process_directory(args.input, args.output, args.keep_original_size)
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        logger.error("请确保已下载dlib的68点关键点预测器模型")
        logger.error("下载链接: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)


if __name__ == '__main__':
    main()
