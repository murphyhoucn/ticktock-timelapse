#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeLapse@Desk Demo (优化版 + 水印功能)
自动拍照和人脸对齐处理的演示程序 - 针对速度进行了优化，增加了水印功能
"""

import cv2
import numpy as np
import os
from datetime import datetime
import mediapipe as mp
import argparse

class TimeLapseCamera:
    def __init__(self, output_dir="photos", aligned_dir="aligned_photos"):
        """
        初始化TimeLapse相机
        
        Args:
            output_dir: 原始照片保存目录
            aligned_dir: 对齐后照片保存目录
        """
        self.output_dir = output_dir
        self.aligned_dir = aligned_dir
        
        # 创建保存目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(aligned_dir, exist_ok=True)
        
        # MediaPipe相关变量（延迟初始化以提高启动速度）
        self.mp_face_detection = None
        self.mp_face_mesh = None
        self.mp_drawing = None
        self.face_detection = None
        self.face_mesh = None
        self._mediapipe_initialized = False
    
    def _init_mediapipe(self):
        """
        延迟初始化MediaPipe（只有在需要人脸检测时才初始化）
        """
        if not self._mediapipe_initialized:
            print("正在初始化人脸检测模型...")
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            
            # 初始化人脸检测器
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5)
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5)
            
            self._mediapipe_initialized = True
            print("人脸检测模型初始化完成")
    
    def _add_watermark(self, image, timestamp, alpha=0.7):
        """
        在图像右下角添加半透明水印
        
        Args:
            image: 输入图像
            timestamp: 时间戳字符串
            alpha: 透明度 (0.0-1.0，0为完全透明，1为完全不透明)
            
        Returns:
            numpy.ndarray: 添加水印后的图像
        """
        # 复制图像以避免修改原图
        watermarked_image = image.copy()
        
        # 水印文本 - 使用稳定的版权标记
        copyright_text = "Copyright Murphy" 
        time_text = timestamp
        
        # 字体设置 - 使用更清晰的字体
        font = cv2.FONT_HERSHEY_DUPLEX  # 更接近Consolas的等宽字体效果
        font_scale = 0.6
        thickness = 1
        color = (255, 255, 255)  # 白色
        
        # 获取图像尺寸
        height, width = watermarked_image.shape[:2]
        
        # 计算文本尺寸
        (copyright_w, copyright_h), _ = cv2.getTextSize(copyright_text, font, font_scale, thickness)
        (time_w, time_h), _ = cv2.getTextSize(time_text, font, font_scale, thickness)
        
        # 设置水印位置（距离边界有一定距离）
        margin_right = 30  # 距离右边界
        margin_bottom = 30  # 距离下边界
        line_spacing = 8   # 行间距
        
        copyright_x = width - copyright_w - margin_right
        copyright_y = height - time_h - margin_bottom - line_spacing
        time_x = width - time_w - margin_right  
        time_y = height - margin_bottom
        
        # 创建透明层
        overlay = watermarked_image.copy()
        
        # 在透明层上绘制文字（无描边，清晰效果）
        cv2.putText(overlay, copyright_text, (copyright_x, copyright_y), 
                   font, font_scale, color, thickness, cv2.LINE_AA)
        cv2.putText(overlay, time_text, (time_x, time_y), 
                   font, font_scale, color, thickness, cv2.LINE_AA)
        
        # 使用alpha混合实现透明效果
        cv2.addWeighted(overlay, alpha, watermarked_image, 1 - alpha, 0, watermarked_image)
        
        return watermarked_image
    
    def _display_camera_settings(self, cap):
        """
        显示摄像头实际设置的参数
        """
        print("摄像头当前设置:")
        print(f"  分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        print(f"  帧率: {cap.get(cv2.CAP_PROP_FPS):.1f} FPS")
        print(f"  亮度: {cap.get(cv2.CAP_PROP_BRIGHTNESS):.2f}")
        print(f"  对比度: {cap.get(cv2.CAP_PROP_CONTRAST):.2f}")
        print(f"  饱和度: {cap.get(cv2.CAP_PROP_SATURATION):.2f}")
        print(f"  锐度: {cap.get(cv2.CAP_PROP_SHARPNESS):.2f}")
        print(f"  曝光: {cap.get(cv2.CAP_PROP_EXPOSURE):.2f}")
        print(f"  增益: {cap.get(cv2.CAP_PROP_GAIN):.2f}")
        print(f"  自动对焦: {'开启' if cap.get(cv2.CAP_PROP_AUTOFOCUS) else '关闭'}")
        print(f"  自动白平衡: {'开启' if cap.get(cv2.CAP_PROP_AUTO_WB) else '关闭'}")
    
    def capture_photo(self, camera_index=0):
        """
        拍摄照片（优化版）
        
        Args:
            camera_index: 摄像头索引，默认为0
            
        Returns:
            tuple: (成功标志, 照片数组, 文件名)
        """
        try:
            print("正在初始化摄像头...")
            # 初始化摄像头
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                print("错误：无法打开摄像头")
                return False, None, None
            
            # 设置摄像头参数（最大化图像质量）
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # 最大分辨率
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)       # 减少缓冲区延迟
            cap.set(cv2.CAP_PROP_FPS, 30)             # 适中帧率
            
            # 图像质量优化设置（针对你的摄像头特点优化）
            # 只设置摄像头实际支持的参数
            try:
                cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)     # 保持默认亮度
                cap.set(cv2.CAP_PROP_CONTRAST, 140)       # 稍微提高对比度
                cap.set(cv2.CAP_PROP_SATURATION, 145)     # 稍微提高饱和度
                cap.set(cv2.CAP_PROP_SHARPNESS, 140)      # 提高锐度
            except:
                print("某些图像参数设置失败，使用默认值")
            
            # 尝试启用自动功能（如果支持的话）
            try:
                cap.set(cv2.CAP_PROP_AUTO_WB, 1)          # 尝试启用自动白平衡
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)        # 尝试启用自动对焦
            except:
                pass  # 如果不支持就忽略
            
            print("摄像头参数设置完成，正在优化图像质量...")
            
            # 显示实际设置的参数
            self._display_camera_settings(cap)
            
            print("摄像头预热中...")
            # 预热摄像头，让相机调整到最佳状态（提高照片质量）
            for i in range(10):  # 增加预热帧数，让相机充分调整
                ret, frame = cap.read()
                if not ret:
                    print(f"预热第{i+1}帧失败")
                    break
                # 显示预热进度
                if (i + 1) % 3 == 0:
                    print(f"预热中... {i+1}/10")
            
            # 额外等待，让自动对焦和曝光稳定
            import time
            time.sleep(1)  # 等待1秒让相机稳定
            
            print("正在拍摄...")
            # 拍摄最终照片
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                print("错误：无法拍摄照片")
                return False, None, None
            
            # 生成文件名（基于当前时间）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            # 添加水印
            watermark_time = datetime.now().strftime("%Y/%m/%d %H:%M")
            watermark_time_place = watermark_time + " Xi'An"
            watermarked_frame = self._add_watermark(frame, watermark_time_place)
            
            # 保存带水印的原始照片
            cv2.imwrite(filepath, watermarked_frame)
            print(f"照片已保存: {filepath}")
            
            # 返回无水印的原始图像供后续对齐处理使用
            return True, frame, filename
            
        except Exception as e:
            print(f"拍照过程中出现错误: {e}")
            return False, None, None
    
    def detect_face_landmarks(self, image):
        """
        检测人脸关键点
        
        Args:
            image: 输入图像
            
        Returns:
            dict: 包含关键点信息的字典
        """
        # 确保MediaPipe已初始化
        self._init_mediapipe()
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            return None
        
        # 获取第一个检测到的人脸
        face_landmarks = results.multi_face_landmarks[0]
        
        # 转换关键点坐标
        h, w, _ = image.shape
        landmarks = []
        for landmark in face_landmarks.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            landmarks.append((x, y))
        
        # 获取重要的关键点
        # 眼睛关键点
        left_eye = landmarks[33]   # 左眼
        right_eye = landmarks[263] # 右眼
        # 鼻尖
        nose_tip = landmarks[1]
        # 嘴角
        mouth_left = landmarks[61]
        mouth_right = landmarks[291]
        
        return {
            'all_landmarks': landmarks,
            'left_eye': left_eye,
            'right_eye': right_eye,
            'nose_tip': nose_tip,
            'mouth_left': mouth_left,
            'mouth_right': mouth_right
        }
    
    def align_face(self, image, landmarks, target_size=(1920, 1080)):
        """
        对齐人脸到固定位置（不缩放，只平移和旋转）
        
        Args:
            image: 输入图像
            landmarks: 人脸关键点
            target_size: 目标图像尺寸，默认1920*1080
            
        Returns:
            numpy.ndarray: 对齐后的图像
        """
        if landmarks is None:
            return None
        
        # 获取关键点
        left_eye = np.array(landmarks['left_eye'])
        right_eye = np.array(landmarks['right_eye'])
        nose_tip = np.array(landmarks['nose_tip'])
        
        # 计算眼睛中心点
        eye_center = (left_eye + right_eye) / 2
        
        # 计算眼睛之间的角度（用于旋转对齐）
        eye_vector = right_eye - left_eye
        angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
        
        # 定义固定的目标位置（关键点应该对齐到的位置）
        target_eye_center = np.array([target_size[0] / 2, target_size[1] * 0.4])  # 眼睛中心在图像上部40%处
        
        # 创建变换矩阵：只旋转，不缩放（scale=1.0）
        rotation_matrix = cv2.getRotationMatrix2D(tuple(eye_center), angle, 1.0)
        
        # 计算平移量，将眼睛中心移动到目标位置
        tx = target_eye_center[0] - eye_center[0]
        ty = target_eye_center[1] - eye_center[1]
        rotation_matrix[0, 2] += tx
        rotation_matrix[1, 2] += ty
        
        # 应用变换，超出部分裁切，空白部分填充黑色
        aligned_image = cv2.warpAffine(
            image, 
            rotation_matrix, 
            target_size,
            borderMode=cv2.BORDER_CONSTANT,  # 边界填充模式
            borderValue=(0, 0, 0)            # 黑色填充
        )
        
        return aligned_image
    
    def process_photo(self, image, filename):
        """
        处理照片：检测人脸并对齐
        
        Args:
            image: 输入图像
            filename: 文件名
            
        Returns:
            bool: 处理成功标志
        """
        try:
            # 检测人脸关键点
            landmarks = self.detect_face_landmarks(image)
            
            if landmarks is None:
                print("警告：未检测到人脸，跳过对齐处理")
                return False
            
            # 对齐人脸
            aligned_image = self.align_face(image, landmarks)
            
            if aligned_image is None:
                print("警告：人脸对齐失败")
                return False
            
            # 从文件名提取时间戳并格式化为水印格式
            timestamp_str = filename.replace("photo_", "").replace(".jpg", "")
            try:
                # 解析时间戳 20250926_143022 -> 2025/09/26 14:30
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                watermark_time = dt.strftime("%Y/%m/%d %H:%M")
            except:
                # 如果解析失败，使用当前时间
                watermark_time = datetime.now().strftime("%Y/%m/%d %H:%M")
            
            # 添加地点信息到时间部分
            watermark_time_place = watermark_time + " Xi'An"
            
            # 为对齐图像添加水印
            watermarked_aligned = self._add_watermark(aligned_image, watermark_time_place)
            
            # 保存带水印的对齐后图像
            aligned_filename = f"aligned_{filename}"
            aligned_filepath = os.path.join(self.aligned_dir, aligned_filename)
            cv2.imwrite(aligned_filepath, watermarked_aligned)
            print(f"对齐照片已保存: {aligned_filepath}")
            
            return True
            
        except Exception as e:
            print(f"处理照片时出现错误: {e}")
            return False
    
    def take_daily_photo(self):
        """
        执行每日拍照流程（自动化完整流程）
        """
        print("=== TimeLapse@Desk 自动拍照对齐 ===")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 拍摄照片
        print("正在拍摄照片...")
        success, image, filename = self.capture_photo()
        
        if not success:
            print("拍照失败，程序退出")
            return False
        
        # 2. 自动进行人脸对齐处理
        print("正在进行人脸对齐...")
        process_success = self.process_photo(image, filename)
        
        if process_success:
            print("✅ 拍照和对齐完成！")
        else:
            print("⚠️ 人脸对齐失败，但原始照片已保存")
        
        print(f"📁 原始照片: {self.output_dir}")
        print(f"📁 对齐照片: {self.aligned_dir}")
        
        return True

def main():
    """主函数 - 自动化拍照对齐流程"""
    parser = argparse.ArgumentParser(description='TimeLapse@Desk 自动拍照对齐程序')
    parser.add_argument('--camera', type=int, default=0, help='摄像头索引 (默认: 0)')
    parser.add_argument('--output', type=str, default='photos', help='原始照片保存目录')
    parser.add_argument('--aligned', type=str, default='aligned_photos', help='对齐照片保存目录')
    
    args = parser.parse_args()
    
    # 创建TimeLapse相机实例
    camera = TimeLapseCamera(args.output, args.aligned)
    
    # 执行自动化拍照对齐流程
    camera.take_daily_photo()

if __name__ == "__main__":
    main()