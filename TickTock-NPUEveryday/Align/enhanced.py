#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TickTock-Enhanced-Align-NPU Library

这个增强版对齐库专门针对日夜混合的图像序列进行优化。
解决了传统SIFT算法在夜间照片上效果不佳的问题。

功能特点:
- 自动检测日夜图像并采用不同策略
- 夜间图像使用增强预处理 + 多种特征检测器组合
- 白天图像使用优化的SIFT算法
- 支持模板匹配作为后备方案
- 渐进式对齐策略
"""

import cv2
import numpy as np
import os
import glob
from pathlib import Path
import logging
from typing import Tuple, List, Optional
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedAlign:
    """
    增强版 TickTock-Align-NPU 图像对齐类
    
    专门优化处理日夜混合的建筑物图像序列，确保夜间照片也能获得良好的对齐效果。
    """
    
    def __init__(self, input_dir="Lib", output_dir="Enhanced-Align", reference_index=0):
        """
        初始化增强版对齐器
        
        Args:
            input_dir (str): 输入图像文件夹路径
            output_dir (str): 输出对齐图像文件夹路径
            reference_index (int): 参考图像索引（默认为0，即第一张图像）
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.reference_index = reference_index
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 支持的图像格式
        self.supported_formats = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
        
        # 日夜判断阈值
        self.night_threshold = 80  # 平均亮度低于此值认为是夜间图像
        
        # 特征检测器参数
        self.init_feature_detectors()
        
    def init_feature_detectors(self):
        """初始化多种特征检测器"""
        # SIFT检测器 - 适用于白天图像
        self.sift = cv2.SIFT_create(nfeatures=1000, contrastThreshold=0.04, edgeThreshold=10)
        
        # ORB检测器 - 对光照变化鲁棒
        self.orb = cv2.ORB_create(nfeatures=1500, scaleFactor=1.2, nlevels=8)
        
        # AKAZE检测器 - 对噪声鲁棒
        self.akaze = cv2.AKAZE_create()
        
        # BRISK检测器 - 快速且鲁棒
        self.brisk = cv2.BRISK_create()
        
    def get_image_files(self):
        """获取输入目录中的所有图像文件（递归搜索子目录）"""
        image_files = []
        
        # 使用pathlib的rglob进行递归搜索
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        for ext in image_extensions:
            # 搜索小写扩展名
            image_files.extend(list(self.input_dir.rglob(f"*{ext}")))
            # 搜索大写扩展名
            image_files.extend(list(self.input_dir.rglob(f"*{ext.upper()}")))
        
        # 转换为字符串路径并去重
        image_files = list(set([str(f) for f in image_files]))
        
        # 按文件名排序
        image_files.sort()
        return image_files
    
    def is_night_image(self, img) -> bool:
        """
        判断图像是否为夜间拍摄
        
        Args:
            img: 输入图像
            
        Returns:
            bool: True表示夜间图像，False表示白天图像
        """
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 计算平均亮度
        mean_brightness = np.mean(gray)
        
        # 计算亮度方差（夜间图像通常对比度更高）
        brightness_std = np.std(gray)
        
        # 综合判断：平均亮度低且方差大的图像可能是夜间图像
        is_night = mean_brightness < self.night_threshold
        
        logger.debug(f"图像亮度分析 - 平均值: {mean_brightness:.2f}, 标准差: {brightness_std:.2f}, 判定: {'夜间' if is_night else '白天'}")
        
        return is_night
    
    def enhance_night_image(self, img):
        """
        增强夜间图像以提高特征检测效果
        
        Args:
            img: 输入夜间图像
            
        Returns:
            enhanced_img: 增强后的图像
        """
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # 1. 直方图均衡化
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 2. 伽马校正
        gamma = 1.5  # 提亮暗部
        lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                                for i in np.arange(0, 256)]).astype("uint8")
        enhanced = cv2.LUT(enhanced, lookup_table)
        
        # 3. 双边滤波去噪
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # 4. 锐化处理
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 确保值在有效范围内
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        
        return enhanced
    
    def detect_features_original_sift(self, img):
        """
        原始SIFT特征检测（来自align_lib.py）
        
        Args:
            img: 输入图像
            
        Returns:
            keypoints: 特征点
            descriptors: 特征描述符
        """
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # 创建SIFT检测器 - 保持原始设置以获取更多特征点
        sift = cv2.SIFT_create()
        
        # 检测特征点和描述符
        keypoints, descriptors = sift.detectAndCompute(gray, None)
        
        return keypoints, descriptors
    
    def match_features_original(self, desc1, desc2):
        """
        原始特征匹配方法（来自align_lib.py）
        
        Args:
            desc1: 第一幅图像的特征描述符
            desc2: 第二幅图像的特征描述符
            
        Returns:
            good_matches: 良好的匹配点对
        """
        if desc1 is None or desc2 is None:
            return []
            
        # 使用FLANN匹配器 - 保持原始设置
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(desc1, desc2, k=2)
        
        # 应用Lowe's ratio test筛选良好匹配 - 保持原始设置
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
        
        return good_matches
    
    def estimate_homography_original(self, kp1, kp2, matches):
        """
        原始单应性矩阵估计（来自align_lib.py）
        
        Args:
            kp1: 参考图像特征点
            kp2: 目标图像特征点
            matches: 匹配点对
            
        Returns:
            homography: 单应性矩阵
        """
        if len(matches) < 4:
            logger.warning("匹配点数量不足，无法计算单应性矩阵")
            return None
            
        # 提取匹配点坐标
        src_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # 使用RANSAC估计单应性矩阵 - 保持原始参数但添加质量评估
        homography, mask = cv2.findHomography(
            src_pts, dst_pts, 
            cv2.RANSAC, 
            ransacReprojThreshold=5.0
        )
        
        # 计算内点数量用于质量评估
        inliers = np.sum(mask) if mask is not None else 0
        if inliers > 0:
            logger.debug(f"单应性估计: 匹配点{len(matches)}, 内点{inliers}, 内点率{inliers/len(matches)*100:.1f}%")
        
        return homography
    
    def detect_features_adaptive(self, img, is_night=False):
        """
        自适应特征检测：根据图像类型选择最佳检测策略
        
        Args:
            img: 输入图像
            is_night: 是否为夜间图像
            
        Returns:
            keypoints: 特征点
            descriptors: 特征描述符
            detector_used: 使用的检测器名称
        """
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        if is_night:
            # 夜间图像：先增强再检测
            enhanced = self.enhance_night_image(img)
            
            # 尝试多种检测器并选择最佳结果
            detectors = [
                ("AKAZE", self.akaze),
                ("ORB", self.orb),
                ("BRISK", self.brisk),
                ("SIFT", self.sift)
            ]
            
            best_kp, best_desc, best_detector = None, None, None
            max_features = 0
            
            for detector_name, detector in detectors:
                try:
                    if detector_name in ["AKAZE", "BRISK"]:
                        kp, desc = detector.detectAndCompute(enhanced, None)
                    else:
                        kp, desc = detector.detectAndCompute(enhanced, None)
                    
                    if desc is not None and len(kp) > max_features:
                        max_features = len(kp)
                        best_kp, best_desc, best_detector = kp, desc, detector_name
                        
                except Exception as e:
                    logger.warning(f"{detector_name} 检测失败: {e}")
                    continue
            
            logger.info(f"夜间图像使用 {best_detector} 检测到 {max_features} 个特征点")
            return best_kp, best_desc, best_detector
        
        else:
            # 白天图像：使用优化的SIFT
            kp, desc = self.sift.detectAndCompute(gray, None)
            feature_count = len(kp) if kp else 0
            logger.info(f"白天图像使用 SIFT 检测到 {feature_count} 个特征点")
            return kp, desc, "SIFT"
    
    def match_features_robust(self, desc1, desc2, detector1, detector2):
        """
        鲁棒的特征匹配：根据检测器类型选择合适的匹配策略
        
        Args:
            desc1: 第一幅图像的特征描述符
            desc2: 第二幅图像的特征描述符
            detector1: 第一幅图像使用的检测器
            detector2: 第二幅图像使用的检测器
            
        Returns:
            good_matches: 良好的匹配点对
        """
        if desc1 is None or desc2 is None:
            return []
        
        # 检查描述符类型是否兼容
        binary_detectors = ["ORB", "AKAZE", "BRISK"]
        float_detectors = ["SIFT"]
        
        detector1_is_binary = detector1 in binary_detectors
        detector2_is_binary = detector2 in binary_detectors
        
        # 如果描述符类型不匹配，返回空匹配（稍后使用模板匹配）
        if detector1_is_binary != detector2_is_binary:
            logger.warning(f"描述符类型不匹配: {detector1} vs {detector2}，将使用模板匹配")
            return []
        
        try:
            # 根据检测器类型选择匹配方法
            if detector1_is_binary and detector2_is_binary:
                # 两个都是二进制描述符，使用汉明距离
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
                matches = bf.knnMatch(desc1, desc2, k=2)
            else:
                # 两个都是浮点描述符，使用欧几里得距离和FLANN
                FLANN_INDEX_KDTREE = 1
                index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                search_params = dict(checks=50)
                
                flann = cv2.FlannBasedMatcher(index_params, search_params)
                matches = flann.knnMatch(desc1, desc2, k=2)
            
            # 应用Lowe's ratio test筛选良好匹配
            good_matches = []
            ratio_threshold = 0.75  # 对夜间图像放宽阈值
            
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < ratio_threshold * n.distance:
                        good_matches.append(m)
            
            return good_matches
            
        except Exception as e:
            logger.warning(f"特征匹配失败: {e}，将使用模板匹配")
            return []
    
    def estimate_homography_robust(self, kp1, kp2, matches):
        """
        鲁棒的单应性矩阵估计
        
        Args:
            kp1: 参考图像特征点
            kp2: 目标图像特征点
            matches: 匹配点对
            
        Returns:
            homography: 单应性矩阵
            inliers: 内点数量
        """
        if len(matches) < 8:  # 提高最小匹配点要求
            logger.warning(f"匹配点数量不足 ({len(matches)}，需要至少8个)，无法计算单应性矩阵")
            return None, 0
            
        # 提取匹配点坐标
        src_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # 使用更严格的RANSAC参数
        homography, mask = cv2.findHomography(
            src_pts, dst_pts, 
            cv2.RANSAC, 
            ransacReprojThreshold=3.0,  # 更严格的重投影误差阈值
            maxIters=5000,  # 增加迭代次数
            confidence=0.995  # 提高置信度
        )
        
        inliers = np.sum(mask) if mask is not None else 0
        
        return homography, inliers
    
    def template_matching_fallback(self, ref_img, target_img):
        """
        模板匹配后备方案：当特征匹配失败时使用
        
        Args:
            ref_img: 参考图像
            target_img: 目标图像
            
        Returns:
            homography: 估计的单应性矩阵
        """
        # 转换为灰度图像
        if len(ref_img.shape) == 3:
            ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
        else:
            ref_gray = ref_img
            
        if len(target_img.shape) == 3:
            target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        else:
            target_gray = target_img
        
        # 使用多尺度模板匹配
        best_corr = -1
        best_translation = (0, 0)
        
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]
        
        for scale in scales:
            # 缩放目标图像
            h, w = target_gray.shape
            new_h, new_w = int(h * scale), int(w * scale)
            scaled_target = cv2.resize(target_gray, (new_w, new_h))
            
            if scaled_target.shape[0] < ref_gray.shape[0] or scaled_target.shape[1] < ref_gray.shape[1]:
                continue
                
            # 模板匹配
            result = cv2.matchTemplate(scaled_target, ref_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_corr:
                best_corr = max_val
                # 计算平移量（考虑缩放）
                best_translation = (
                    (max_loc[0] - (new_w - ref_gray.shape[1]) // 2) / scale,
                    (max_loc[1] - (new_h - ref_gray.shape[0]) // 2) / scale
                )
        
        # 构建平移矩阵
        if best_corr > 0.3:  # 相关性阈值
            homography = np.array([
                [1, 0, best_translation[0]],
                [0, 1, best_translation[1]],
                [0, 0, 1]
            ], dtype=np.float32)
            
            logger.info(f"模板匹配后备方案：相关性 {best_corr:.3f}, 平移 {best_translation}")
            return homography
        
        return None
    
    def align_image(self, img, homography, reference_shape):
        """
        使用单应性矩阵对齐图像
        
        Args:
            img: 待对齐的图像
            homography: 单应性矩阵
            reference_shape: 参考图像的形状
            
        Returns:
            aligned_img: 对齐后的图像
        """
        if homography is None:
            logger.warning("单应性矩阵为空，返回调整大小后的原图像")
            return cv2.resize(img, (reference_shape[1], reference_shape[0]))
        
        # 应用透视变换
        aligned_img = cv2.warpPerspective(
            img, homography, 
            (reference_shape[1], reference_shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
        
        return aligned_img
    
    def process_images(self):
        """
        处理所有图像进行对齐
        """
        # 获取所有图像文件
        image_files = self.get_image_files()
        
        if not image_files:
            logger.error(f"在 {self.input_dir} 中未找到图像文件")
            return False
        
        logger.info(f"找到 {len(image_files)} 张图像")
        
        # 读取参考图像
        if self.reference_index >= len(image_files):
            logger.error(f"参考图像索引 {self.reference_index} 超出范围")
            return False
            
        reference_path = image_files[self.reference_index]
        reference_img = cv2.imread(reference_path)
        
        if reference_img is None:
            logger.error(f"无法读取参考图像: {reference_path}")
            return False
        
        logger.info(f"使用参考图像: {Path(reference_path).name}")
        
        # 判断参考图像是否为夜间图像
        ref_is_night = self.is_night_image(reference_img)
        logger.info(f"参考图像类型: {'夜间' if ref_is_night else '白天'}")
        
        # 检测参考图像特征 - 始终使用原始SIFT以保证兼容性
        ref_kp, ref_desc = self.detect_features_original_sift(reference_img)
        ref_detector = "SIFT"
        
        if ref_desc is None:
            logger.error("参考图像特征检测失败")
            return
        
        logger.info(f"参考图像使用原始SIFT检测到 {len(ref_kp)} 个特征点")
        
        # 保存参考图像到输出目录
        ref_output_path = self.output_dir / Path(reference_path).name
        cv2.imwrite(str(ref_output_path), reference_img)
        logger.info(f"保存参考图像: {ref_output_path}")
        
        # 统计处理结果
        day_count = 0
        night_count = 0
        success_count = 0
        fallback_count = 0
        copy_count = 0
        
        # 处理报告数据
        processing_report = []
        
        # 处理其他图像
        for i, img_path in enumerate(image_files):
            if i == self.reference_index:
                continue  # 跳过参考图像
                
            logger.info(f"处理图像 {i+1}/{len(image_files)}: {Path(img_path).name}")
            start_time = time.time()
            
            # 读取当前图像
            current_img = cv2.imread(img_path)
            if current_img is None:
                logger.warning(f"无法读取图像: {img_path}")
                continue
            
            # 判断图像类型
            curr_is_night = self.is_night_image(current_img)
            if curr_is_night:
                night_count += 1
            else:
                day_count += 1
            
            homography = None
            processing_method = ""
            match_points = 0
            inliers = 0
            
            if curr_is_night:
                # 夜间图像：使用增强算法
                curr_kp, curr_desc, curr_detector = self.detect_features_adaptive(current_img, curr_is_night)
                
                if curr_desc is not None:
                    # 匹配特征点
                    matches = self.match_features_robust(ref_desc, curr_desc, ref_detector, curr_detector)
                    match_points = len(matches)
                    logger.info(f"夜间增强算法找到 {match_points} 个匹配点")
                    
                    # 估计单应性矩阵
                    homography, inliers = self.estimate_homography_robust(ref_kp, curr_kp, matches)
                    
                    if homography is not None:
                        processing_method = "夜间增强特征匹配"
                        logger.info(f"夜间增强算法成功，内点数量: {inliers}")
                    else:
                        logger.warning("夜间增强算法失败，尝试模板匹配")
                
                # 如果增强算法失败，使用模板匹配
                if homography is None:
                    homography = self.template_matching_fallback(reference_img, current_img)
                    if homography is not None:
                        processing_method = "夜间模板匹配"
                        fallback_count += 1
                    else:
                        processing_method = "夜间无处理(直接复制)"
                        copy_count += 1
            else:
                # 白天图像：使用原始SIFT算法
                curr_kp, curr_desc = self.detect_features_original_sift(current_img)
                
                if curr_desc is not None:
                    # 匹配特征点
                    matches = self.match_features_original(ref_desc, curr_desc)
                    match_points = len(matches)
                    logger.info(f"白天原始SIFT算法找到 {match_points} 个匹配点")
                    
                    # 估计单应性矩阵
                    homography = self.estimate_homography_original(ref_kp, curr_kp, matches)
                    
                    if homography is not None:
                        processing_method = "白天原始SIFT匹配"
                        logger.info(f"白天原始SIFT算法成功，匹配点: {match_points}")
                    else:
                        logger.warning("白天原始SIFT算法失败，尝试模板匹配")
                
                # 如果原始算法失败，使用模板匹配
                if homography is None:
                    homography = self.template_matching_fallback(reference_img, current_img)
                    if homography is not None:
                        processing_method = "白天模板匹配"
                        fallback_count += 1
                    else:
                        processing_method = "白天无处理(直接复制)"
                        copy_count += 1
            
            # 对齐图像
            aligned_img = self.align_image(current_img, homography, reference_img.shape)
            
            # 保存对齐后的图像
            output_path = self.output_dir / Path(img_path).name
            cv2.imwrite(str(output_path), aligned_img)
            
            processing_time = time.time() - start_time
            image_type = "夜间" if curr_is_night else "白天"
            
            # 记录处理报告
            report_entry = {
                'filename': Path(img_path).name,
                'image_type': image_type,
                'processing_method': processing_method,
                'match_points': match_points,
                'inliers': inliers,
                'processing_time': processing_time,
                'success': homography is not None
            }
            processing_report.append(report_entry)
            
            logger.info(f"保存对齐图像: {output_path} ({image_type}, {processing_method}, {processing_time:.2f}秒)")
            
            if homography is not None:
                success_count += 1
        
        # 输出处理统计
        total_processed = len(image_files) - 1  # 排除参考图像
        logger.info("=" * 60)
        logger.info("处理统计:")
        logger.info(f"总图像数量: {total_processed}")
        logger.info(f"白天图像: {day_count}")
        logger.info(f"夜间图像: {night_count}")
        logger.info(f"成功对齐: {success_count}")
        logger.info(f"使用模板匹配: {fallback_count}")
        logger.info(f"直接复制: {copy_count}")
        logger.info(f"成功率: {success_count/total_processed*100:.1f}%")
        
        # 生成详细处理报告
        self.generate_processing_report(processing_report, day_count, night_count, success_count, fallback_count, copy_count)
        
        logger.info("图像对齐处理完成！")
        return True  # 返回成功状态
    
    def generate_processing_report(self, processing_report, day_count, night_count, success_count, fallback_count, copy_count):
        """
        生成详细的处理报告
        
        Args:
            processing_report: 处理数据列表
            day_count: 白天图像数量
            night_count: 夜间图像数量
            success_count: 成功处理数量
            fallback_count: 使用后备方案数量
            copy_count: 直接复制数量
        """
        report_path = self.output_dir / "processing_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 图像对齐处理报告\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 总体统计
            f.write("## 📊 总体统计\n\n")
            f.write(f"- **总图像数量**: {len(processing_report)}\n")
            f.write(f"- **白天图像**: {day_count} ({day_count/len(processing_report)*100:.1f}%)\n")
            f.write(f"- **夜间图像**: {night_count} ({night_count/len(processing_report)*100:.1f}%)\n")
            f.write(f"- **成功对齐**: {success_count} ({success_count/len(processing_report)*100:.1f}%)\n")
            f.write(f"- **模板匹配**: {fallback_count} ({fallback_count/len(processing_report)*100:.1f}%)\n")
            f.write(f"- **直接复制**: {copy_count} ({copy_count/len(processing_report)*100:.1f}%)\n\n")
            
            # 算法效果统计
            f.write("## 🔍 算法效果统计\n\n")
            
            # 统计各种处理方法的数量
            method_stats = {}
            for entry in processing_report:
                method = entry['processing_method']
                if method not in method_stats:
                    method_stats[method] = {'count': 0, 'success': 0, 'total_time': 0}
                method_stats[method]['count'] += 1
                if entry['success']:
                    method_stats[method]['success'] += 1
                method_stats[method]['total_time'] += entry['processing_time']
            
            f.write("| 处理方法 | 使用次数 | 成功率 | 平均耗时 |\n")
            f.write("|---------|---------|--------|----------|\n")
            for method, stats in method_stats.items():
                success_rate = stats['success'] / stats['count'] * 100
                avg_time = stats['total_time'] / stats['count']
                f.write(f"| {method} | {stats['count']} | {success_rate:.1f}% | {avg_time:.2f}s |\n")
            
            f.write("\n## 📋 详细处理记录\n\n")
            f.write("| 文件名 | 图像类型 | 处理方法 | 匹配点数 | 内点数 | 耗时(秒) | 状态 |\n")
            f.write("|--------|---------|----------|----------|--------|----------|------|\n")
            
            for entry in processing_report:
                status = "✅ 成功" if entry['success'] else "❌ 失败"
                f.write(f"| {entry['filename']} | {entry['image_type']} | {entry['processing_method']} | ")
                f.write(f"{entry['match_points']} | {entry['inliers']} | {entry['processing_time']:.2f} | {status} |\n")
            
            # 分类统计
            f.write("\n## 📈 分类详细统计\n\n")
            
            # 白天图像统计
            day_images = [e for e in processing_report if e['image_type'] == '白天']
            if day_images:
                day_success = len([e for e in day_images if e['success']])
                f.write(f"### 白天图像 ({len(day_images)}张)\n")
                f.write(f"- 成功率: {day_success/len(day_images)*100:.1f}%\n")
                f.write(f"- 原始SIFT成功: {len([e for e in day_images if '原始SIFT' in e['processing_method'] and e['success']])}张\n")
                f.write(f"- 模板匹配: {len([e for e in day_images if '模板匹配' in e['processing_method']])}张\n")
                f.write(f"- 直接复制: {len([e for e in day_images if '直接复制' in e['processing_method']])}张\n\n")
            
            # 夜间图像统计
            night_images = [e for e in processing_report if e['image_type'] == '夜间']
            if night_images:
                night_success = len([e for e in night_images if e['success']])
                f.write(f"### 夜间图像 ({len(night_images)}张)\n")
                f.write(f"- 成功率: {night_success/len(night_images)*100:.1f}%\n")
                f.write(f"- 增强算法成功: {len([e for e in night_images if '增强特征' in e['processing_method'] and e['success']])}张\n")
                f.write(f"- 模板匹配: {len([e for e in night_images if '模板匹配' in e['processing_method']])}张\n")
                f.write(f"- 直接复制: {len([e for e in night_images if '直接复制' in e['processing_method']])}张\n\n")
            
            f.write("\n---\n")
            f.write("*报告生成于 Enhanced TickTock-Align-NPU Library*\n")
        
        logger.info(f"详细处理报告已保存到: {report_path}")
    
