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

def create_file_list():
    """创建文件列表（解决glob不支持问题）"""
    aligned_dir = Path("aligned_photos").resolve()  # 使用绝对路径
    jpg_files = sorted(aligned_dir.glob("*.jpg"))
    
    if not jpg_files:
        print("❌ 没有找到jpg文件")
        return None
    
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
        return temp_file.name
        
    except Exception as e:
        print(f"❌ 创建文件列表失败: {e}")
        temp_file.close()
        os.unlink(temp_file.name)
        return None

def create_timelapse_video(file_list_path, output_name, framerate=15, quality=18):
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
        '-vf', 'scale=1920:1080',  # 确保分辨率
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
    aligned_dir = Path("aligned_photos")
    if not aligned_dir.exists():
        print("❌ aligned_photos目录不存在")
        print("💡 请先运行: python timelapse_demo.py")
        return
    
    jpg_files = list(aligned_dir.glob("*.jpg"))
    if len(jpg_files) < 2:
        print(f"❌ 照片数量不足: 找到{len(jpg_files)}张，至少需要2张")
        print("💡 请先运行拍照程序获取更多照片")
        return
    
    print(f"📷 找到 {len(jpg_files)} 张照片")
    
    # 创建文件列表
    file_list_path = create_file_list()
    if not file_list_path:
        return
    
    try:
        # 创建多个版本的视频
        videos_created = 0
        
        # 1. 快速预览版 (30fps, 中等质量)
        print("\n🎬 创建快速预览版...")
        if create_timelapse_video(file_list_path, "timelapse_preview.mp4", framerate=30, quality=23):
            videos_created += 1
        
        # 2. 标准版 (15fps, 高质量)
        print("\n🎬 创建标准版...")
        if create_timelapse_video(file_list_path, "timelapse_standard.mp4", framerate=15, quality=20):
            videos_created += 1
        
        # 3. 高质量版 (10fps, 最高质量)
        print("\n🎬 创建高质量版...")
        if create_timelapse_video(file_list_path, "timelapse_hq.mp4", framerate=10, quality=18):
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