#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头参数测试工具
用于测试和优化摄像头设置，确保获得最佳图像质量
"""

import cv2
import numpy as np
import os
from datetime import datetime

class CameraOptimizer:
    def __init__(self):
        self.camera_index = 0
    
    def test_camera_capabilities(self, camera_index=0):
        """
        测试摄像头支持的最大能力
        """
        print("=== 摄像头能力测试 ===")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            return False
        
        print("✅ 摄像头打开成功")
        
        # 测试支持的分辨率
        print("\n📹 测试支持的分辨率:")
        resolutions = [
            (3840, 2160),  # 4K
            (2560, 1440),  # 2K
            (1920, 1080),  # 1080p
            (1280, 720),   # 720p
            (640, 480),    # VGA
        ]
        
        supported_resolutions = []
        for width, height in resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                print(f"  ✅ {width}x{height}")
                supported_resolutions.append((width, height))
            else:
                print(f"  ❌ {width}x{height} (实际: {actual_width}x{actual_height})")
        
        # 使用最高支持的分辨率
        if supported_resolutions:
            best_res = supported_resolutions[0]
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, best_res[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, best_res[1])
            print(f"\n🎯 推荐使用分辨率: {best_res[0]}x{best_res[1]}")
        
        # 测试帧率
        print(f"\n⚡ 当前帧率: {cap.get(cv2.CAP_PROP_FPS):.1f} FPS")
        
        # 显示当前所有参数
        self._display_all_camera_properties(cap)
        
        cap.release()
        return True
    
    def _display_all_camera_properties(self, cap):
        """
        显示摄像头所有可用属性
        """
        print("\n📊 摄像头详细参数:")
        
        properties = [
            (cv2.CAP_PROP_FRAME_WIDTH, "宽度"),
            (cv2.CAP_PROP_FRAME_HEIGHT, "高度"),
            (cv2.CAP_PROP_FPS, "帧率"),
            (cv2.CAP_PROP_BRIGHTNESS, "亮度"),
            (cv2.CAP_PROP_CONTRAST, "对比度"),
            (cv2.CAP_PROP_SATURATION, "饱和度"),
            (cv2.CAP_PROP_HUE, "色调"),
            (cv2.CAP_PROP_GAIN, "增益"),
            (cv2.CAP_PROP_EXPOSURE, "曝光"),
            (cv2.CAP_PROP_SHARPNESS, "锐度"),
            (cv2.CAP_PROP_AUTOFOCUS, "自动对焦"),
            (cv2.CAP_PROP_AUTO_WB, "自动白平衡"),
            (cv2.CAP_PROP_AUTO_EXPOSURE, "自动曝光"),
            (cv2.CAP_PROP_BUFFERSIZE, "缓冲区大小"),
        ]
        
        for prop, name in properties:
            try:
                value = cap.get(prop)
                if prop in [cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_BUFFERSIZE]:
                    print(f"  {name}: {int(value)}")
                elif prop in [cv2.CAP_PROP_AUTOFOCUS, cv2.CAP_PROP_AUTO_WB]:
                    print(f"  {name}: {'开启' if value > 0 else '关闭'}")
                else:
                    print(f"  {name}: {value:.2f}")
            except:
                print(f"  {name}: 不支持")
    
    def optimize_camera_settings(self, camera_index=0):
        """
        优化摄像头设置以获得最佳图像质量
        """
        print("=== 摄像头优化设置 ===")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            return None
        
        # 设置最佳参数
        print("正在应用最佳设置...")
        
        # 分辨率设置（尝试最高分辨率）
        resolutions_to_try = [(1920, 1080), (1280, 720), (640, 480)]
        for width, height in resolutions_to_try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual_w == width and actual_h == height:
                print(f"✅ 分辨率设置为: {width}x{height}")
                break
        
        # 图像质量优化
        optimizations = [
            (cv2.CAP_PROP_BUFFERSIZE, 1, "缓冲区大小"),
            (cv2.CAP_PROP_FPS, 30, "帧率"),
            (cv2.CAP_PROP_AUTO_EXPOSURE, 0.25, "自动曝光"),
            (cv2.CAP_PROP_EXPOSURE, -6, "曝光值"),
            (cv2.CAP_PROP_BRIGHTNESS, 0.5, "亮度"),
            (cv2.CAP_PROP_CONTRAST, 0.6, "对比度"),
            (cv2.CAP_PROP_SATURATION, 0.6, "饱和度"),
            (cv2.CAP_PROP_SHARPNESS, 0.7, "锐度"),
            (cv2.CAP_PROP_GAIN, 0, "增益"),
            (cv2.CAP_PROP_AUTO_WB, 1, "自动白平衡"),
            (cv2.CAP_PROP_AUTOFOCUS, 1, "自动对焦"),
        ]
        
        for prop, value, name in optimizations:
            try:
                cap.set(prop, value)
                actual = cap.get(prop)
                print(f"  {name}: 设置={value}, 实际={actual:.2f}")
            except:
                print(f"  {name}: 不支持设置")
        
        return cap
    
    def capture_test_photo(self, camera_index=0):
        """
        拍摄测试照片以验证设置效果
        """
        print("\n=== 拍摄测试照片 ===")
        
        cap = self.optimize_camera_settings(camera_index)
        if cap is None:
            return False
        
        # 预热摄像头
        print("摄像头预热中...")
        for i in range(10):
            ret, frame = cap.read()
            if not ret:
                print(f"预热失败在第{i+1}帧")
                break
            if (i + 1) % 3 == 0:
                print(f"预热进度: {i+1}/10")
        
        # 额外稳定时间
        import time
        time.sleep(1)
        
        # 拍摄照片
        print("正在拍摄测试照片...")
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ 拍摄失败")
            return False
        
        # 保存照片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_test_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        
        # 显示图像信息
        h, w, c = frame.shape
        print(f"✅ 测试照片已保存: {filename}")
        print(f"📷 图像信息:")
        print(f"  分辨率: {w}x{h}")
        print(f"  通道数: {c}")
        print(f"  文件大小: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")
        
        # 简单的图像质量分析
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = np.mean(gray)
        
        print(f"📊 图像质量分析:")
        print(f"  清晰度分数: {blur_score:.2f} (>100为清晰)")
        print(f"  平均亮度: {mean_brightness:.2f} (0-255)")
        
        if blur_score > 100:
            print("  ✅ 图像清晰度良好")
        else:
            print("  ⚠️ 图像可能模糊，建议检查对焦")
        
        if 50 < mean_brightness < 200:
            print("  ✅ 亮度适中")
        else:
            print("  ⚠️ 亮度可能需要调整")
        
        return True

def main():
    """主函数"""
    optimizer = CameraOptimizer()
    
    print("摄像头优化工具")
    print("="*50)
    
    # 测试摄像头能力
    if not optimizer.test_camera_capabilities():
        print("摄像头测试失败")
        return
    
    print("\n" + "="*50)
    
    # 拍摄优化测试照片
    optimizer.capture_test_photo()
    
    print("\n" + "="*50)
    print("🎉 测试完成！")
    print("建议：")
    print("1. 确保摄像头支持1920x1080分辨率")
    print("2. 保持充足的光线环境")
    print("3. 定期清洁摄像头镜头")
    print("4. 如果图像模糊，检查自动对焦是否正常")

if __name__ == "__main__":
    main()