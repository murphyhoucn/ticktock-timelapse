#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TickTock-Align-NPU Library 完整流水线

整合所有功能的完整处理流水线：
1. 图像放缩统一 (Resize) - 统一两种手机的分辨率到4096×3072
2. 图像对齐 (Align) - 使用SIFT特征点对齐图像序列  
3. 延时摄影 (Timelapse) - 生成延时摄影视频
4. 马赛克拼图 (Mosaic) - 生成马赛克效果拼图
5. 统计信息 (Statistics) - 生成拍摄统计报告

输入: NPU-Everyday 或 NPU-Every-Sample
输出: {输入文件夹名称}_Output 文件夹，包含所有处理结果
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import shutil
from datetime import datetime

from Resize.image_resizer import process_directory as resize_images
from Align.main_align import MainAlign
from Timelapse.create_timelapse import create_file_list, create_timelapse_video
from Stas.visual_report_generator import generate_npu_statistics_reports
from PIL import Image
from Timelapse.utils import preprocess_add_timestamp

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印程序横幅"""
    print("████████╗██╗ ██████╗██╗  ██╗████████╗ ██████╗  ██████╗██╗  ██╗")
    print("╚══██╔══╝██║██╔════╝██║ ██╔╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝")
    print("   ██║   ██║██║     █████╔╝    ██║   ██║   ██║██║     █████╔╝ ")
    print("   ██║   ██║██║     ██╔═██╗    ██║   ██║   ██║██║     ██╔═██╗ ")
    print("   ██║   ██║╚██████╗██║  ██╗   ██║   ╚██████╔╝╚██████╗██║  ██╗")
    print("   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝")
    print()
    print("TickTock-Align-NPU Library 完整流水线")
    print("NPU建筑物图像处理 - 完整工作流程")
    print("=" * 60)

class TickTockPipeline:
    """TickTock 完整处理流水线"""
    
    @staticmethod
    def get_sorted_image_files(directory, extensions=None):
        """获取按时间顺序排序的图像文件列表"""
        if extensions is None:
            extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        image_files = []
        for ext in extensions:
            image_files.extend(list(directory.rglob(f"*{ext}")))
            image_files.extend(list(directory.rglob(f"*{ext.upper()}")))
        
        # 去重并按时间顺序排序（先按文件夹，再按文件名）
        image_files = sorted(set(image_files), key=lambda x: (str(x.parent), x.name))
        return image_files
    
    def __init__(self, input_dir, output_dir=None, steps=None, align_method="superpoint"):
        """
        初始化处理流水线
        
        Args:
            input_dir (str): 输入目录 (NPU-Everyday 或 NPU-Everyday-Sample)
            steps (list): 要执行的步骤列表，None表示执行所有步骤
                        可选: ['resize', 'align', 'timelapse', 'mosaic', 'stats']
            align_method (str): 对齐方法选择
                        可选: ['superpoint', 'enhanced', 'auto']
                        默认: 'superpoint' (深度学习方法，LoFTR+SuperPoint)
        """
        self.input_dir = Path(input_dir)
        self.input_name = self.input_dir.name
        self.output_dir = Path(f"{self.input_name}_Output")
        
        # 各个步骤的输出目录
        self.rescale_dir = self.output_dir / "Rescaled"
        self.align_dir = self.output_dir / "Aligned"
        self.timelapse_dir = self.output_dir / "Timelapse"
        self.mosaic_dir = self.output_dir / "Mosaic"
        self.stats_dir = self.output_dir / "Statistics"
        
        # 要执行的步骤
        self.steps = steps or ['resize', 'align', 'timelapse', 'mosaic', 'stats']
        
        # 深度学习对齐方法
        self.align_method = align_method
        
        logger.info(f"初始化NPU处理流水线")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"对齐方法: {self.align_method}")
        logger.info(f"执行步骤: {', '.join(self.steps)}")
    
    def check_environment(self):
        """检查运行环境"""
        logger.info("检查运行环境...")
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {self.input_dir}")
        
        # 检查图片数量
        image_files = self.get_sorted_image_files(self.input_dir)
        
        if len(image_files) == 0:
            raise ValueError(f"输入目录中没有找到图片文件: {self.input_dir}")
        
        logger.info(f"发现 {len(image_files)} 个图片文件（按时间顺序排列）")
        
        # 打印前几个文件以验证顺序
        logger.info("文件顺序示例:")
        for i, file in enumerate(image_files[:5]):
            logger.info(f"  {i+1}. {file.relative_to(self.input_dir)}")
        if len(image_files) > 5:
            logger.info(f"  ... 还有 {len(image_files)-5} 个文件")
        return True
    
    def step_1_resize(self):
        """步骤1: 图像放缩统一"""
        if 'resize' not in self.steps:
            logger.info("跳过步骤1: 图像放缩")
            return
        
        logger.info("=" * 60)
        logger.info("步骤1: 图像放缩统一")
        logger.info("将所有图像统一放缩到 4096×3072 像素")
        logger.info("=" * 60)
        
        try:
            # 使用现有的image_resizer
            resize_images(
                input_dir=str(self.input_dir),
                output_dir=str(self.rescale_dir),
                target_size=(4096, 3072)
            )
            logger.info("✅ 步骤1完成: 图像放缩统一")
        except Exception as e:
            logger.error(f"❌ 步骤1失败: {e}")
            raise
    
    def step_2_align(self):
        """步骤2: 图像对齐"""
        if 'align' not in self.steps:
            logger.info("跳过步骤2: 图像对齐")
            return
        
        logger.info("=" * 60)
        logger.info("步骤2: 图像对齐")
        logger.info("使用深度学习方法对齐图像序列 (LoFTR + 传统方法回退)")
        logger.info("=" * 60)
        
        # 确定输入目录：如果做了放缩就用放缩后的，否则用原始的
        source_dir = self.rescale_dir if 'resize' in self.steps and self.rescale_dir.exists() else self.input_dir
        
        try:
            # 创建输出目录
            self.align_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查源目录是否存在图像文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            image_files = []
            for ext in image_extensions:
                image_files.extend(list(Path(source_dir).rglob(f"*{ext}")))
                image_files.extend(list(Path(source_dir).rglob(f"*{ext.upper()}")))
            
            if not image_files:
                logger.warning(f"⚠️ 在源目录 {source_dir} 中没有找到图像文件，跳过对齐步骤")
                return
            
            logger.info(f"在源目录中找到 {len(image_files)} 个图像文件")
            
            # 使用MainAlign进行对齐（支持superpoint、enhanced、auto方法）
            aligner = MainAlign(
                input_dir=str(source_dir),
                output_dir=str(self.align_dir),
                reference_index=0,
                method=self.align_method  # 在初始化时指定对齐方法
            )
            aligner.process_images()  # 执行对齐处理
            
            logger.info("✅ 步骤2完成: 图像对齐")
        except Exception as e:
            logger.error(f"❌ 步骤2失败: {e}")
            raise
    
    def step_3_timelapse(self):
        """步骤3: 延时摄影"""
        if 'timelapse' not in self.steps:
            logger.info("跳过步骤3: 延时摄影")
            return
        
        logger.info("=" * 60)
        logger.info("步骤3: 延时摄影")
        logger.info("生成延时摄影视频")
        logger.info("=" * 60)
        
        # 确定输入目录：优先使用对齐后的图像，但要检查是否有文件
        source_dir = None
        
        # 检查对齐后的图像
        if 'align' in self.steps and self.align_dir.exists():
            align_files = list(self.align_dir.rglob("*.jpg")) + list(self.align_dir.rglob("*.jpeg")) + list(self.align_dir.rglob("*.png"))
            align_files = sorted(set(align_files), key=lambda x: (str(x.parent), x.name))
            if align_files:
                source_dir = self.align_dir
                logger.info(f"使用对齐后的图像: {len(align_files)} 个文件（按时间顺序）")
                print(f"加 时间 水印, source_dir = {source_dir}")
                source_dir = preprocess_add_timestamp(source_dir)
        
        # 如果对齐目录没有文件，检查放缩后的图像
        if source_dir is None and 'resize' in self.steps and self.rescale_dir.exists():
            rescale_files = list(self.rescale_dir.rglob("*.jpg")) + list(self.rescale_dir.rglob("*.jpeg")) + list(self.rescale_dir.rglob("*.png"))
            if rescale_files:
                source_dir = self.rescale_dir
                logger.info(f"使用放缩后的图像: {len(rescale_files)} 个文件")
        
        # 最后使用原始图像
        if source_dir is None:
            source_dir = self.input_dir
            original_files = list(self.input_dir.rglob("*.jpg")) + list(self.input_dir.rglob("*.jpeg")) + list(self.input_dir.rglob("*.png"))
            logger.info(f"使用原始图像: {len(original_files)} 个文件")
        
        try:
            # 创建输出目录
            self.timelapse_dir.mkdir(parents=True, exist_ok=True)
            
            # 验证源目录
            if source_dir is None:
                raise ValueError("没有找到可用的图像文件")
            
            logger.info(f"延时摄影使用源目录: {source_dir}")
            
            # 创建自定义的文件列表生成函数
            def create_custom_file_list_with_resolution(input_dir, output_file):
                """为指定目录创建文件列表并获取原始分辨率"""
                input_path = Path(input_dir)
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
                
                # 收集所有图像文件
                image_files = []
                for ext in image_extensions:
                    image_files.extend(input_path.rglob(f"*{ext}"))
                    image_files.extend(input_path.rglob(f"*{ext.upper()}"))
                
                # 去重
                image_files = list(set(image_files))
                
                # 按完整路径排序，确保时间顺序正确
                image_files = sorted(image_files, key=lambda x: (str(x.parent), x.name))
                
                if not image_files:
                    raise ValueError(f"在目录 {input_dir} 中没有找到图像文件")
                
                # 获取第一张图片的分辨率作为原始分辨率
                try:
                    with Image.open(image_files[0]) as img:
                        original_width, original_height = img.size
                    logger.info(f"📷 原始图片分辨率: {original_width}x{original_height}")
                except Exception as e:
                    logger.warning(f"无法获取图片分辨率: {e}，使用默认设置")
                    original_width, original_height = 1920, 1080
                
                # 写入文件列表
                with open(output_file, 'w', encoding='utf-8') as f:
                    for img_file in image_files:
                        abs_path = img_file.resolve().as_posix()
                        f.write(f"file '{abs_path}'\n")
                
                logger.info(f"创建文件列表: {len(image_files)} 个图像文件")
                return len(image_files), (original_width, original_height)
            
            # 生成文件列表并获取原始分辨率
            file_list_path = self.timelapse_dir / "file_list.txt"
            image_count, original_resolution = create_custom_file_list_with_resolution(str(source_dir), str(file_list_path))
            
            original_width, original_height = original_resolution
            
            # 计算三个质量等级的分辨率
            # 高质量: 原始分辨率
            hq_resolution = f"{original_width}x{original_height}"
            
            # 标准质量: 75%原始分辨率
            std_width = int(original_width * 0.75)
            std_height = int(original_height * 0.75)
            std_width = std_width - (std_width % 2)  # 确保是偶数
            std_height = std_height - (std_height % 2)
            std_resolution = f"{std_width}x{std_height}"
            
            # 预览质量: 50%原始分辨率
            prev_width = int(original_width * 0.5)
            prev_height = int(original_height * 0.5)
            prev_width = prev_width - (prev_width % 2)
            prev_height = prev_height - (prev_height % 2)
            prev_resolution = f"{prev_width}x{prev_height}"
            
            logger.info(f"🎬 视频质量设置:")
            logger.info(f"   高质量: {hq_resolution} (CRF 18)")
            logger.info(f"   标准质量: {std_resolution} (CRF 23)")
            logger.info(f"   预览质量: {prev_resolution} (CRF 28)")
            
            # 生成三种质量的视频（统一使用30fps）
            video_configs = [
                ("preview", prev_resolution, 28, "预览版"),
                ("standard", std_resolution, 23, "标准版"), 
                ("hq", hq_resolution, 18, "高质量版")
            ]
            
            for name, resolution, quality, desc in video_configs:
                output_video = self.timelapse_dir / f"timelapse_{name}.mp4"
                logger.info(f"生成{desc} (30fps, {resolution}): {output_video.name}")
                
                create_timelapse_video(
                    str(file_list_path),
                    str(output_video),
                    framerate=30,
                    quality=quality,
                    resolution=resolution
                )
            
            logger.info("✅ 步骤3完成: 延时摄影")
        except Exception as e:
            logger.error(f"❌ 步骤3失败: {e}")
            raise
    
    def step_4_mosaic(self):
        """步骤4: 马赛克拼图"""
        if 'mosaic' not in self.steps:
            logger.info("跳过步骤4: 马赛克拼图")
            return
        
        logger.info("=" * 60)
        logger.info("步骤4: 马赛克拼图")
        logger.info("生成马赛克拼图效果")
        logger.info("=" * 60)
        
        # 确定输入目录：优先使用对齐后的图像
        source_dir = None
        
        # # 检查对齐后的图像
        # if 'align' in self.steps and self.align_dir.exists():
        #     align_files = list(self.align_dir.rglob("*.jpg")) + list(self.align_dir.rglob("*.jpeg")) + list(self.align_dir.rglob("*.png"))
        #     if align_files:
        #         source_dir = self.align_dir
        #         logger.info(f"使用对齐后的图像: {len(align_files)} 个文件")
        
        # 如果对齐目录没有文件，检查放缩后的图像
        if source_dir is None and 'resize' in self.steps and self.rescale_dir.exists():
            rescale_files = list(self.rescale_dir.rglob("*.jpg")) + list(self.rescale_dir.rglob("*.jpeg")) + list(self.rescale_dir.rglob("*.png"))
            if rescale_files:
                source_dir = self.rescale_dir
                logger.info(f"使用放缩后的图像: {len(rescale_files)} 个文件")
        
        # 最后使用原始图像
        if source_dir is None:
            source_dir = self.input_dir
            original_files = list(self.input_dir.rglob("*.jpg")) + list(self.input_dir.rglob("*.jpeg")) + list(self.input_dir.rglob("*.png"))
            logger.info(f"使用原始图像: {len(original_files)} 个文件")
        
        try:
            # 创建输出目录
            self.mosaic_dir.mkdir(parents=True, exist_ok=True)
            
            # 验证源目录
            if source_dir is None:
                raise ValueError("没有找到可用的图像文件")
            
            logger.info(f"马赛克生成使用源目录: {source_dir}")
            
            # 导入并使用马赛克生成器
            from Mosaic.mosaic_pic import MosaicGenerator
            
            # 创建马赛克生成器
            generator = MosaicGenerator(
                input_dir=str(source_dir),
                output_dir=str(self.mosaic_dir),
                target_width=4096,
                max_output_size=16384
            )
            
            # 生成马赛克
            success = generator.generate_mosaics()
            
            if success:
                logger.info("✅ 步骤4完成: 马赛克拼图")
            else:
                logger.warning("⚠️ 马赛克拼图生成过程中出现问题")
                
        except Exception as e:
            logger.error(f"❌ 步骤4失败: {e}")
            # 创建占位文件以表示尝试过但失败
            try:
                placeholder = self.mosaic_dir / "mosaic_error.txt"
                placeholder.write_text(f"马赛克拼图生成失败:\n{str(e)}\n", encoding='utf-8')
            except:
                pass
            raise
    
    def step_5_stats(self):
        """步骤5: 统计信息"""
        if 'stats' not in self.steps:
            logger.info("跳过步骤5: 统计信息")
            return
        
        logger.info("=" * 60)
        logger.info("步骤5: 统计信息")
        logger.info("生成拍摄统计报告")
        logger.info("=" * 60)
        
        try:
            # 创建输出目录
            self.stats_dir.mkdir(parents=True, exist_ok=True)
            
            # 导入统计生成器
            import sys
            sys.path.append(str(Path(__file__).parent / "Stas"))
            
            try: 
                # 生成统计报告
                logger.info("调用统计分析模块...")
                results = generate_npu_statistics_reports(
                    base_directory=str(self.input_dir),
                    start_date="2023-09-01",
                    end_date="2026-04-30",
                    output_dir=str(self.stats_dir)
                )
                
                if results:
                    logger.info(f"✅ Markdown报告：{Path(results['markdown_path']).name}")
                    if results['png_path']:
                        logger.info(f"✅ PNG图表：{Path(results['png_path']).name}")
                    
                    stats = results['stats']
                    logger.info(f"📊 统计摘要：总天数 {stats['total_days']}，拍照天数 {stats['photo_days']}，总照片 {stats['total_photos']} 张")
                else:
                    logger.error("统计报告生成失败")
                    
            except ImportError as e:
                logger.error(f"❌ 无法导入统计模块: {e}")
                # 创建占位文件
                placeholder = self.stats_dir / "stats_placeholder.txt"
                placeholder.write_text("统计模块导入失败，请检查依赖包是否安装完整\n", encoding='utf-8')
            
            logger.info("✅ 步骤5完成: 统计信息")
        except Exception as e:
            logger.error(f"❌ 步骤5失败: {e}")
            raise
    
    def run_pipeline(self):
        """运行完整流水线"""
        start_time = datetime.now()
        logger.info(f"开始执行NPU处理流水线: {start_time}")
        
        try:
            # 检查环境
            self.check_environment()
            
            # 执行各个步骤
            self.step_1_resize()
            self.step_2_align()
            self.step_3_timelapse()
            self.step_4_mosaic()
            self.step_5_stats()
            
            # 生成完成报告
            self.generate_report()
            
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"✅ 流水线执行完成! 耗时: {duration}")
            
        except Exception as e:
            logger.error(f"❌ 流水线执行失败: {e}")
            raise
    
    def generate_report(self):
        """生成处理报告"""
        report_path = self.output_dir / "processing_report.md"
        
        report_content = f"""# NPU图像处理报告

