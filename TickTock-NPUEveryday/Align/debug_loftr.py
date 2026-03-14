#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoFTR深度学习对齐诊断工具

专门用于调试和分析LoFTR深度学习图像对齐的效果
"""

import cv2
import numpy as np
import torch
import kornia.feature as KF
from pathlib import Path
import matplotlib.pyplot as plt
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoFTRDebugger:
    """LoFTR诊断工具"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"使用设备: {self.device}")
        
        # 初始化LoFTR
        self.init_loftr()
    
    def init_loftr(self):
        """初始化LoFTR模型"""
        try:
            local_loftr_path = "/mnt/houjinliang/MyDevProject/TickTock-NPUEveryday/Align/loftr_outdoor.ckpt"
            
            if Path(local_loftr_path).exists():
                # 加载本地模型
                state_dict = torch.load(local_loftr_path, map_location=self.device)
                self.loftr = KF.LoFTR(pretrained=None)
                self.loftr.load_state_dict(state_dict['state_dict'])
                self.loftr = self.loftr.to(self.device).eval()
                logger.info("✅ LoFTR模型初始化成功")
            else:
                raise FileNotFoundError(f"模型文件不存在: {local_loftr_path}")
                
        except Exception as e:
            logger.error(f"❌ LoFTR初始化失败: {e}")
            raise
    
    def preprocess_image(self, img, target_size=640):
        """预处理图像"""
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 获取原始尺寸
        h, w = gray.shape
        
        # 计算缩放因子，保持纵横比
        scale = min(target_size / w, target_size / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # 调整大小
        resized = cv2.resize(gray, (new_w, new_h))
        
        # 创建填充的正方形图像
        padded = np.zeros((target_size, target_size), dtype=np.uint8)
        start_x = (target_size - new_w) // 2
        start_y = (target_size - new_h) // 2
        padded[start_y:start_y+new_h, start_x:start_x+new_w] = resized
        
        # 转换为tensor
        tensor_img = torch.from_numpy(padded).float().unsqueeze(0).unsqueeze(0).to(self.device) / 255.0
        
        return tensor_img, scale, (start_x, start_y, new_w, new_h)
    
    def match_images_loftr(self, img1, img2, confidence_thresh=0.2):
        """使用LoFTR匹配两张图像"""
        try:
            # 预处理图像
            tensor1, scale1, (sx1, sy1, w1, h1) = self.preprocess_image(img1)
            tensor2, scale2, (sx2, sy2, w2, h2) = self.preprocess_image(img2)
            
            logger.info(f"图像1预处理: scale={scale1:.3f}, size=({w1}x{h1}), offset=({sx1},{sy1})")
            logger.info(f"图像2预处理: scale={scale2:.3f}, size=({w2}x{h2}), offset=({sx2},{sy2})")
            
            with torch.no_grad():
                # 准备输入数据
                input_dict = {
                    'image0': tensor1,  # [1, 1, H, W]
                    'image1': tensor2   # [1, 1, H, W]
                }
                
                # 运行LoFTR
                logger.info("🔍 运行LoFTR匹配...")
                correspondences = self.loftr(input_dict)
                
                # 提取匹配结果
                mkpts0 = correspondences['keypoints0'].cpu().numpy()  # [N, 2]
                mkpts1 = correspondences['keypoints1'].cpu().numpy()  # [N, 2]
                mconf = correspondences['confidence'].cpu().numpy()   # [N]
                
                logger.info(f"📊 原始匹配数量: {len(mkpts0)}")
                logger.info(f"📊 置信度范围: {mconf.min():.3f} - {mconf.max():.3f}")
                logger.info(f"📊 平均置信度: {mconf.mean():.3f}")
                
                # 置信度分析
                high_conf = np.sum(mconf > 0.8)
                med_conf = np.sum((mconf > 0.5) & (mconf <= 0.8))
                low_conf = np.sum((mconf > confidence_thresh) & (mconf <= 0.5))
                very_low_conf = np.sum(mconf <= confidence_thresh)
                
                logger.info(f"📊 置信度分布:")
                logger.info(f"   高置信度(>0.8): {high_conf}")
                logger.info(f"   中置信度(0.5-0.8): {med_conf}")
                logger.info(f"   低置信度({confidence_thresh}-0.5): {low_conf}")
                logger.info(f"   极低置信度(<{confidence_thresh}): {very_low_conf}")
                
                # 过滤低置信度匹配
                mask = mconf > confidence_thresh
                mkpts0_filtered = mkpts0[mask]
                mkpts1_filtered = mkpts1[mask]
                mconf_filtered = mconf[mask]
                
                logger.info(f"📊 过滤后匹配数量: {len(mkpts0_filtered)}")
                
                if len(mkpts0_filtered) == 0:
                    logger.warning("⚠️  没有足够置信度的匹配点")
                    return [], [], []
                
                # 将坐标从填充图像转换回原始图像
                # 图像1的坐标转换
                mkpts0_orig = mkpts0_filtered.copy()
                mkpts0_orig[:, 0] = (mkpts0_orig[:, 0] - sx1) / scale1  # x坐标
                mkpts0_orig[:, 1] = (mkpts0_orig[:, 1] - sy1) / scale1  # y坐标
                
                # 图像2的坐标转换
                mkpts1_orig = mkpts1_filtered.copy()
                mkpts1_orig[:, 0] = (mkpts1_orig[:, 0] - sx2) / scale2  # x坐标
                mkpts1_orig[:, 1] = (mkpts1_orig[:, 1] - sy2) / scale2  # y坐标
                
                # 过滤超出原始图像边界的点
                h1_orig, w1_orig = img1.shape[:2]
                h2_orig, w2_orig = img2.shape[:2]
                
                valid_mask = ((mkpts0_orig[:, 0] >= 0) & (mkpts0_orig[:, 0] < w1_orig) &
                            (mkpts0_orig[:, 1] >= 0) & (mkpts0_orig[:, 1] < h1_orig) &
                            (mkpts1_orig[:, 0] >= 0) & (mkpts1_orig[:, 0] < w2_orig) &
                            (mkpts1_orig[:, 1] >= 0) & (mkpts1_orig[:, 1] < h2_orig))
                
                mkpts0_final = mkpts0_orig[valid_mask]
                mkpts1_final = mkpts1_orig[valid_mask]
                mconf_final = mconf_filtered[valid_mask]
                
                logger.info(f"📊 有效匹配数量: {len(mkpts0_final)}")
                
                # 创建OpenCV匹配格式
                matches = []
                kp1_list = []
                kp2_list = []
                
                for i in range(len(mkpts0_final)):
                    kp1_list.append(cv2.KeyPoint(x=mkpts0_final[i, 0], y=mkpts0_final[i, 1], size=1))
                    kp2_list.append(cv2.KeyPoint(x=mkpts1_final[i, 0], y=mkpts1_final[i, 1], size=1))
                    matches.append(cv2.DMatch(i, i, float(1.0 - mconf_final[i])))
                
                return matches, kp1_list, kp2_list
                
        except Exception as e:
            logger.error(f"❌ LoFTR匹配失败: {e}")
            import traceback
            traceback.print_exc()
            return [], [], []
    
    def estimate_homography_robust(self, kp1, kp2, matches, ransac_thresh=5.0):
        """鲁棒的单应性矩阵估计"""
        if len(matches) < 4:
            logger.warning(f"⚠️  匹配点数量不足 ({len(matches)})，无法计算单应性矩阵")
            return None, 0
        
        # 提取匹配点坐标
        src_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        logger.info(f"🔍 RANSAC参数: 阈值={ransac_thresh}, 最大迭代=5000")
        
        # 使用RANSAC估计单应性矩阵
        homography, mask = cv2.findHomography(
            src_pts, dst_pts, 
            cv2.RANSAC, 
            ransacReprojThreshold=ransac_thresh,
            maxIters=5000,
            confidence=0.99
        )
        
        inliers = np.sum(mask) if mask is not None else 0
        outliers = len(matches) - inliers
        
        logger.info(f"📊 RANSAC结果: 内点={inliers}, 外点={outliers}, 内点比例={inliers/len(matches)*100:.1f}%")
        
        if homography is not None:
            # 分析单应性矩阵
            det = np.linalg.det(homography[:2, :2])
            logger.info(f"📊 单应性矩阵行列式: {det:.3f}")
            
            # 检查条件数
            cond = np.linalg.cond(homography)
            logger.info(f"📊 单应性矩阵条件数: {cond:.1f}")
            
            if cond > 1000:
                logger.warning("⚠️  单应性矩阵条件数过高，可能不稳定")
        
        return homography, inliers
    
    def visualize_matches(self, img1, img2, kp1, kp2, matches, output_path="debug_matches.jpg"):
        """可视化匹配结果"""
        try:
            # 创建匹配可视化图像
            img_matches = cv2.drawMatches(img1, kp1, img2, kp2, matches[:50], None, 
                                        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            
            # 保存图像
            cv2.imwrite(output_path, img_matches)
            logger.info(f"📷 匹配可视化已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ 可视化失败: {e}")
    
    def debug_image_pair(self, img1_path, img2_path, output_dir="debug_output"):
        """调试一对图像的匹配效果"""
        logger.info("=" * 80)
        logger.info(f"🔍 调试图像对: {Path(img1_path).name} vs {Path(img2_path).name}")
        logger.info("=" * 80)
        
        # 创建输出目录
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 读取图像
        img1 = cv2.imread(str(img1_path))
        img2 = cv2.imread(str(img2_path))
        
        if img1 is None or img2 is None:
            logger.error("❌ 无法读取图像")
            return
        
        logger.info(f"📐 图像1尺寸: {img1.shape}")
        logger.info(f"📐 图像2尺寸: {img2.shape}")
        
        # 分析图像统计信息
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if len(img1.shape) == 3 else img1
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if len(img2.shape) == 3 else img2
        
        logger.info(f"📊 图像1统计: 均值={gray1.mean():.1f}, 标准差={gray1.std():.1f}, 范围=[{gray1.min()}-{gray1.max()}]")
        logger.info(f"📊 图像2统计: 均值={gray2.mean():.1f}, 标准差={gray2.std():.1f}, 范围=[{gray2.min()}-{gray2.max()}]")
        
        # 测试不同的置信度阈值
        confidence_thresholds = [0.1, 0.2, 0.3, 0.5]
        
        best_matches = 0
        best_threshold = 0.2
        best_result = None
        
        for thresh in confidence_thresholds:
            logger.info(f"\n🔍 测试置信度阈值: {thresh}")
            
            matches, kp1, kp2 = self.match_images_loftr(img1, img2, confidence_thresh=thresh)
            
            if len(matches) >= 4:
                homography, inliers = self.estimate_homography_robust(kp1, kp2, matches)
                
                if len(matches) > best_matches:
                    best_matches = len(matches)
                    best_threshold = thresh
                    best_result = (matches, kp1, kp2, homography, inliers)
                
                # 保存可视化
                vis_path = output_dir / f"matches_thresh_{thresh}.jpg"
                self.visualize_matches(img1, img2, kp1, kp2, matches, str(vis_path))
            else:
                logger.warning(f"⚠️  置信度{thresh}: 匹配点不足({len(matches)})")
        
        # 输出最佳结果
        if best_result:
            matches, kp1, kp2, homography, inliers = best_result
            logger.info("\n" + "=" * 50)
            logger.info(f"🏆 最佳结果 (阈值={best_threshold}):")
            logger.info(f"   匹配点数: {len(matches)}")
            logger.info(f"   内点数: {inliers}")
            logger.info(f"   成功率: {inliers/len(matches)*100:.1f}% ({inliers}/{len(matches)})")
            logger.info(f"   对齐: {'✅ 成功' if homography is not None else '❌ 失败'}")
            
            # 保存最佳匹配可视化
            best_vis_path = output_dir / f"best_matches_{Path(img1_path).stem}_vs_{Path(img2_path).stem}.jpg"
            self.visualize_matches(img1, img2, kp1, kp2, matches, str(best_vis_path))
            
            return homography is not None, len(matches), inliers
        else:
            logger.warning("❌ 所有阈值都无法产生足够的匹配点")
            return False, 0, 0

def main():
    """主函数：调试NPU-Everyday-Sample中的图像"""
    debugger = LoFTRDebugger()
    
    # 输入目录
    input_dir = Path("NPU-Everyday-Sample")
    if not input_dir.exists():
        logger.error(f"❌ 输入目录不存在: {input_dir}")
        return
    
    # 获取图像文件 - 递归搜索
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png']:
        image_files.extend(list(input_dir.rglob(f"*{ext}")))
        image_files.extend(list(input_dir.rglob(f"*{ext.upper()}")))
    
    image_files.sort()
    logger.info(f"📁 找到 {len(image_files)} 张图像")
    
    if len(image_files) < 2:
        logger.error("❌ 图像数量不足")
        return
    
    # 选择参考图像
    ref_img = image_files[0]
    logger.info(f"📌 参考图像: {ref_img.name}")
    
    # 调试前几对图像
    success_count = 0
    total_matches = 0
    total_inliers = 0
    
    max_debug = min(5, len(image_files) - 1)  # 调试前5对
    
    for i in range(1, max_debug + 1):
        curr_img = image_files[i]
        
        success, matches, inliers = debugger.debug_image_pair(ref_img, curr_img)
        
        if success:
            success_count += 1
        total_matches += matches
        total_inliers += inliers
    
    # 输出总结
    logger.info("\n" + "=" * 80)
    logger.info("📊 LoFTR诊断总结")
    logger.info("=" * 80)
    logger.info(f"调试图像对数: {max_debug}")
    logger.info(f"成功对齐: {success_count}")
    logger.info(f"成功率: {success_count/max_debug*100:.1f}%")
    logger.info(f"平均匹配点数: {total_matches/max_debug:.1f}")
    logger.info(f"平均内点数: {total_inliers/max_debug:.1f}")
    logger.info(f"平均内点比例: {total_inliers/total_matches*100 if total_matches > 0 else 0:.1f}%")
    
    # 诊断建议
    logger.info("\n🔧 优化建议:")
    if success_count == 0:
        logger.info("- ❌ 完全失败，建议检查图像预处理和模型配置")
        logger.info("- 🔍 尝试降低置信度阈值或调整RANSAC参数")
    elif success_count < max_debug * 0.5:
        logger.info("- ⚠️  成功率较低，建议优化匹配策略")
        logger.info("- 🔧 考虑使用多尺度匹配或特征融合")
    else:
        logger.info("- ✅ 效果尚可，可进一步优化参数")

if __name__ == "__main__":
    main()