#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg视频制作工具 - 兼容版本
解决glob模式不支持的问题
"""

import os
import subprocess
import sys
from pathlib import Path
import tempfile
from PIL import Image

def create_file_list():
    """创建文件列表（解决glob不支持问题）并获取原始分辨率"""
    aligned_dir = Path("../NPU-Lib-Align")
    if not aligned_dir.exists():
        aligned_dir = Path("NPU-Lib-Align") 
    aligned_dir = aligned_dir.resolve()  # 使用绝对路径
    jpg_files = sorted(aligned_dir.glob("*.jpg"))
    
    if not jpg_files:
        print("❌ 没有找到jpg文件")
        return None, None
    
    # 获取第一张图片的分辨率作为原始分辨率
    try:
        with Image.open(jpg_files[0]) as img:
            original_width, original_height = img.size
        print(f"📷 原始图片分辨率: {original_width}x{original_height}")
    except Exception as e:
        print(f"❌ 无法获取图片分辨率: {e}")
        return None, None
    
    # 创建临时文件列表
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    try:
        for jpg_file in jpg_files:
            # 使用绝对路径，Windows路径转换
            abs_path = jpg_file.resolve().as_posix()
            temp_file.write(f"file '{abs_path}'\n")
        temp_file.close()
        
        print(f"✅ 创建文件列表: {len(jpg_files)} 张照片")
        print(f"📄 文件列表路径: {temp_file.name}")
        return temp_file.name, (original_width, original_height)
        
    except Exception as e:
        print(f"❌ 创建文件列表失败: {e}")
        temp_file.close()
        os.unlink(temp_file.name)
        return None, None

def create_timelapse_video(file_list_path, output_name, framerate=30, quality=18, resolution="1920x1080"):
    """使用文件列表方式创建延时视频"""
    
    cmd = [
        'ffmpeg', '-y',  # 覆盖输出文件
        '-f', 'concat',  # 使用concat格式
        '-safe', '0',    # 允许相对路径
        '-i', file_list_path,  # 文件列表
        '-r', str(framerate),  # 输出帧率
        '-c:v', 'libx264',     # 视频编码器
        '-crf', str(quality),  # 质量参数
        '-pix_fmt', 'yuv420p', # 像素格式
        '-vf', f'scale={resolution}',  # 设置分辨率
        output_name
    ]
    
    print(f"🎬 创建视频: {output_name}")
    print("命令:", " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ 视频创建成功: {output_name}")
            
            # 显示文件信息
            if os.path.exists(output_name):
                file_size = os.path.getsize(output_name) / (1024 * 1024)
                print(f"📁 文件大小: {file_size:.1f} MB")
            
            return True
        else:
            print("❌ 视频创建失败")
            print("错误信息:")
            print(result.stderr[-800:])  # 显示最后800字符
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 视频创建超时（超过5分钟）")
        return False
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False

def main():
    """主函数"""
    print("🎬 FFmpeg视频制作工具（兼容版）")
    print("=" * 50)
    
    # 检查输入文件
    aligned_dir = Path("../NPU-Lib-Align")
    if not aligned_dir.exists():
        aligned_dir = Path("NPU-Lib-Align")
    if not aligned_dir.exists():
        print("❌ NPU-Lib-Align目录不存在")
        print("💡 请先运行: python demo.py")
        return
    
    jpg_files = list(aligned_dir.glob("*.jpg"))
    if len(jpg_files) < 2:
        print(f"❌ 照片数量不足: 找到{len(jpg_files)}张，至少需要2张")
        print("💡 请先运行拍照程序获取更多照片")
        return
    
    print(f"📷 找到 {len(jpg_files)} 张照片")
    
    # 创建文件列表并获取原始分辨率
    file_list_path, original_resolution = create_file_list()
    if not file_list_path or not original_resolution:
        return
    
    original_width, original_height = original_resolution
    
    # 计算三个质量等级的分辨率
    # 高质量: 原始分辨率
    hq_resolution = f"{original_width}x{original_height}"
    
    # 标准质量: 75%原始分辨率
    std_width = int(original_width * 0.75)
    std_height = int(original_height * 0.75)
    # 确保是偶数（FFmpeg要求）
    std_width = std_width - (std_width % 2)
    std_height = std_height - (std_height % 2)
    std_resolution = f"{std_width}x{std_height}"
    
    # 预览质量: 50%原始分辨率
    prev_width = int(original_width * 0.5)
    prev_height = int(original_height * 0.5)
    # 确保是偶数
    prev_width = prev_width - (prev_width % 2)
    prev_height = prev_height - (prev_height % 2)
    prev_resolution = f"{prev_width}x{prev_height}"
    
    print(f"🎬 视频质量设置:")
    print(f"   高质量: {hq_resolution} (CRF 18)")
    print(f"   标准质量: {std_resolution} (CRF 23)")
    print(f"   预览质量: {prev_resolution} (CRF 28)")
    
    try:
        # 创建多个版本的视频
        videos_created = 0
        
        # 确保Video目录存在
        Path("./Video").mkdir(exist_ok=True)
        
        # 1. 预览版 (30fps, 50%分辨率, 较低质量)
        print(f"\n🎬 创建预览版 ({prev_resolution})...")
        if create_timelapse_video(file_list_path, "./Video/timelapse_preview.mp4", framerate=30, quality=28, resolution=prev_resolution):
            videos_created += 1
        
        # 2. 标准版 (30fps, 75%分辨率, 中等质量)
        print(f"\n🎬 创建标准版 ({std_resolution})...")
        if create_timelapse_video(file_list_path, "./Video/timelapse_standard.mp4", framerate=30, quality=23, resolution=std_resolution):
            videos_created += 1
        
        # 3. 高质量版 (30fps, 原始分辨率, 高质量)
        print(f"\n🎬 创建高质量版 ({hq_resolution})...")
        if create_timelapse_video(file_list_path, "./Video/timelapse_hq.mp4", framerate=30, quality=18, resolution=hq_resolution):
            videos_created += 1
        
        print(f"\n🎉 完成！成功创建 {videos_created} 个视频文件")
        
        if videos_created > 0:
            print("\n📁 生成的视频文件:")
            for video_file in ["timelapse_preview.mp4", "timelapse_standard.mp4", "timelapse_hq.mp4"]:
                if os.path.exists(video_file):
                    size = os.path.getsize(video_file) / (1024 * 1024)
                    print(f"   🎬 {video_file} ({size:.1f} MB)")
        
    finally:
        # 清理临时文件
        if os.path.exists(file_list_path):
            os.unlink(file_list_path)
            print(f"\n🧹 清理临时文件: {file_list_path}")

if __name__ == "__main__":
    main()