## 基本信息
- **输入目录**: {self.input_dir}
- **输出目录**: {self.output_dir}
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **执行步骤**: {', '.join(self.steps)}

## 处理结果

### 1. 图像放缩统一
- **输出目录**: {self.rescale_dir}
- **目标尺寸**: 4096×3072 像素
- **状态**: {'✅ 完成' if 'resize' in self.steps else '⏭️ 跳过'}

### 2. 图像对齐
- **输出目录**: {self.align_dir}
- **对齐方法**: SIFT特征点匹配
- **状态**: {'✅ 完成' if 'align' in self.steps else '⏭️ 跳过'}

### 3. 延时摄影
- **输出目录**: {self.timelapse_dir}
- **视频格式**: MP4 (H.264编码)
- **状态**: {'✅ 完成' if 'timelapse' in self.steps else '⏭️ 跳过'}

### 4. 马赛克拼图
- **输出目录**: {self.mosaic_dir}
- **状态**: {'✅ 完成' if 'mosaic' in self.steps else '⏭️ 跳过'}

### 5. 统计信息
- **输出目录**: {self.stats_dir}
- **状态**: {'✅ 完成' if 'stats' in self.steps else '⏭️ 跳过'}

## 文件结构

```
{self.output_dir}/
├── Aligned/           # 对齐后的图像
├── Timelapse/         # 延时摄影视频
├── Mosaic/            # 马赛克拼图
├── Statistics/        # 统计报告
└── processing_report.md  # 处理报告
```

