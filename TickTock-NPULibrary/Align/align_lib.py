#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TickTock-Align-NPU Library Demo

这个demo展示了如何使用TickTock-Align-NPU Library进行建筑物图像对齐。
输入: NPU-Lib文件夹中的图像序列
输出: 对齐后的图像保存到NPU-Lib-Align文件夹

功能特点:
- 使用第一张图像作为参考图像
- 支持手动设置参考图像
- 自动对齐后续所有图像
"""

import cv2
import numpy as np
import os
import glob
from pathlib import Path
import argparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TickTockAlign:
    """
    TickTock-Align-NPU 图像对齐类
    
    用于对建筑物图像序列进行对齐处理，确保所有图像都与参考图像对齐。
    """
    
    def __init__(self, input_dir="Lib", output_dir="Align", reference_index=0):
        """
        初始化对齐器
        
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
    
    def detect_features(self, img):
        """
        使用SIFT检测图像特征点
        
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
            
        # 创建SIFT检测器
        sift = cv2.SIFT_create()
        
        # 检测特征点和描述符
        keypoints, descriptors = sift.detectAndCompute(gray, None)
        
        return keypoints, descriptors
    
    def match_features(self, desc1, desc2):
        """
        匹配两幅图像的特征点
        
        Args:
            desc1: 第一幅图像的特征描述符
            desc2: 第二幅图像的特征描述符
            
        Returns:
            good_matches: 良好的匹配点对
        """
        # 使用FLANN匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(desc1, desc2, k=2)
        
        # 应用Lowe's ratio test筛选良好匹配
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
        
        return good_matches
    
    def estimate_homography(self, kp1, kp2, matches):
        """
        估计单应性矩阵
        
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
        
        # 使用RANSAC估计单应性矩阵
        homography, mask = cv2.findHomography(src_pts, dst_pts, 
                                            cv2.RANSAC, 
                                            ransacReprojThreshold=5.0)
        
        return homography
    
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
            logger.warning("单应性矩阵为空，返回原图像")
            return cv2.resize(img, (reference_shape[1], reference_shape[0]))
        
        # 应用透视变换
        aligned_img = cv2.warpPerspective(img, homography, 
                                        (reference_shape[1], reference_shape[0]))
        
        return aligned_img
    
    def process_images(self):
        """
        处理所有图像进行对齐
        """
        # 获取所有图像文件
        image_files = self.get_image_files()
        
        if not image_files:
            logger.error(f"在 {self.input_dir} 中未找到图像文件")
            return
        
        logger.info(f"找到 {len(image_files)} 张图像")
        
        # 读取参考图像
        if self.reference_index >= len(image_files):
            logger.error(f"参考图像索引 {self.reference_index} 超出范围")
            return
            
        reference_path = image_files[self.reference_index]
        reference_img = cv2.imread(reference_path)
        
        if reference_img is None:
            logger.error(f"无法读取参考图像: {reference_path}")
            return
        
        logger.info(f"使用参考图像: {Path(reference_path).name}")
        
        # 检测参考图像特征
        ref_kp, ref_desc = self.detect_features(reference_img)
        
        if ref_desc is None:
            logger.error("参考图像特征检测失败")
            return
        
        logger.info(f"参考图像检测到 {len(ref_kp)} 个特征点")
        
        # 保存参考图像到输出目录
        ref_output_path = self.output_dir / Path(reference_path).name
        cv2.imwrite(str(ref_output_path), reference_img)
        logger.info(f"保存参考图像: {ref_output_path}")
        
        # 处理其他图像
        for i, img_path in enumerate(image_files):
            if i == self.reference_index:
                continue  # 跳过参考图像
                
            logger.info(f"处理图像 {i+1}/{len(image_files)}: {Path(img_path).name}")
            
            # 读取当前图像
            current_img = cv2.imread(img_path)
            if current_img is None:
                logger.warning(f"无法读取图像: {img_path}")
                continue
            
            # 检测当前图像特征
            curr_kp, curr_desc = self.detect_features(current_img)
            
            if curr_desc is None:
                logger.warning(f"图像 {Path(img_path).name} 特征检测失败")
                # 保存调整大小后的原图像
                resized_img = cv2.resize(current_img, 
                                       (reference_img.shape[1], reference_img.shape[0]))
                output_path = self.output_dir / Path(img_path).name
                cv2.imwrite(str(output_path), resized_img)
                continue
            
            # 匹配特征点
            matches = self.match_features(ref_desc, curr_desc)
            logger.info(f"找到 {len(matches)} 个匹配点")
            
            # 估计单应性矩阵
            homography = self.estimate_homography(ref_kp, curr_kp, matches)
            
            # 对齐图像
            aligned_img = self.align_image(current_img, homography, reference_img.shape)
            
            # 保存对齐后的图像
            output_path = self.output_dir / Path(img_path).name
            cv2.imwrite(str(output_path), aligned_img)
            logger.info(f"保存对齐图像: {output_path}")
        
        logger.info("图像对齐处理完成！")
    
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TickTock-Align-NPU Library Demo')
    parser.add_argument('--input', '-i', default='NPU-Lib', 
                       help='输入图像文件夹路径 (默认: NPU-Lib)')
    parser.add_argument('--output', '-o', default='NPU-Lib-Align', 
                       help='输出图像文件夹路径 (默认: NPU-Lib-Align)')
    parser.add_argument('--reference', '-r', type=int, default=0, 
                       help='参考图像索引 (默认: 0，即第一张图像)')
    
    args = parser.parse_args()
    
    print("████████╗██╗ ██████╗██╗  ██╗████████╗ ██████╗  ██████╗██╗  ██╗")
    print("╚══██╔══╝██║██╔════╝██║ ██╔╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝")
    print("   ██║   ██║██║     █████╔╝    ██║   ██║   ██║██║     █████╔╝ ")
    print("   ██║   ██║██║     ██╔═██╗    ██║   ██║   ██║██║     ██╔═██╗ ")
    print("   ██║   ██║╚██████╗██║  ██╗   ██║   ╚██████╔╝╚██████╗██║  ██╗")
    print("   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝")
    print()
    print("TickTock-Align-NPU Library Demo")
    print("建筑物图像序列对齐工具")
    print("=" * 50)
    
    # 创建对齐器
    aligner = TickTockAlign(
        input_dir=args.input,
        output_dir=args.output,
        reference_index=args.reference
    )
    
    # 执行图像对齐
    aligner.process_images()
    
    print("=" * 50)
    print("处理完成！")
    print(f"对齐后的图像保存在: {args.output}")


if __name__ == "__main__":
    main()