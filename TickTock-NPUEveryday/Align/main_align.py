#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TickTock-Main-Align Library

主要图像对齐库，整合了深度学习和增强传统方法。
提供两种对齐策略：
1. 深度学习方法 (superpoint) - 基于LoFTR的现代深度学习对齐
2. 增强传统方法 (enhanced) - 增强的SIFT+模板匹配组合方法

功能特点:
- 智能方法选择和回退
- 保持目录结构的输出
- 统一的处理接口
- 详细的处理报告
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import logging
import time
import sys
import warnings
warnings.filterwarnings('ignore')

# 导入两个对齐模块
try:
    from .superpoint import DeepLearningAlign
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False
    logging.warning("深度学习对齐模块不可用")

try:
    from .enhanced import EnhancedAlign
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    logging.warning("增强对齐模块不可用")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainAlign:
    """
    主要图像对齐类 - 整合深度学习和增强传统方法
    """
    
    def __init__(self, input_dir="NPU-Everyday-Sample", output_dir="NPU-Everyday-Sample_Aligned", 
                 reference_index=0, method="auto"):
        """
        初始化主要对齐器
        
        Args:
            input_dir (str): 输入图像文件夹路径
            output_dir (str): 输出对齐图像文件夹路径
            reference_index (int): 参考图像索引
            method (str): 对齐方法选择
                        - "superpoint": 深度学习LoFTR方法
                        - "enhanced": 增强传统SIFT+模板匹配方法
                        - "auto": 自动选择最佳方法
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.reference_index = reference_index
        self.method = method
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查可用的对齐方法
        self.available_methods = []
        if DL_AVAILABLE:
            self.available_methods.append("superpoint")
        if ENHANCED_AVAILABLE:
            self.available_methods.append("enhanced")
            
        if not self.available_methods:
            raise RuntimeError("没有可用的对齐方法！请检查依赖模块。")
        
        logger.info(f"可用的对齐方法: {', '.join(self.available_methods)}")
        
        # 初始化对齐器
        self.aligner = None
        self.selected_method = None
        
        # 统计信息收集
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'successful_alignments': 0,
            'failed_alignments': 0,
            'processing_times': [],
            'image_details': [],
            'method_used': None,
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'average_processing_time': 0,
            'success_rate': 0,
            'hardware_info': {},
            'error_details': []
        }
        
        self._init_aligner()
    
    def _init_aligner(self):
        """初始化具体的对齐器"""
        if self.method == "auto":
            # 自动选择最佳方法
            if "superpoint" in self.available_methods:
                self.selected_method = "superpoint"
                logger.info("🚀 自动选择深度学习方法 (superpoint)")
            else:
                self.selected_method = "enhanced"
                logger.info("🔧 自动选择增强传统方法 (enhanced)")
        else:
            if self.method not in self.available_methods:
                logger.warning(f"请求的方法 '{self.method}' 不可用，回退到可用方法")
                self.selected_method = self.available_methods[0]
            else:
                self.selected_method = self.method
        
        # 记录选择的方法
        self.stats['method_used'] = self.selected_method
        
        # 创建对应的对齐器
        if self.selected_method == "superpoint":
            self.aligner = DeepLearningAlign(
                input_dir=str(self.input_dir),
                output_dir=str(self.output_dir),
                reference_index=self.reference_index
            )
            # 收集GPU信息
            self._collect_hardware_info()
            logger.info("✅ 深度学习对齐器初始化完成")
            
        elif self.selected_method == "enhanced":
            self.aligner = EnhancedAlign(
                input_dir=str(self.input_dir),
                output_dir=str(self.output_dir),
                reference_index=self.reference_index
            )
            # 收集硬件信息
            self._collect_hardware_info()
            logger.info("✅ 增强传统对齐器初始化完成")
    
    def get_image_files(self):
        """获取所有图像文件"""
        image_files = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        for ext in image_extensions:
            image_files.extend(list(self.input_dir.rglob(f"*{ext}")))
            image_files.extend(list(self.input_dir.rglob(f"*{ext.upper()}")))
        
        image_files = list(set([str(f) for f in image_files]))
        image_files.sort()
        return image_files
    
    def preserve_directory_structure(self):
        """保持目录结构的对齐处理"""
        logger.info("🔄 开始保持目录结构的图像对齐处理...")
        
        # 获取所有图像文件
        image_files = self.get_image_files()
        if not image_files:
            logger.error(f"❌ 在 {self.input_dir} 中未找到图像文件")
            return False
        
        logger.info(f"📁 找到 {len(image_files)} 张图像")
        
        # 先执行基础对齐到临时目录
        temp_output = self.output_dir / "temp_aligned"
        temp_output.mkdir(exist_ok=True)
        
        # 创建临时对齐器
        if self.selected_method == "superpoint":
            temp_aligner = DeepLearningAlign(
                input_dir=str(self.input_dir),
                output_dir=str(temp_output),
                reference_index=self.reference_index
            )
        else:
            temp_aligner = EnhancedAlign(
                input_dir=str(self.input_dir),
                output_dir=str(temp_output),
                reference_index=self.reference_index
            )
        
        # 执行对齐
        logger.info(f"🎯 使用 {self.selected_method} 方法进行对齐...")
        temp_aligner.process_images()
        
        # 重新组织文件到原有目录结构
        self._reorganize_files(temp_output, image_files)
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_output)
        
        # 生成最终报告
        self._generate_main_report(image_files)
        
        logger.info("✅ 保持目录结构的对齐处理完成！")
        return True
    
    def _collect_hardware_info(self):
        """收集硬件信息"""
        try:
            import torch
            if torch.cuda.is_available():
                self.stats['hardware_info']['gpu_available'] = True
                self.stats['hardware_info']['gpu_name'] = torch.cuda.get_device_name(0)
                self.stats['hardware_info']['gpu_memory'] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB"
                self.stats['hardware_info']['cuda_version'] = torch.version.cuda
            else:
                self.stats['hardware_info']['gpu_available'] = False
        except ImportError:
            self.stats['hardware_info']['gpu_available'] = False
        
        # CPU信息
        try:
            import psutil
            self.stats['hardware_info']['cpu_count'] = psutil.cpu_count()
            self.stats['hardware_info']['memory_total'] = f"{psutil.virtual_memory().total / 1024**3:.1f}GB"
        except ImportError:
            import multiprocessing
            self.stats['hardware_info']['cpu_count'] = multiprocessing.cpu_count()
            self.stats['hardware_info']['memory_total'] = "Unknown"
    
    def _collect_detailed_stats_from_submodule(self):
        """从子模块的处理报告中收集详细统计信息"""
        try:
            # 尝试读取子模块生成的报告文件
            if self.selected_method == "superpoint":
                report_file = self.output_dir / "superpoint_processing_report.md"
            else:
                report_file = self.output_dir / "processing_report.md"
            
            if report_file.exists():
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析成功统计信息
                import re
                
                # 查找成功对齐数量 (匹配Markdown粗体格式)
                success_match = re.search(r'\*\*成功对齐\*\*:\s*(\d+)', content)
                if success_match:
                    processed_successful = int(success_match.group(1))
                    # 成功对齐的总数 = 处理成功的 + 参考图像(总是成功的)
                    self.stats['successful_alignments'] = processed_successful + 1
                
                # 查找总图像数量（子模块报告的是处理的图像数，不包括参考图像）
                total_match = re.search(r'\*\*总图像数量\*\*:\s*(\d+)', content)
                if total_match:
                    processed_images = int(total_match.group(1))
                    # 总图像 = 处理的图像 + 参考图像
                    self.stats['total_images'] = processed_images + 1
                
                # 计算失败数量
                self.stats['failed_alignments'] = self.stats['total_images'] - self.stats['successful_alignments']
                
                # 查找成功率
                success_rate_match = re.search(r'成功率:\s*([\d.]+)%', content)
                if success_rate_match:
                    reported_rate = float(success_rate_match.group(1))
                    # 调整成功率计算包括参考图像
                    self.stats['success_rate'] = (self.stats['successful_alignments'] / self.stats['total_images']) * 100
                
                logger.debug(f"从子模块报告收集到统计信息: 成功={self.stats['successful_alignments']}, 失败={self.stats['failed_alignments']}")
            
        except Exception as e:
            logger.warning(f"无法从子模块报告收集统计信息: {e}")
            # 使用简单估算
            self.stats['successful_alignments'] = self.stats['total_images']
            self.stats['failed_alignments'] = 0
    
    def _reorganize_files(self, temp_output, original_files):
        """重新组织文件到原有目录结构"""
        logger.info("📂 重新组织文件到原有目录结构...")
        
        for original_file in original_files:
            original_path = Path(original_file)
            filename = original_path.name
            
            # 在临时输出目录中找到对应的对齐文件
            aligned_file = temp_output / filename
            if aligned_file.exists():
                # 计算相对于输入目录的路径
                relative_path = original_path.relative_to(self.input_dir)
                
                # 创建对应的输出路径
                output_path = self.output_dir / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                import shutil
                shutil.copy2(str(aligned_file), str(output_path))
                logger.debug(f"📄 {filename} -> {relative_path}")
        
        logger.info("✅ 文件重新组织完成")
    
    def _generate_main_report(self, image_files):
        """生成详细的主要处理报告"""
        report_path = self.output_dir / "main_align_report.md"
        
        # 计算最终统计数据
        self.stats['total_images'] = len(image_files) if image_files else self.stats['total_images']
        if self.stats['processing_times']:
            self.stats['average_processing_time'] = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
        if self.stats['total_images'] > 0:
            self.stats['success_rate'] = (self.stats['successful_alignments'] / self.stats['total_images']) * 100
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # 头部信息
            f.write("# 🎯 Main Align 详细处理报告\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**处理时间**: {self.stats.get('start_time', 'N/A')} ~ {self.stats.get('end_time', 'N/A')}\n")
            f.write(f"**总耗时**: {self.stats['total_duration']:.2f} 秒\n")
            f.write(f"**使用方法**: {self.selected_method}\n")
            f.write(f"**输入目录**: {self.input_dir}\n")
            f.write(f"**输出目录**: {self.output_dir}\n\n")
            
            # 性能统计
            f.write("## 🚀 性能统计\n\n")
            f.write(f"- **总图像数量**: {self.stats['total_images']}\n")
            f.write(f"- **成功对齐**: {self.stats['successful_alignments']}\n")
            f.write(f"- **失败数量**: {self.stats['failed_alignments']}\n")
            f.write(f"- **成功率**: {self.stats['success_rate']:.1f}%\n")
            f.write(f"- **平均处理时间**: {self.stats['average_processing_time']:.2f} 秒/张\n")
            
            if self.stats['processing_times']:
                f.write(f"- **最快处理**: {min(self.stats['processing_times']):.2f} 秒\n")
                f.write(f"- **最慢处理**: {max(self.stats['processing_times']):.2f} 秒\n")
            f.write("\n")
            
            # 硬件环境
            f.write("## 🖥️ 硬件环境\n\n")
            hw_info = self.stats['hardware_info']
            if hw_info.get('gpu_available'):
                f.write(f"- **GPU**: {hw_info.get('gpu_name', 'Unknown')}\n")
                f.write(f"- **GPU内存**: {hw_info.get('gpu_memory', 'Unknown')}\n")
                f.write(f"- **CUDA版本**: {hw_info.get('cuda_version', 'Unknown')}\n")
            else:
                f.write("- **GPU**: 不可用 (CPU模式)\n")
            f.write(f"- **CPU核数**: {hw_info.get('cpu_count', 'Unknown')}\n")
            f.write(f"- **系统内存**: {hw_info.get('memory_total', 'Unknown')}\n\n")
            
            # 对齐方法详情
            f.write("## 🔧 对齐方法详情\n\n")
            if self.selected_method == "superpoint":
                f.write("### 🚀 深度学习方法 (SuperPoint)\n")
                f.write("- **核心技术**: LoFTR (Local Feature TRansformer)\n")
                f.write("- **特征提取**: SuperPoint + LoFTR Transformer\n")
                f.write("- **匹配算法**: 深度学习特征匹配\n")
                f.write("- **优势**: 对光照、季节变化鲁棒，高精度\n")
                f.write("- **适用场景**: 现代建筑、复杂场景、光照变化\n")
                f.write("- **GPU加速**: 支持CUDA加速，处理速度提升10倍\n\n")
            else:
                f.write("### 🔧 增强传统方法 (Enhanced)\n")
                f.write("- **核心技术**: 增强SIFT + 模板匹配 + BRISK\n")
                f.write("- **特征提取**: 日间SIFT + 夜间BRISK\n")
                f.write("- **匹配策略**: 多层次回退机制\n")
                f.write("- **优势**: 兼容性好、稳定性高、CPU友好\n")
                f.write("- **适用场景**: 传统场景、无GPU环境、兼容性要求\n")
                f.write("- **回退机制**: SIFT失败→BRISK→模板匹配\n\n")
            
            # 目录结构分析  
            f.write("## � 目录结构分析\n\n")
            if image_files:
                dirs = set()
                for img_file in image_files:
                    rel_path = Path(img_file).relative_to(self.input_dir)
                    if len(rel_path.parts) > 1:
                        dirs.add(rel_path.parent)
                
                if dirs:
                    f.write(f"- **目录数量**: {len(dirs)}\n")
                    f.write(f"- **结构类型**: 层次化目录结构\n")
                    f.write(f"- **结构保持**: 已完整保持原有结构\n\n")
                    
                    f.write("### � 详细目录分布\n\n")
                    for dir_path in sorted(dirs):
                        dir_files = [f for f in image_files if Path(f).relative_to(self.input_dir).parent == dir_path]
                        f.write(f"- `{dir_path}`: {len(dir_files)} 张图像\n")
                else:
                    f.write(f"- **结构类型**: 扁平目录结构\n")
                    f.write(f"- **文件存放**: 所有文件在同一目录\n")
            f.write("\n")
            
            # 错误详情(如果有)
            if self.stats['error_details']:
                f.write("## ⚠️ 错误详情\n\n")
                for i, error in enumerate(self.stats['error_details'], 1):
                    f.write(f"{i}. **{error.get('file', 'Unknown')}**: {error.get('error', 'Unknown error')}\n")
                f.write("\n")
            
            # 优化建议
            f.write("## 💡 优化建议\n\n")
            if self.stats['success_rate'] < 90:
                f.write("⚠️ **成功率偏低建议**:\n")
                f.write("- 检查输入图像质量和清晰度\n")
                f.write("- 尝试不同的对齐方法\n")
                f.write("- 确认图像序列的一致性\n\n")
            
            if self.stats['average_processing_time'] > 5.0:
                f.write("⚡ **性能优化建议**:\n")
                f.write("- 检查GPU是否正常工作\n")
                f.write("- 考虑使用SuperPoint方法获得更快速度\n")
                f.write("- 适当降低图像分辨率\n\n")
            
            if self.selected_method == "enhanced" and hw_info.get('gpu_available'):
                f.write("🚀 **方法升级建议**:\n")
                f.write("- 检测到GPU可用，建议尝试SuperPoint方法获得更好效果\n")
                f.write("- 使用 `--method superpoint` 参数重新运行\n\n")
            
            # 结束信息
            f.write(f"## 🎉 处理完成\n\n")
            f.write(f"所有图像已成功对齐并保存到: `{self.output_dir}`\n\n")
            f.write("### 📄 相关文件\n\n")
            f.write("- 对齐后的图像: 在输出目录中\n")
            f.write("- 处理日志: 查看命令行输出\n")
            if self.selected_method == "superpoint":
                f.write("- SuperPoint详细报告: `superpoint_processing_report.md`\n")
            else:
                f.write("- Enhanced详细报告: `processing_report.md`\n")
            
            f.write("\n---\n")
            f.write("*Generated by TickTock Main Align Library - Enhanced Report Version*\n")
        
        logger.info(f"📝 详细处理报告已保存: {report_path}")
    
    def process_images(self):
        """主要的图像处理方法（增强统计版）"""
        start_time = time.time()
        self.stats['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
        
        logger.info("=" * 70)
        logger.info("🎯 TickTock Main Align 开始处理")
        logger.info(f"📂 输入: {self.input_dir}")
        logger.info(f"📂 输出: {self.output_dir}")
        logger.info(f"🔧 方法: {self.selected_method}")
        logger.info("=" * 70)
        
        try:
            # 检查输入目录结构
            image_files = self.get_image_files()
            if not image_files:
                logger.error("❌ 未找到图像文件")
                return False
            
            self.stats['total_images'] = len(image_files)
            
            # 检查是否需要保持目录结构
            has_subdirs = any(len(Path(f).relative_to(self.input_dir).parts) > 1 for f in image_files)
            
            if has_subdirs:
                logger.info("📁 检测到子目录结构，将保持目录结构")
                success = self.preserve_directory_structure()
            else:
                logger.info("📄 扁平目录结构，直接处理")
                success = self.aligner.process_images()
            
            end_time = time.time()
            duration = end_time - start_time
            self.stats['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
            self.stats['total_duration'] = duration
            
            # 从子模块处理报告中收集实际统计信息
            try:
                if success:
                    self._collect_detailed_stats_from_submodule()
                else:
                    self.stats['successful_alignments'] = 0
                    self.stats['failed_alignments'] = self.stats['total_images']
            except Exception as e:
                # 简单估算作为后备
                if success:
                    self.stats['successful_alignments'] = self.stats['total_images']
                    self.stats['failed_alignments'] = 0
                else:
                    self.stats['successful_alignments'] = 0
                    self.stats['failed_alignments'] = self.stats['total_images']
            
            if success:
                # 生成详细报告
                self._generate_main_report(image_files)
                
                logger.info("=" * 70)
                logger.info("🎉 Main Align 处理完成!")
                logger.info(f"⏱️  总耗时: {duration:.2f} 秒")
                logger.info(f"� 成功率: {self.stats['success_rate']:.1f}%")
                logger.info(f"�📂 结果保存在: {self.output_dir}")
                logger.info("=" * 70)
                return True
            else:
                # 生成错误报告
                self._generate_main_report(image_files)
                logger.error("❌ 处理失败")
                return False
                
        except Exception as e:
            end_time = time.time()
            self.stats['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
            self.stats['total_duration'] = end_time - start_time
            self.stats['error_details'].append({'error': str(e), 'file': 'general'})
            
            # 依然生成报告，即使有错误
            try:
                image_files = self.get_image_files() or []
                self._generate_main_report(image_files)
            except:
                pass
            
            logger.error(f"❌ 处理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TickTock Main Image Alignment')
    
    parser.add_argument('--input', '-i', default='NPU-Everyday-Sample',
                       help='输入图像文件夹路径 (默认: NPU-Everyday-Sample)')
    
    parser.add_argument('--output', '-o', default='NPU-Everyday-Sample_Aligned',
                       help='输出图像文件夹路径 (默认: NPU-Everyday-Sample_Aligned)')
    
    parser.add_argument('--reference', '-r', type=int, default=0,
                       help='参考图像索引 (默认: 0)')
    
    parser.add_argument('--method', '-m', 
                       choices=['superpoint', 'enhanced', 'auto'],
                       default='auto',
                       help='对齐方法选择 (默认: auto - 自动选择最佳方法)')
    
    args = parser.parse_args()
    
    # 打印启动信息
    print("🎯 TickTock Main Align Library")
    print("=" * 70)
    print(f"📂 输入目录: {args.input}")
    print(f"📂 输出目录: {args.output}")
    print(f"🔧 对齐方法: {args.method}")
    print(f"📍 参考图像: 第 {args.reference + 1} 张")
    print("=" * 70)
    
    try:
        # 创建主要对齐器
        main_aligner = MainAlign(
            input_dir=args.input,
            output_dir=args.output,
            reference_index=args.reference,
            method=args.method
        )
        
        # 执行对齐处理
        success = main_aligner.process_images()
        
        if success:
            print("=" * 70)
            print("✅ 图像对齐处理完成！")
            print(f"📂 结果保存在: {args.output}")
            print("📝 查看详细报告: main_align_report.md")
            print("=" * 70)
        else:
            print("❌ 处理失败，请检查日志信息")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"启动失败: {e}")
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()