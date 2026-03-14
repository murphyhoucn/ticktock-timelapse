#!/usr/bin/env python3
"""
将对齐后的人脸照片制作成延时视频
"""

import cv2
import os
from pathlib import Path
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_timelapse_video(input_folder: str, output_video: str, fps: int = 10, duration_per_frame: float = 0.1):
    """
    创建延时视频
    Args:
        input_folder: 输入文件夹（包含对齐后的人脸图片）
        output_video: 输出视频文件名
        fps: 视频帧率
        duration_per_frame: 每张图片显示时长（秒）
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        logger.error(f"输入文件夹不存在: {input_folder}")
        return
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # 获取所有图片文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        logger.error(f"在 {input_folder} 中未找到图片文件")
        return
    
    # 按文件名排序
    image_files.sort()
    logger.info(f"找到 {len(image_files)} 张图片")
    
    # 读取第一张图片以获取尺寸
    first_image = cv2.imread(str(image_files[0]))
    if first_image is None:
        logger.error(f"无法读取第一张图片: {image_files[0]}")
        return
    
    height, width, _ = first_image.shape
    logger.info(f"视频尺寸: {width}x{height}")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        logger.error("无法创建视频文件")
        return
    
    # 计算每张图片需要重复的帧数
    frames_per_image = max(1, int(fps * duration_per_frame))
    
    logger.info(f"开始创建视频，每张图片显示 {frames_per_image} 帧...")
    
    for i, image_file in enumerate(image_files):
        logger.info(f"处理第 {i+1}/{len(image_files)} 张图片: {image_file.name}")
        
        # 读取图片
        image = cv2.imread(str(image_file))
        if image is None:
            logger.warning(f"无法读取图片: {image_file}")
            continue
        
        # 调整图片尺寸以匹配视频尺寸
        if image.shape[:2] != (height, width):
            image = cv2.resize(image, (width, height))
        
        # 为每张图片写入多帧
        for _ in range(frames_per_image):
            video_writer.write(image)
    
    # 释放资源
    video_writer.release()
    
    total_duration = len(image_files) * duration_per_frame
    logger.info(f"视频创建完成: {output_video}")
    logger.info(f"视频时长: {total_duration:.1f} 秒")
    logger.info(f"总帧数: {len(image_files) * frames_per_image}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='创建人脸延时视频')
    parser.add_argument('--input', '-i', default='Everyday_align_dlib',
                       help='输入文件夹路径 (默认: Everyday_align_dlib)')
    parser.add_argument('--output', '-o', default='timelapse.mp4',
                       help='输出视频文件名 (默认: timelapse.mp4)')
    parser.add_argument('--fps', type=int, default=10,
                       help='视频帧率 (默认: 10)')
    parser.add_argument('--duration', type=float, default=0.1,
                       help='每张图片显示时长（秒） (默认: 0.1)')
    
    args = parser.parse_args()
    
    create_timelapse_video(args.input, args.output, args.fps, args.duration)

if __name__ == "__main__":
    main()