---
生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_path.write_text(report_content, encoding='utf-8')
        logger.info(f"生成处理报告: {report_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='NPU图像处理完整流水线')
    
    parser.add_argument('input_dir', 
                       help='输入目录 (NPU-Everyday 或 NPU-Everyday-Sample)')
    
    parser.add_argument('--steps', 
                       nargs='+',
                       choices=['resize', 'align', 'timelapse', 'mosaic', 'stats'],
                       help='要执行的步骤 (默认执行所有步骤)')
    
    parser.add_argument('--align-method', 
                       choices=['superpoint', 'enhanced', 'auto'],
                       default='superpoint',
                       help='对齐方法选择 (superpoint: 深度学习方法; enhanced: 增强传统方法; auto: 自动选择)')
    
    parser.add_argument('--resize-only', 
                       action='store_true',
                       help='仅执行图像放缩')
    
    parser.add_argument('--align-only', 
                       action='store_true',
                       help='仅执行图像对齐')
    
    parser.add_argument('--timelapse-only', 
                       action='store_true',
                       help='仅执行延时摄影')
        
    parser.add_argument('--mosaic-only', 
                       action='store_true',
                       help='仅执行马赛克拼图')

    parser.add_argument('--stats-only', 
                       action='store_true',
                       help='仅执行统计信息')

    args = parser.parse_args()
    
    # 处理快捷选项
    if args.resize_only:
        args.steps = ['resize']
    elif args.align_only:
        args.steps = ['align']
    elif args.timelapse_only:
        args.steps = ['timelapse']
    elif args.mosaic_only:
        args.steps = ['mosaic']
    elif args.stats_only:
        args.steps = ['stats']

    print_banner()

    # 创建并运行流水线
    pipeline = TickTockPipeline(args.input_dir, steps=args.steps, align_method=args.align_method)
    pipeline.run_pipeline()
    
if __name__ == "__main__":
    main()