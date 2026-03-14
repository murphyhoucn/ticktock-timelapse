#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TickTock-Deep-Learning-Align Library

基于深度学习的图像对齐库，专门针对建筑物时间序列图像。
使用SuperGlue/SuperPoint或LoFTR等现代深度学习特征匹配方法。

功能特点:
- 基于深度学习的特征提取和匹配
- 对光照变化、季节变化鲁棒
- 支持日夜图像的统一处理
- 多种深度学习模型可选
- 自动回退到传统方法
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import logging
import time
import sys
import warnings
import requests
from tqdm import tqdm
warnings.filterwarnings('ignore')

# 深度学习导入
import torch
import torch.nn.functional as F
TORCH_AVAILABLE = True

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 指定使用的GPU

# 可选的特殊库导入
try:
    import kornia as K
    import kornia.feature as KF
    # 尝试导入可用的特征检测器
    KORNIA_AVAILABLE = True
    
    # 检查可用的特征检测器
    SIFT_AVAILABLE = hasattr(KF, 'SIFTFeature')
    LOFTR_AVAILABLE = hasattr(KF, 'LoFTR')
    
except ImportError:
    KORNIA_AVAILABLE = False
    SIFT_AVAILABLE = False
    LOFTR_AVAILABLE = False

try:
    from scipy.ndimage import maximum_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepLearningAlign:
    """
    基于深度学习的图像对齐类
    
    支持多种深度学习特征匹配方法，对传统方法难以处理的场景提供更好的解决方案。
    """
    
    def __init__(self, input_dir="Lib", output_dir="DL-Align", reference_index=0, method="superpoint"):
        """
        初始化深度学习对齐器
        
        Args:
            input_dir (str): 输入图像文件夹路径
            output_dir (str): 输出对齐图像文件夹路径
            reference_index (int): 参考图像索引
            method (str): 使用的深度学习方法 ('superpoint', 'loftr', 'sift_dl')
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.reference_index = reference_index
        self.method = method
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 检查GPU可用性
        if TORCH_AVAILABLE:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"使用设备: {self.device}")
            if torch.cuda.is_available():
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            self.device = 'cpu'
            logger.warning("PyTorch未安装，将使用CPU和传统方法")
        
        # 初始化深度学习模型
        self.init_models()
        
    def init_models(self):
        """初始化深度学习模型"""
        logger.info(f"初始化深度学习模型: {self.method}")
        
        if self.method == "superpoint":
            self.init_superpoint()
        elif self.method == "loftr":
            self.init_loftr()
        elif self.method == "sift_dl":
            self.init_sift_dl()
        elif self.method == "lightweight":
            self.init_lightweight_features()
        else:
            logger.warning(f"未知方法 {self.method}，回退到传统SIFT")
            self.init_traditional_sift()
    
    def init_superpoint(self):
        """初始化Kornia特征检测器（优先使用LoFTR，回退到SIFT）"""
        if KORNIA_AVAILABLE and TORCH_AVAILABLE:
            try:
                # 首先尝试使用本地LoFTR模型
                local_loftr_path = "/mnt/houjinliang/MyDevProject/TickTock-NPUEveryday/Align/loftr_outdoor.ckpt"
                
                # 检查本地是否有LoFTR模型文件
                if LOFTR_AVAILABLE:
                    if not Path(local_loftr_path).exists():
                        logger.info("本地LoFTR模型文件不存在，开始下载...")
                        success = self.download_loftr_model(local_loftr_path)
                        if not success:
                            logger.warning("LoFTR模型下载失败，回退到其他方法")
                            self.init_fallback_method()
                            return
                    
                    # 使用本地LoFTR模型
                    import torch
                    state_dict = torch.load(local_loftr_path, map_location=self.device)
                    self.loftr_matcher = KF.LoFTR(pretrained=None)
                    self.loftr_matcher.load_state_dict(state_dict['state_dict'])
                    self.loftr_matcher = self.loftr_matcher.to(self.device).eval()
                    logger.info("LoFTR模型初始化成功")
                    self.model_available = True
                    self.use_loftr = True
                    return
                else:
                    logger.warning("未找到LoFTR支持，回退到其他方法")
                    self.init_fallback_method()
                    return
            except Exception as e:
                logger.warning(f"Kornia特征检测器初始化失败: {e}")
        
        logger.warning("Kornia不可用，使用轻量级特征提取器")
        self.init_lightweight_features()
    
    def download_loftr_model(self, local_path):
        """下载LoFTR模型文件"""
        try:
            # LoFTR outdoor模型下载链接
            model_url = "https://github.com/zju3dv/LoFTR/releases/download/v1.0/outdoor_ds.ckpt"
            
            logger.info(f"正在下载LoFTR模型到: {local_path}")
            
            # 创建目录
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(local_path, 'wb') as f, tqdm(
                desc="下载LoFTR模型",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            logger.info(f"LoFTR模型下载完成: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"LoFTR模型下载失败: {e}")
            # 清理可能的部分下载文件
            if Path(local_path).exists():
                Path(local_path).unlink()
            return False
    
    def init_fallback_method(self):
        """初始化回退方法"""
        if SIFT_AVAILABLE:
            # 回退到Kornia SIFT特征
            self.kornia_sift = KF.SIFTFeature(num_features=2000).to(self.device).eval()
            logger.info("Kornia SIFT模型初始化成功")
            self.model_available = True
            self.use_loftr = False
        else:
            logger.warning("回退到轻量级特征提取器")
            self.init_lightweight_features()
    
    def init_loftr(self):
        """初始化LoFTR模型"""
        try:
            # 尝试使用第三方LoFTR实现
            logger.info("LoFTR模型需要额外安装，回退到轻量级特征提取")
            self.init_lightweight_features()
        except Exception as e:
            logger.warning(f"LoFTR初始化失败: {e}")
            self.init_lightweight_features()
    
    def init_sift_dl(self):
        """初始化SIFT+深度学习匹配的混合方法"""
        # 使用传统SIFT提取特征，深度学习进行匹配
        self.sift = cv2.SIFT_create(nfeatures=2000)
        self.init_lightweight_matcher()
        logger.info("SIFT+DL混合模型初始化成功")
        self.model_available = True
    
    def init_lightweight_features(self):
        """初始化轻量级深度学习特征提取器"""
        if not TORCH_AVAILABLE:
            self.init_traditional_sift()
            return
            
        # 更强大的CNN特征提取器
        class EnhancedFeatureExtractor(torch.nn.Module):
            def __init__(self):
                super().__init__()
                # 改进的CNN架构
                self.conv1 = torch.nn.Conv2d(1, 64, 3, padding=1)
                self.bn1 = torch.nn.BatchNorm2d(64)
                self.conv2 = torch.nn.Conv2d(64, 128, 3, padding=1)
                self.bn2 = torch.nn.BatchNorm2d(128)
                self.conv3 = torch.nn.Conv2d(128, 256, 3, padding=1)
                self.bn3 = torch.nn.BatchNorm2d(256)
                self.conv4 = torch.nn.Conv2d(256, 512, 3, padding=1)
                self.bn4 = torch.nn.BatchNorm2d(512)
                
                # 特征描述子头
                self.descriptor_head = torch.nn.Conv2d(512, 256, 1)
                
                # 关键点检测头
                self.keypoint_head = torch.nn.Conv2d(512, 1, 1)
                
            def forward(self, x):
                # 特征提取
                x = F.relu(self.bn1(self.conv1(x)))
                x = F.max_pool2d(x, 2)  # 1/2
                
                x = F.relu(self.bn2(self.conv2(x)))
                x = F.max_pool2d(x, 2)  # 1/4
                
                x = F.relu(self.bn3(self.conv3(x)))
                x = F.max_pool2d(x, 2)  # 1/8
                
                features = F.relu(self.bn4(self.conv4(x)))
                
                # 生成描述子和关键点
                descriptors = F.normalize(self.descriptor_head(features), p=2, dim=1)
                keypoint_scores = torch.sigmoid(self.keypoint_head(features))
                
                return {
                    'descriptors': descriptors,
                    'keypoint_scores': keypoint_scores,
                    'features': features
                }
        
        self.feature_extractor = EnhancedFeatureExtractor().to(self.device).eval()
        logger.info("增强版特征提取器初始化成功")
        self.model_available = True
    
    def init_lightweight_matcher(self):
        """初始化轻量级深度学习匹配器"""
        class LightweightMatcher(torch.nn.Module):
            def __init__(self, feature_dim=128):
                super().__init__()
                self.matcher = torch.nn.Sequential(
                    torch.nn.Linear(feature_dim * 2, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, 128),
                    torch.nn.ReLU(),
                    torch.nn.Linear(128, 1),
                    torch.nn.Sigmoid()
                )
            
            def forward(self, desc1, desc2):
                # 计算描述符相似度
                combined = torch.cat([desc1, desc2], dim=-1)
                similarity = self.matcher(combined)
                return similarity
        
        self.matcher = LightweightMatcher().to(self.device).eval()
        self.model_available = True
    
    def init_traditional_sift(self):
        """初始化传统SIFT作为回退方案"""
        self.sift = cv2.SIFT_create(nfeatures=2000)

        logger.info("传统SIFT初始化成功（回退方案）")
        self.model_available = True
    
    def get_image_files(self):
        """获取输入目录中的所有图像文件"""
        image_files = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        for ext in image_extensions:
            image_files.extend(list(self.input_dir.rglob(f"*{ext}")))
            image_files.extend(list(self.input_dir.rglob(f"*{ext.upper()}")))
        
        image_files = list(set([str(f) for f in image_files]))
        image_files.sort()
        return image_files
    
    def preprocess_image(self, img, target_size=512):
        """
        预处理图像用于深度学习模型
        
        Args:
            img: 输入图像
            target_size: 目标尺寸
            
        Returns:
            processed_img: 预处理后的图像tensor
            scale_factor: 缩放因子
        """
        # 转换为灰度图像
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 计算缩放因子
        h, w = gray.shape
        scale = target_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        # 调整大小
        resized = cv2.resize(gray, (new_w, new_h))
        
        # 转换为tensor
        tensor_img = torch.from_numpy(resized).float() / 255.0
        tensor_img = tensor_img.unsqueeze(0).unsqueeze(0).to(self.device)
        
        return tensor_img, scale, (new_h, new_w)
    
    def extract_features_kornia(self, img):
        """使用Kornia特征检测器提取特征"""
        try:
            if hasattr(self, 'use_loftr') and self.use_loftr:
                # 对于LoFTR，返回预处理后的tensor
                tensor_result, scale, bbox = self.preprocess_for_loftr(img)
                logger.info("LoFTR特征准备完成")
                return None, tensor_result  # 返回None和tensor供后续LoFTR匹配使用
                    
            elif hasattr(self, 'kornia_sift'):
                # 预处理图像
                if len(img.shape) == 3:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img
                    
                # 转换为tensor
                img_tensor = torch.from_numpy(gray).float().unsqueeze(0).unsqueeze(0).to(self.device) / 255.0
                
                # 使用Kornia SIFT
                lafs, responses, descriptors = self.kornia_sift(img_tensor)
                
                if lafs.shape[1] > 0:
                    # 转换LAFs到关键点
                    lafs_np = lafs[0].cpu().numpy()  # [N, 2, 3]
                    keypoints = []
                    
                    for laf in lafs_np:
                        # LAF格式转换为关键点坐标
                        x, y = laf[0, 2], laf[1, 2]  # 中心坐标
                        # 计算尺度
                        scale = np.sqrt(laf[0, 0]**2 + laf[0, 1]**2)
                        keypoints.append(cv2.KeyPoint(x=float(x), y=float(y), size=float(scale)))
                    
                    desc_np = descriptors[0].cpu().numpy().T  # [N, 128]
                    
                    logger.info(f"Kornia SIFT特征提取: {len(keypoints)}个关键点")
                    return keypoints, desc_np
                else:
                    logger.warning("Kornia SIFT未检测到特征点")
                    return self.extract_features_sift(img)
                        
        except Exception as e:
            logger.error(f"Kornia特征提取失败: {e}")
            return self.extract_features_sift(img)
    
    def extract_features_lightweight(self, img):
        """使用增强版网络提取特征"""
        try:
            processed_img, scale, (h, w) = self.preprocess_image(img, target_size=640)
            
            with torch.no_grad():
                # 特征提取
                output = self.feature_extractor(processed_img)
                descriptors_map = output['descriptors']
                keypoint_scores = output['keypoint_scores']
                
                # 关键点检测：使用非最大值抑制
                scores = keypoint_scores[0, 0].cpu().numpy()
                
                # 使用更好的关键点检测
                if SCIPY_AVAILABLE:
                    from scipy.ndimage import maximum_filter
                    local_max = maximum_filter(scores, size=3) == scores  # 减小窗口
                    coords = np.where(local_max & (scores > 0.15))  # 降低阈值
                else:
                    # 简单的局部最大值检测
                    threshold = np.percentile(scores, 85)  # 降低百分位
                    coords = np.where(scores > max(threshold, 0.15))
                
                if len(coords[0]) == 0:
                    logger.warning("未检测到足够的关键点")
                    return self.extract_features_sift(img)
                
                # 限制关键点数量
                max_keypoints = 2000  # 增加关键点数量
                if len(coords[0]) > max_keypoints:
                    # 按分数排序并选择最好的
                    point_scores = scores[coords]
                    top_indices = np.argsort(point_scores)[-max_keypoints:]
                    coords = (coords[0][top_indices], coords[1][top_indices])
                
                # 构建关键点和描述符
                keypoints = []
                descriptors = []
                
                desc_map = descriptors_map[0].cpu().numpy()  # [256, H, W]
                
                for y, x in zip(coords[0], coords[1]):
                    # 缩放回原始图像坐标
                    scale_factor = 8  # 下采样倍数
                    orig_x = (x * scale_factor) / scale
                    orig_y = (y * scale_factor) / scale
                    
                    if 0 <= orig_x < img.shape[1] and 0 <= orig_y < img.shape[0]:
                        keypoints.append(cv2.KeyPoint(x=float(orig_x), y=float(orig_y), size=8.0))
                        
                        # 提取描述符
                        if y < desc_map.shape[1] and x < desc_map.shape[2]:
                            desc = desc_map[:, y, x]  # [256]
                            descriptors.append(desc)
                
                if descriptors and len(descriptors) > 10:  # 提高最小特征点要求
                    descriptors = np.array(descriptors)  # [N, 256]
                    logger.info(f"深度学习特征提取: {len(keypoints)}个关键点")
                    return keypoints, descriptors
                else:
                    logger.warning(f"深度学习特征提取结果不佳({len(descriptors) if descriptors else 0}个特征点)，切换到SIFT")
                    return self.extract_features_sift(img)
                    
        except Exception as e:
            logger.error(f"深度学习特征提取失败: {e}")
            return self.extract_features_sift(img)
    
    def extract_features_sift(self, img):
        """使用传统SIFT提取特征"""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        keypoints, descriptors = self.sift.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def extract_features(self, img):
        """根据方法提取特征"""
        if self.method == "superpoint" and (hasattr(self, 'loftr_matcher') or hasattr(self, 'kornia_sift')):
            return self.extract_features_kornia(img)
        elif self.method in ["loftr", "lightweight"] and hasattr(self, 'feature_extractor'):
            # 尝试深度学习方法，如果失败则自动回退到SIFT
            dl_result = self.extract_features_lightweight(img)
            if dl_result[1] is not None and len(dl_result[1]) >= 50:  # 如果有足够的特征点
                return dl_result
            else:
                logger.info("深度学习特征不足，使用SIFT补充")
                return self.extract_features_sift(img)
        else:
            return self.extract_features_sift(img)
    
    def preprocess_for_loftr(self, img, target_size=640):
        """专为LoFTR优化的图像预处理"""
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

    def match_features_loftr(self, ref_tensor_info, curr_img):
        """使用LoFTR进行特征匹配 - 优化版"""
        try:
            # 预处理当前图像
            curr_tensor, curr_scale, (curr_sx, curr_sy, curr_w, curr_h) = self.preprocess_for_loftr(curr_img)
            
            # 引用图像信息 (ref_tensor_info 就是预处理后的tensor)
            ref_tensor = ref_tensor_info
            
            with torch.no_grad():
                # 准备输入数据
                input_dict = {
                    'image0': ref_tensor,    # [1, 1, H, W]
                    'image1': curr_tensor    # [1, 1, H, W]
                }
                
                # 运行LoFTR
                correspondences = self.loftr_matcher(input_dict)
                
                # 提取匹配结果
                mkpts0 = correspondences['keypoints0'].cpu().numpy()  # [N, 2]
                mkpts1 = correspondences['keypoints1'].cpu().numpy()  # [N, 2]
                mconf = correspondences['confidence'].cpu().numpy()   # [N]
                
                # 使用更低的置信度阈值
                confidence_thresh = 0.1
                mask = mconf > confidence_thresh
                mkpts0_filtered = mkpts0[mask]
                mkpts1_filtered = mkpts1[mask]
                mconf_filtered = mconf[mask]
                
                if len(mkpts0_filtered) == 0:
                    logger.warning("⚠️  没有足够置信度的匹配点")
                    return [], [], []
                
                # 将坐标从填充图像转换回原始图像坐标
                # 参考图像坐标转换 (假设使用相同的预处理)
                ref_scale = curr_scale  # 假设参考图像用相同预处理
                mkpts0_orig = mkpts0_filtered.copy()
                mkpts0_orig[:, 0] = (mkpts0_orig[:, 0] - curr_sx) / ref_scale
                mkpts0_orig[:, 1] = (mkpts0_orig[:, 1] - curr_sy) / ref_scale
                
                # 当前图像坐标转换
                mkpts1_orig = mkpts1_filtered.copy()
                mkpts1_orig[:, 0] = (mkpts1_orig[:, 0] - curr_sx) / curr_scale
                mkpts1_orig[:, 1] = (mkpts1_orig[:, 1] - curr_sy) / curr_scale
                
                # 过滤超出原始图像边界的点
                ref_h, ref_w = self.reference_shape[:2]
                curr_h, curr_w = curr_img.shape[:2]
                
                valid_mask = ((mkpts0_orig[:, 0] >= 0) & (mkpts0_orig[:, 0] < ref_w) &
                            (mkpts0_orig[:, 1] >= 0) & (mkpts0_orig[:, 1] < ref_h) &
                            (mkpts1_orig[:, 0] >= 0) & (mkpts1_orig[:, 0] < curr_w) &
                            (mkpts1_orig[:, 1] >= 0) & (mkpts1_orig[:, 1] < curr_h))
                
                mkpts0_final = mkpts0_orig[valid_mask]
                mkpts1_final = mkpts1_orig[valid_mask]
                mconf_final = mconf_filtered[valid_mask]
                
                # 创建OpenCV匹配格式
                matches = []
                kp1_list = []
                kp2_list = []
                
                for i in range(len(mkpts0_final)):
                    kp1_list.append(cv2.KeyPoint(x=mkpts0_final[i, 0], y=mkpts0_final[i, 1], size=1))
                    kp2_list.append(cv2.KeyPoint(x=mkpts1_final[i, 0], y=mkpts1_final[i, 1], size=1))
                    matches.append(cv2.DMatch(i, i, float(1.0 - mconf_final[i])))
                
                logger.info(f"LoFTR找到 {len(matches)} 个有效匹配")
                return matches, kp1_list, kp2_list
                
        except Exception as e:
            logger.error(f"LoFTR匹配失败: {e}")
            import traceback
            traceback.print_exc()
            return [], [], []
    
    def match_features_dl(self, desc1, desc2, kp1, kp2):
        """使用深度学习方法匹配特征"""
        if desc1 is None or desc2 is None:
            return []
        
        try:
            # 如果有深度学习匹配器
            if hasattr(self, 'matcher') and self.method == "sift_dl":
                return self.match_with_dl_matcher(desc1, desc2)
            else:
                return self.match_features_traditional(desc1, desc2)
                
        except Exception as e:
            logger.warning(f"深度学习匹配失败: {e}，使用传统方法")
            return self.match_features_traditional(desc1, desc2)
    
    def match_with_dl_matcher(self, desc1, desc2):
        """使用深度学习匹配器（优化版）"""
        if hasattr(self, 'matcher'):
            # 使用可学习的匹配器
            return self.match_with_learned_matcher(desc1, desc2)
        else:
            # 使用余弦相似度匹配
            return self.match_with_cosine_similarity(desc1, desc2)
    
    def match_with_cosine_similarity(self, desc1, desc2):
        """使用余弦相似度进行特征匹配"""
        desc1_tensor = torch.from_numpy(desc1).float().to(self.device)
        desc2_tensor = torch.from_numpy(desc2).float().to(self.device)
        
        # 归一化描述符
        desc1_norm = F.normalize(desc1_tensor, p=2, dim=1)
        desc2_norm = F.normalize(desc2_tensor, p=2, dim=1)
        
        # 计算相似度矩阵
        similarity_matrix = torch.mm(desc1_norm, desc2_norm.t())
        
        matches = []
        
        # 互相最近邻匹配
        for i in range(similarity_matrix.shape[0]):
            # 找到最似和次似的匹配
            similarities = similarity_matrix[i]
            sorted_indices = torch.argsort(similarities, descending=True)
            
            if len(sorted_indices) >= 2:
                best_idx = sorted_indices[0]
                second_best_idx = sorted_indices[1]
                
                best_sim = similarities[best_idx]
                second_sim = similarities[second_best_idx]
                
                # Lowe's ratio test for cosine similarity
                ratio = best_sim / (second_sim + 1e-8)
                
                if best_sim > 0.5 and ratio > 1.1:  # 降低匹配阈值
                    # 检查互相最近邻
                    reverse_best = torch.argmax(similarity_matrix[:, best_idx])
                    if reverse_best == i:
                        distance = float(1.0 - best_sim)
                        matches.append(cv2.DMatch(i, int(best_idx), distance))
        
        return matches
    
    def match_with_learned_matcher(self, desc1, desc2):
        """使用可学习的匹配器"""
        desc1_tensor = torch.from_numpy(desc1).float().to(self.device)
        desc2_tensor = torch.from_numpy(desc2).float().to(self.device)
        
        matches = []
        
        # 计算所有可能的匹配对
        with torch.no_grad():
            for i, d1 in enumerate(desc1_tensor):
                best_match_idx = -1
                best_similarity = 0
                
                for j, d2 in enumerate(desc2_tensor):
                    similarity = self.matcher(d1.unsqueeze(0), d2.unsqueeze(0))
                    
                    if similarity > best_similarity and similarity > 0.6:  # 阈值
                        best_similarity = similarity
                        best_match_idx = j
                
                if best_match_idx >= 0:
                    matches.append(cv2.DMatch(i, best_match_idx, float(1.0 - best_similarity)))
        
        return matches
    
    def match_features_traditional(self, desc1, desc2):
        """传统特征匹配"""
        # 使用FLANN匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        try:
            matches = flann.knnMatch(desc1, desc2, k=2)
            
            # Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            return good_matches
            
        except Exception as e:
            logger.warning(f"FLANN匹配失败: {e}")
            return []
    
    def estimate_homography_robust(self, kp1, kp2, matches, ransac_thresh=5.0):
        """鲁棒的单应性矩阵估计"""
        if len(matches) < 4:  # OpenCV最低要求是4个点
            logger.warning(f"匹配点数量不足 ({len(matches)})，无法计算单应性矩阵")
            return None, 0
        
        # 提取匹配点坐标
        src_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # 使用RANSAC估计单应性矩阵，优化参数
        homography, mask = cv2.findHomography(
            src_pts, dst_pts, 
            cv2.RANSAC, 
            ransacReprojThreshold=ransac_thresh,  # 更宽松的阈值
            maxIters=10000,  # 更多迭代
            confidence=0.995  # 更高置信度
        )
        
        inliers = np.sum(mask) if mask is not None else 0
        
        # 检查单应性矩阵质量
        if homography is not None:
            # 检查条件数
            cond_num = np.linalg.cond(homography)
            if cond_num > 100000:  # 条件数过高
                logger.warning(f"单应性矩阵条件数过高: {cond_num:.0f}，尝试降低精度要求")
                # 尝试更宽松的参数
                homography, mask = cv2.findHomography(
                    src_pts, dst_pts, 
                    cv2.RANSAC, 
                    ransacReprojThreshold=ransac_thresh * 2,  # 更宽松
                    maxIters=5000,
                    confidence=0.99
                )
                inliers = np.sum(mask) if mask is not None else 0
        
        return homography, inliers
    
    def align_image(self, img, homography, reference_shape):
        """对齐图像"""
        if homography is None:
            logger.warning("单应性矩阵为空，返回调整大小后的原图像")
            return cv2.resize(img, (reference_shape[1], reference_shape[0]))
        
        aligned_img = cv2.warpPerspective(
            img, homography, 
            (reference_shape[1], reference_shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
        
        return aligned_img
    
    def process_images(self):
        """处理所有图像进行对齐"""
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
        
        # 保存参考图像尺寸供LoFTR使用
        self.reference_shape = reference_img.shape
        
        # 提取参考图像特征
        ref_kp, ref_desc = self.extract_features(reference_img)
        
        # 特殊处理LoFTR情况
        if hasattr(self, 'use_loftr') and self.use_loftr:
            if ref_desc is None:
                logger.error("参考图像tensor提取失败")
                return
            logger.info("参考图像已准备用于LoFTR匹配")
        else:
            if ref_desc is None:
                logger.error("参考图像特征提取失败")
                return
            logger.info(f"参考图像提取到 {len(ref_kp)} 个特征点")
        
        # 保存参考图像
        ref_output_path = self.output_dir / Path(reference_path).name
        cv2.imwrite(str(ref_output_path), reference_img)
        logger.info(f"保存参考图像: {ref_output_path}")
        
        # 处理统计
        success_count = 0
        total_processed = 0
        processing_report = []
        
        # 处理其他图像
        for i, img_path in enumerate(image_files):
            if i == self.reference_index:
                continue
            
            logger.info(f"处理图像 {i+1}/{len(image_files)}: {Path(img_path).name}")
            start_time = time.time()
            
            # 读取当前图像
            current_img = cv2.imread(img_path)
            if current_img is None:
                logger.warning(f"无法读取图像: {img_path}")
                continue
            
            total_processed += 1
            
            # 检查是否使用LoFTR
            if hasattr(self, 'use_loftr') and self.use_loftr and hasattr(self, 'loftr_matcher'):
                # LoFTR直接匹配两张图像
                matches, matched_kp1, matched_kp2 = self.match_features_loftr(ref_desc, current_img)
                match_points = len(matches)
                
                logger.info(f"LoFTR找到 {match_points} 个匹配点")
                
                if match_points >= 4:
                    # 使用更宽松的RANSAC参数
                    homography, inliers = self.estimate_homography_robust(matched_kp1, matched_kp2, matches, ransac_thresh=8.0)
                    
                    if homography is not None:
                        logger.info(f"LoFTR对齐成功，内点数量: {inliers}")
                    else:
                        logger.warning("LoFTR对齐失败")
                else:
                    homography = None
                    inliers = 0
                    logger.warning("LoFTR匹配点不足")
            else:
                # 传统的特征提取和匹配
                curr_kp, curr_desc = self.extract_features(current_img)
                
                homography = None
                match_points = 0
                inliers = 0
                
                if curr_desc is not None:
                    # 匹配特征点
                    matches = self.match_features_dl(ref_desc, curr_desc, ref_kp, curr_kp)
                    match_points = len(matches)
                    
                    logger.info(f"找到 {match_points} 个匹配点")
                    
                    # 估计单应性矩阵
                    homography, inliers = self.estimate_homography_robust(ref_kp, curr_kp, matches)
                    
                    if homography is not None:
                        logger.info(f"深度学习对齐成功，内点数量: {inliers}")
                    else:
                        logger.warning("深度学习对齐失败")
            
            # 对齐图像
            aligned_img = self.align_image(current_img, homography, reference_img.shape)
            
            # 保存对齐后的图像
            output_path = self.output_dir / Path(img_path).name
            cv2.imwrite(str(output_path), aligned_img)
            
            processing_time = time.time() - start_time
            success = homography is not None
            
            if success:
                success_count += 1
            
            # 记录处理报告
            report_entry = {
                'filename': Path(img_path).name,
                'method': self.method,
                'match_points': match_points,
                'inliers': inliers,
                'processing_time': processing_time,
                'success': success
            }
            processing_report.append(report_entry)
            
            logger.info(f"保存对齐图像: {output_path} (深度学习, {processing_time:.2f}秒)")
        
        # 输出统计结果
        logger.info("=" * 60)
        logger.info("深度学习对齐处理统计:")
        logger.info(f"总图像数量: {total_processed}")
        logger.info(f"成功对齐: {success_count}")
        logger.info(f"成功率: {success_count/total_processed*100:.1f}%")
        logger.info(f"使用方法: {self.method}")
        logger.info(f"使用设备: {self.device}")
        
        # 生成处理报告
        self.generate_report(processing_report, success_count, total_processed)
        
        logger.info("深度学习图像对齐处理完成！")
    
    def generate_report(self, processing_report, success_count, total_processed):
        """生成处理报告"""
        report_path = self.output_dir / "dl_processing_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 深度学习图像对齐处理报告\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**使用方法**: {self.method}\n")
            f.write(f"**使用设备**: {self.device}\n\n")
            
            # 总体统计
            f.write("## 📊 总体统计\n\n")
            f.write(f"- **总图像数量**: {total_processed}\n")
            f.write(f"- **成功对齐**: {success_count} ({success_count/total_processed*100:.1f}%)\n")
            f.write(f"- **失败数量**: {total_processed - success_count}\n\n")
            
            # 性能统计
            if processing_report:
                avg_time = np.mean([r['processing_time'] for r in processing_report])
                avg_matches = np.mean([r['match_points'] for r in processing_report if r['success']])
                avg_inliers = np.mean([r['inliers'] for r in processing_report if r['success']])
                
                f.write("## 📈 性能统计\n\n")
                f.write(f"- **平均处理时间**: {avg_time:.2f}秒\n")
                f.write(f"- **平均匹配点数**: {avg_matches:.1f}\n")
                f.write(f"- **平均内点数**: {avg_inliers:.1f}\n\n")
            
            # 详细记录
            f.write("## 📋 详细处理记录\n\n")
            f.write("| 文件名 | 匹配点数 | 内点数 | 耗时(秒) | 状态 |\n")
            f.write("|--------|----------|--------|----------|------|\n")
            
            for entry in processing_report:
                status = "✅ 成功" if entry['success'] else "❌ 失败"
                f.write(f"| {entry['filename']} | {entry['match_points']} | {entry['inliers']} | ")
                f.write(f"{entry['processing_time']:.2f} | {status} |\n")
            
            f.write(f"\n---\n*报告生成于 Deep Learning Align Library*\n")
        
        logger.info(f"处理报告已保存到: {report_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Deep Learning Image Alignment')
    parser.add_argument('--input', '-i', default='NPU-Everyday-Sample', 
                       help='输入图像文件夹路径')
    parser.add_argument('--output', '-o', default='NPU-Everyday-Sample_DL-Align', 
                       help='输出图像文件夹路径')
    parser.add_argument('--reference', '-r', type=int, default=0, 
                       help='参考图像索引')
    parser.add_argument('--align-method', '-m', default='lightweight',
                       choices=['superpoint', 'loftr', 'sift_dl', 'lightweight'],
                       help='深度学习方法选择')
    
    args = parser.parse_args()
    
    print("🚀 Deep Learning Image Alignment")
    print("=" * 60)
    print(f"方法: {args.align_method}")
    print(f"输入: {args.input}")
    print(f"输出: {args.output}")
    print("=" * 60)
    
    # 创建深度学习对齐器
    try:
        aligner = DeepLearningAlign(
            input_dir=args.input,
            output_dir=args.output,
            reference_index=args.reference,
            method=args.align_method
        )
        
        # 执行对齐
        aligner.process_images()
        
        print("=" * 60)
        print("✅ 深度学习图像对齐完成！")
        print(f"结果保存在: {args.output}")
        
    except Exception as e:
        logger.error(f"深度学习对齐失败: {e}")
        print("❌ 处理失败，请检查错误日志")


if __name__ == "__main__":
    main()