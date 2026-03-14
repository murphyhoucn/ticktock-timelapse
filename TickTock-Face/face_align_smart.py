#!/usr/bin/env python3
"""
智能人脸对齐工具 - 自动处理dlib兼容性问题
优先使用dlib进行高精度对齐，如果失败则自动切换到OpenCV方法
"""

import cv2
import os
import numpy as np
from pathlib import Path
import argparse
from typing import List, Tuple, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入dlib相关模块
try:
    import dlib
    from imutils import face_utils
    DLIB_AVAILABLE = True
    logger.info("✅ dlib 可用")
except ImportError as e:
    DLIB_AVAILABLE = False
    logger.warning(f"⚠️  dlib 不可用: {e}")

class SmartFaceAligner:
    """智能人脸对齐器 - 自动选择最佳方法"""
    
    def __init__(self, predictor_path: Optional[str] = None):
        """
        初始化人脸对齐器
        Args:
            predictor_path: dlib人脸关键点检测器路径
        """
        self.dlib_working = False
        self.opencv_face_cascade = None
        self.opencv_eye_cascade = None
        
        # 尝试初始化dlib
        if DLIB_AVAILABLE:
            try:
                self.detector = dlib.get_frontal_face_detector()
                
                if predictor_path is None:
                    predictor_path = "shape_predictor_68_face_landmarks.dat"
                
                if os.path.exists(predictor_path):
                    self.predictor = dlib.shape_predictor(predictor_path)
                    
                    # 测试dlib是否真正可用
                    test_image = np.zeros((100, 100), dtype=np.uint8)
                    test_faces = self.detector(test_image)
                    
                    self.dlib_working = True
                    logger.info("✅ dlib 人脸检测器初始化成功")
                else:
                    logger.warning(f"⚠️  dlib模型文件不存在: {predictor_path}")
                    
            except Exception as e:
                logger.warning(f"⚠️  dlib 初始化失败: {e}")
        
        # 初始化OpenCV检测器（备选方案）
        try:
            self.opencv_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.opencv_eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            logger.info("✅ OpenCV 人脸检测器初始化成功")
        except Exception as e:
            logger.error(f"❌ OpenCV 检测器初始化失败: {e}")
            raise RuntimeError("无法初始化任何人脸检测器")
        
        # 定义基准人脸关键点（正面人脸的理想位置）
        self.template_landmarks = np.array([
            [0.31556875000000000, 0.4615741071428571],  # 左眼
            [0.68262291666666670, 0.4615741071428571],  # 右眼
            [0.50026249999999990, 0.6405053571428571],  # 鼻尖
            [0.34947187500000004, 0.8246919642857142],  # 左嘴角
            [0.65343645833333330, 0.8246919642857142]   # 右嘴角
        ], dtype=np.float32)
    
    def _prepare_image_for_dlib(self, image: np.ndarray) -> np.ndarray:
        """
        为dlib准备图像格式
        Args:
            image: 输入图像
        Returns:
            处理后的灰度图像
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            if image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 确保数据类型和内存布局正确
        gray = np.array(gray, dtype=np.uint8, order='C')
        
        return gray
    
    def detect_faces_dlib(self, image: np.ndarray) -> List:
        """
        使用dlib检测人脸
        Args:
            image: 输入图像
        Returns:
            人脸区域列表
        """
        if not self.dlib_working:
            return []
        
        try:
            gray = self._prepare_image_for_dlib(image)
            faces = self.detector(gray)
            return faces
        except Exception as e:
            logger.debug(f"dlib人脸检测失败: {e}")
            return []
    
    def detect_faces_opencv(self, image: np.ndarray) -> List:
        """
        使用OpenCV检测人脸
        Args:
            image: 输入图像
        Returns:
            人脸区域列表（转换为dlib格式）
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            faces_opencv = self.opencv_face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # 转换为类似dlib的格式
            faces_dlib_format = []
            for (x, y, w, h) in faces_opencv:
                # 创建一个简单的矩形对象
                class Rectangle:
                    def __init__(self, x, y, w, h):
                        self.x, self.y, self.w, self.h = x, y, w, h
                    def left(self): return self.x
                    def top(self): return self.y
                    def right(self): return self.x + self.w
                    def bottom(self): return self.y + self.h
                    def width(self): return self.w
                    def height(self): return self.h
                
                face_rect = Rectangle(x, y, w, h)
                faces_dlib_format.append(face_rect)
            
            return faces_dlib_format
        except Exception as e:
            logger.error(f"OpenCV人脸检测失败: {e}")
            return []
    
    def detect_faces(self, image: np.ndarray) -> List:
        """
        智能人脸检测 - 优先使用dlib，失败则使用OpenCV
        Args:
            image: 输入图像
        Returns:
            人脸区域列表
        """
        # 首先尝试dlib
        faces = self.detect_faces_dlib(image)
        
        if len(faces) > 0:
            logger.debug(f"dlib检测到 {len(faces)} 个人脸")
            return faces
        
        # dlib失败，使用OpenCV
        faces = self.detect_faces_opencv(image)
        if len(faces) > 0:
            logger.debug(f"OpenCV检测到 {len(faces)} 个人脸")
        
        return faces
    
    def get_landmarks_dlib(self, image: np.ndarray, face_rect) -> Optional[np.ndarray]:
        """
        使用dlib获取人脸关键点
        Args:
            image: 输入图像
            face_rect: 人脸区域
        Returns:
            68个关键点坐标或None
        """
        if not self.dlib_working:
            return None
        
        try:
            gray = self._prepare_image_for_dlib(image)
            landmarks = self.predictor(gray, face_rect)
            landmarks = face_utils.shape_to_np(landmarks)
            return landmarks
        except Exception as e:
            logger.debug(f"dlib关键点检测失败: {e}")
            return None
    
    def get_landmarks_opencv(self, image: np.ndarray, face_rect) -> np.ndarray:
        """
        使用OpenCV估算人脸关键点
        Args:
            image: 输入图像
            face_rect: 人脸区域
        Returns:
            68个估算的关键点坐标
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        x, y, w, h = face_rect.left(), face_rect.top(), face_rect.width(), face_rect.height()
        
        # 在人脸区域内检测眼睛
        face_roi = gray[y:y+h, x:x+w]
        eyes = self.opencv_eye_cascade.detectMultiScale(face_roi, 1.1, 3)
        
        # 创建68个关键点
        landmarks = np.zeros((68, 2), dtype=np.float32)
        
        if len(eyes) >= 2:
            # 使用检测到的眼睛位置
            eyes = sorted(eyes, key=lambda e: e[0])  # 按x坐标排序
            left_eye = eyes[0]
            right_eye = eyes[1] if len(eyes) > 1 else eyes[0]
            
            # 转换回原图坐标
            left_eye_center = (x + left_eye[0] + left_eye[2]//2, y + left_eye[1] + left_eye[3]//2)
            right_eye_center = (x + right_eye[0] + right_eye[2]//2, y + right_eye[1] + right_eye[3]//2)
        else:
            # 使用估算的眼睛位置
            left_eye_center = (x + int(w * 0.3), y + int(h * 0.4))
            right_eye_center = (x + int(w * 0.7), y + int(h * 0.4))
        
        # 设置主要关键点
        landmarks[36:42] = [left_eye_center] * 6  # 左眼区域
        landmarks[42:48] = [right_eye_center] * 6  # 右眼区域
        landmarks[30] = [x + w//2, y + int(h * 0.6)]  # 鼻尖
        landmarks[48] = [x + int(w * 0.35), y + int(h * 0.8)]  # 左嘴角
        landmarks[54] = [x + int(w * 0.65), y + int(h * 0.8)]  # 右嘴角
        
        # 填充其他关键点（简化处理）
        for i in range(68):
            if np.array_equal(landmarks[i], [0, 0]):
                landmarks[i] = [x + w//2, y + h//2]
        
        return landmarks
    
    def get_landmarks(self, image: np.ndarray, face_rect) -> np.ndarray:
        """
        智能获取人脸关键点 - 优先使用dlib，失败则使用OpenCV估算
        Args:
            image: 输入图像
            face_rect: 人脸区域
        Returns:
            68个关键点坐标
        """
        # 首先尝试dlib
        landmarks = self.get_landmarks_dlib(image, face_rect)
        
        if landmarks is not None:
            logger.debug("使用dlib获取的68个关键点")
            return landmarks
        
        # dlib失败，使用OpenCV估算
        landmarks = self.get_landmarks_opencv(image, face_rect)
        logger.debug("使用OpenCV估算的68个关键点")
        return landmarks
    
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
        对齐人脸
        Args:
            image: 输入图像
            output_size: 输出图像大小，如果为None且keep_original_size=True则使用原始尺寸
            keep_original_size: 是否保持原始图像尺寸
        Returns:
            对齐后的人脸图像，如果检测失败返回None
        """
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            logger.warning("未检测到人脸")
            return None
        
        if len(faces) > 1:
            logger.warning(f"检测到{len(faces)}个人脸，使用最大的人脸")
            # 选择最大的人脸
            faces = [max(faces, key=lambda face: face.width() * face.height())]
        
        face = faces[0]
        landmarks = self.get_landmarks(image, face)
        key_points = self.get_key_points(landmarks)
        
        # 如果要保持原始尺寸，使用输入图像的尺寸
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
            dy = right_eye[1] - left_eye[1]
            dx = right_eye[0] - left_eye[0]
            angle = np.degrees(np.arctan2(dy, dx))
            
            # 创建旋转矩阵（不缩放，scale=1.0）
            transform_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
            
            # 调整平移，使眼睛在理想位置
            desired_eye_x = output_size[0] * 0.5  # 水平居中
            desired_eye_y = output_size[1] * 0.4  # 眼睛在上部
            
            transform_matrix[0, 2] += (desired_eye_x - eye_center[0])
            transform_matrix[1, 2] += (desired_eye_y - eye_center[1])
        else:
            # 缩放对齐方法
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
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            output_size: 输出图像大小，如果为None且keep_original_size=True则保持原始尺寸
            keep_original_size: 是否保持原始图像尺寸
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            logger.error(f"输入文件夹不存在: {input_folder}")
            return
        
        # 创建输出文件夹
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
        
        # 按文件名排序
        image_files.sort()
        
        logger.info(f"找到 {len(image_files)} 张图片，开始处理...")
        method_used = "智能混合模式 (dlib + OpenCV备选)"
        logger.info(f"使用检测方法: {method_used}")
        
        success_count = 0
        for i, image_file in enumerate(image_files):
            logger.info(f"处理第 {i+1}/{len(image_files)} 张图片: {image_file.name}")
            
            try:
                # 读取图片
                image = cv2.imread(str(image_file), cv2.IMREAD_COLOR)
                if image is None:
                    logger.warning(f"无法读取图片: {image_file}")
                    continue
                
                # 确保图片格式正确
                if image.dtype != np.uint8:
                    if image.dtype == np.uint16:
                        image = (image / 256).astype(np.uint8)
                    else:
                        image = cv2.convertScaleAbs(image)
                
                # 检查图片尺寸
                if image.shape[0] == 0 or image.shape[1] == 0:
                    logger.warning(f"图片尺寸无效: {image_file}")
                    continue
                
                logger.debug(f"图片信息: {image_file.name} - 尺寸: {image.shape}, 类型: {image.dtype}")
                
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
    parser = argparse.ArgumentParser(description='智能人脸对齐工具 - 自动处理dlib兼容性问题')
    parser.add_argument('--input', '-i', default='Everyday',
                       help='输入文件夹路径 (默认: Everyday)')
    parser.add_argument('--output', '-o', default='Everyday_align_smart',
                       help='输出文件夹路径 (默认: Everyday_align_smart)')
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
        # 创建智能人脸对齐器
        aligner = SmartFaceAligner()
        
        # 处理图片
        aligner.process_folder(args.input, args.output, output_size, keep_original_size)
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()