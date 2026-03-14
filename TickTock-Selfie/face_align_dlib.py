#!/usr/bin/env python3
"""
TickTock Face Alignment Tool - 纯dlib版本（保持原始尺寸）
每天一张自拍照，时间长了就能拼成一个延时视频
本工具用于对齐人脸照片，使制作延时视频更加流畅

纯dlib实现，使用68点关键点进行高精度人脸对齐
"""

import cv2
import os
import numpy as np
from pathlib import Path
import argparse
from typing import List, Tuple, Optional
import logging
import dlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaceAligner:
    """
    人脸对齐器 - 纯dlib实现
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

    def detect_faces(self, image: np.ndarray) -> List[dlib.rectangle]:
        """
        使用dlib检测人脸
        Args:
            image: 输入图像
        Returns:
            检测到的人脸区域列表
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 确保图像格式正确 - dlib需要连续的内存布局
        if gray.dtype != np.uint8:
            gray = gray.astype(np.uint8)
        
        # 确保内存是连续的
        if not gray.flags['C_CONTIGUOUS']:
            gray = np.ascontiguousarray(gray)
        
        # 确保数组是可写的
        if not gray.flags['WRITEABLE']:
            gray = gray.copy()
        
        # 使用dlib检测人脸
        try:
            faces = self.detector(gray, 1)  # 添加upsampling参数
            logger.debug(f"dlib检测到 {len(faces)} 个人脸")
            return faces
        except RuntimeError as e:
            logger.error(f"dlib检测人脸时出错: {e}")
            logger.info("尝试使用RGB图像...")
            # 尝试使用RGB图像
            try:
                if len(image.shape) == 3:
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    rgb = np.ascontiguousarray(rgb)
                    faces = self.detector(rgb, 1)
                    logger.debug(f"使用RGB图像，dlib检测到 {len(faces)} 个人脸")
                    return faces
                else:
                    return []
            except Exception as e2:
                logger.error(f"RGB图像检测也失败: {e2}")
                return []
    
    def get_landmarks(self, image: np.ndarray, face_rect: dlib.rectangle) -> np.ndarray:
        """
        获取68个人脸关键点
        Args:
            image: 输入图像
            face_rect: 人脸区域
        Returns:
            68个关键点坐标 (68, 2)
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 确保图像格式正确 - dlib需要连续的内存布局
        if gray.dtype != np.uint8:
            gray = gray.astype(np.uint8)
        
        # 确保内存是连续的
        if not gray.flags['C_CONTIGUOUS']:
            gray = np.ascontiguousarray(gray)
        
        # 确保数组是可写的
        if not gray.flags['WRITEABLE']:
            gray = gray.copy()
        
        # 获取关键点
        try:
            landmarks = self.predictor(gray, face_rect)
        except RuntimeError as e:
            logger.error(f"dlib获取关键点时出错: {e}")
            logger.info("尝试使用RGB图像...")
            # 尝试使用RGB图像
            if len(image.shape) == 3:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                rgb = np.ascontiguousarray(rgb)
                landmarks = self.predictor(rgb, face_rect)
            else:
                raise
        
        # 转换为numpy数组
        coords = np.zeros((68, 2), dtype=np.float32)
        for i in range(68):
            coords[i] = (landmarks.part(i).x, landmarks.part(i).y)
        
        return coords
    
    def get_key_points(self, landmarks: np.ndarray) -> np.ndarray:
        """
        从68个关键点中提取关键的5个点（双眼、鼻尖、嘴角）
        Args:
            landmarks: 68个人脸关键点
        Returns:
            5个关键点坐标
        """
        # 左眼中心（点36-41的平均值）
        left_eye = np.mean(landmarks[36:42], axis=0)
        # 右眼中心（点42-47的平均值）
        right_eye = np.mean(landmarks[42:48], axis=0)
        # 鼻尖（点30）
        nose_tip = landmarks[30]
        # 左嘴角（点48）
        mouth_left = landmarks[48]
        # 右嘴角（点54）
        mouth_right = landmarks[54]
        
        return np.array([left_eye, right_eye, nose_tip, mouth_left, mouth_right], dtype=np.float32)

    def align_face(self, image: np.ndarray, output_size: Tuple[int, int] = None, keep_original_size: bool = True) -> Optional[np.ndarray]:
        """
        使用dlib进行人脸对齐
        Args:
            image: 输入图像
            output_size: 输出图像大小，如果为None且keep_original_size=True则使用原始尺寸
            keep_original_size: 是否保持原始图像尺寸
        Returns:
            对齐后的人脸图像，如果检测失败返回None
        """
        # 检测人脸
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            logger.warning("未检测到人脸")
            return None
        
        if len(faces) > 1:
            logger.warning(f"检测到{len(faces)}个人脸，使用最大的人脸")
            # 选择最大的人脸
            faces = [max(faces, key=lambda face: face.width() * face.height())]
        
        face = faces[0]
        
        # 获取68个关键点
        landmarks = self.get_landmarks(image, face)
        
        # 提取5个关键点
        key_points = self.get_key_points(landmarks)
        
        # 确定输出尺寸
        if keep_original_size and output_size is None:
            output_size = (image.shape[1], image.shape[0])  # (width, height)
        elif output_size is None:
            output_size = (256, 256)  # 默认尺寸
        
        if keep_original_size:
            # 保持原始尺寸时，使用更精确的对齐方法
            # 计算眼睛中心
            left_eye = key_points[0]
            right_eye = key_points[1]
            eye_center = ((left_eye[0] + right_eye[0]) / 2, (left_eye[1] + right_eye[1]) / 2)
            
            # 计算旋转角度
            dy = float(right_eye[1] - left_eye[1])
            dx = float(right_eye[0] - left_eye[0])
            angle = float(np.degrees(np.arctan2(dy, dx)))
            
            # 创建旋转矩阵（不缩放，scale=1.0）
            transform_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
            
            # 调整平移，使眼睛在理想位置
            desired_eye_x = output_size[0] * 0.5  # 水平居中
            desired_eye_y = output_size[1] * 0.4  # 眼睛在上部
            
            transform_matrix[0, 2] += (desired_eye_x - eye_center[0])
            transform_matrix[1, 2] += (desired_eye_y - eye_center[1])
        else:
            # 标准的缩放对齐方法
            # 计算目标关键点在输出图像中的位置
            target_landmarks = self.template_landmarks * np.array([output_size[0], output_size[1]])
            
            # 计算仿射变换矩阵
            transform_matrix = cv2.estimateAffinePartial2D(key_points, target_landmarks)[0]
        
        # 应用仿射变换
        aligned_face = cv2.warpAffine(image, transform_matrix, output_size)
        
        return aligned_face

    def process_folder(self, input_folder: str, output_folder: str, output_size: Tuple[int, int] = None, keep_original_size: bool = True):
        """
        处理文件夹中的所有图片
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
        image_files = [p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() in image_extensions]
        
        if not image_files:
            logger.error(f"在文件夹 {input_folder} 中未找到图片文件")
            return
        
        logger.info(f"找到 {len(image_files)} 张图片，开始处理...")
        
        success_count = 0
        
        for i, image_file in enumerate(image_files, 1):
            logger.info(f"处理第 {i}/{len(image_files)} 张图片: {image_file.name}")
            
            try:
                # 读取图像
                image = cv2.imread(str(image_file))
                if image is None:
                    logger.error(f"无法读取图片: {image_file}")
                    continue
                
                # 对齐人脸
                aligned_face = self.align_face(image, output_size, keep_original_size)
                
                if aligned_face is not None:
                    # 保存结果
                    output_file = output_path / image_file.name
                    cv2.imwrite(str(output_file), aligned_face)
                    success_count += 1
                    logger.info(f"成功保存: {output_file}")
                else:
                    logger.warning(f"人脸对齐失败: {image_file.name}")
                    
            except Exception as e:
                logger.error(f"处理图片时出错 {image_file}: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"处理完成！成功对齐 {success_count}/{len(image_files)} 张图片")

def main():
    parser = argparse.ArgumentParser(description='TickTock人脸对齐工具 - 纯dlib版本')
    parser.add_argument('--input', '-i', type=str, default='Everyday', help='输入文件夹路径')
    parser.add_argument('--output', '-o', type=str, default='Everyday_align_dlib', help='输出文件夹路径')
    parser.add_argument('--size', '-s', type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'),
                      help='输出图像尺寸 (宽度 高度)')
    parser.add_argument('--keep-original-size', action='store_true', 
                      help='保持原始图像尺寸（忽略--size参数）')
    parser.add_argument('--predictor', '-p', type=str, 
                      default="shape_predictor_68_face_landmarks.dat",
                      help='dlib 68点关键点预测器模型路径')
    
    args = parser.parse_args()
    
    try:
        # 创建人脸对齐器
        aligner = FaceAligner(args.predictor)
        
        # 处理图片
        output_size = tuple(args.size) if args.size else None
        aligner.process_folder(args.input, args.output, output_size, args.keep_original_size)
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()