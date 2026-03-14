# 🧩 智能马赛克拼图模块 (Mosaic)

## 📖 模块简介

智能马赛克拼图模块将对齐后的图像序列智能组合成精美的拼图展示。支持多种布局模式和智能尺寸适配，使用高质量图像处理算法，自动生成适合不同展示场景的马赛克效果图。特别针对NPU建筑图像序列优化，展现时间变化的视觉效果。

## � 多布局模式

### 📐 网格马赛克 (Grid Layout)
- **规整排列**: 按照矩形网格整齐排列所有图像
- **智能计算**: 自动计算最优的行列数组合
- **等比缩放**: 所有图像统一尺寸，保持视觉一致性
- **适用场景**: 展示全貌、打印输出、规整展示

### ⏰ 时间线马赛克 (Timeline Layout)  
- **时序排列**: 按照拍摄时间顺序横向或纵向排列
- **渐变效果**: 可选的时间渐变色彩效果
- **紧凑布局**: 最大化利用空间展示更多图像
- **适用场景**: 展示变化过程、时间轴效果

### 📱 缩略图概览 (Thumbnail Overview)
- **快速浏览**: 生成小尺寸缩略图便于快速浏览
- **信息保留**: 保持图像基本信息和视觉特征
- **内存友好**: 低内存占用，适合大批量图像
- **适用场景**: 快速预览、目录索引、移动设备展示

## ✨ 技术特性

### 🔧 智能算法
- **自适应布局**: 根据图像数量自动优化布局参数
- **质量保持**: 使用LANCZOS算法保证缩放质量
- **内存管理**: 分批处理避免大量图像导致内存溢出  
- **错误处理**: 完善的异常处理和错误恢复机制

### 🎯 输出控制
- **多尺寸支持**: 支持不同输出尺寸需求
- **格式灵活**: JPEG、PNG等多种输出格式
- **质量可调**: 可配置的输出质量和压缩参数
- **信息报告**: 自动生成马赛克信息和统计报告

## 🚀 使用方法

### 1. 作为独立模块使用
```python
from Mosaic.mosaic_pic import MosaicGenerator

# 创建马赛克生成器
generator = MosaicGenerator(
    input_dir="NPU-Everyday-Sample_aligned",
    output_dir="NPU-Everyday-Sample_mosaic"
)

# 生成网格布局拼接图
generator.create_grid_mosaic(
    output_filename="grid_mosaic.jpg",
    cell_size=(400, 300),
    margin=10
)

# 生成时间线布局
generator.create_timeline_mosaic(
    output_filename="timeline_mosaic.jpg",
    height=800,
    margin=5
)
```

### 2. 通过流水线使用
```bash
# 仅执行马赛克拼接步骤
python pipeline.py NPU-Everyday-Sample --mosaic-only

# 作为流水线的一部分
python pipeline.py NPU-Everyday-Sample --steps resize align mosaic
```

### 3. 批量生成多种布局
```python
# 生成所有预设布局
layouts = ['grid', 'timeline', 'waterfall', 'freeform']
for layout in layouts:
    generator.create_mosaic(layout=layout)
```

## 📋 参数配置

### MosaicGenerator类参数
```python
class MosaicGenerator:
    def __init__(self, input_dir, output_dir, quality=95):
        """
        Args:
            input_dir (str): 输入图像文件夹路径
            output_dir (str): 输出马赛克图像文件夹路径
            quality (int): JPEG输出质量 (1-100, 默认95)
        """
```

### 布局参数详解

#### 网格布局参数
```python
def create_grid_mosaic(
    self, 
    output_filename="grid_mosaic.jpg",
    cell_size=(400, 300),      # 单元格尺寸 (宽, 高)
    margin=10,                 # 图像间距 (像素)
    cols=None,                 # 列数 (None=自动计算)
    background_color=(255, 255, 255)  # 背景颜色 (R, G, B)
):
```

#### 时间线布局参数  
```python
def create_timeline_mosaic(
    self,
    output_filename="timeline_mosaic.jpg", 
    height=600,                # 图像高度 (像素)
    margin=5,                  # 图像间距 (像素)
    direction='horizontal'     # 排列方向 ('horizontal', 'vertical')
):
```

#### 瀑布流布局参数
```python
def create_waterfall_mosaic(
    self,
    output_filename="waterfall_mosaic.jpg",
    column_width=300,          # 列宽 (像素) 
    margin=10,                 # 图像间距 (像素)
    num_columns=3              # 列数
):
```

## 🔧 技术实现

### 核心算法流程

#### 1. 智能网格计算
```python
def calculate_grid_layout(self, num_images, max_width=4000, max_height=3000):
    """计算最佳网格布局"""
    # 计算接近正方形的网格
    cols = math.ceil(math.sqrt(num_images))
    rows = math.ceil(num_images / cols)
    
    # 优化长宽比
    aspect_ratios = []
    for c in range(max(1, cols-2), cols+3):
        r = math.ceil(num_images / c)
        if c * r >= num_images:
            ratio = abs((c / r) - 1.0)  # 越接近1越好
            aspect_ratios.append((ratio, c, r))
    
    # 选择最佳比例
    _, best_cols, best_rows = min(aspect_ratios)
    
    # 计算单元格大小
    cell_width = min(max_width // best_cols, 500)
    cell_height = min(max_height // best_rows, 400)
    
    return best_cols, best_rows, (cell_width, cell_height)
```

## 📊 处理过程详解

### 典型处理日志
```
2025-09-30 12:45:23,156 - INFO - 开始创建马赛克拼接图像
2025-09-30 12:45:23,156 - INFO - 输入文件夹: NPU-Everyday-Sample_Output\Aligned
2025-09-30 12:45:23,164 - INFO - 找到 6 张图像文件
2025-09-30 12:45:23,164 - INFO - 输出文件夹: NPU-Everyday-Sample_Output\Mosaic

布局计算结果:
2025-09-30 12:45:23,164 - INFO - 网格布局: 3列 × 2行
2025-09-30 12:45:23,164 - INFO - 单元格尺寸: 400×300像素
2025-09-30 12:45:23,164 - INFO - 画布尺寸: 1240×630像素

马赛克生成进度:
2025-09-30 12:45:23,164 - INFO - 创建网格马赛克: grid_mosaic.jpg
2025-09-30 12:45:26,331 - INFO - ✅ 网格马赛克创建成功 (285KB)
2025-09-30 12:45:26,331 - INFO - 创建时间线马赛克: timeline_mosaic.jpg  
2025-09-30 12:45:29,486 - INFO - ✅ 时间线马赛克创建成功 (394KB)
2025-09-30 12:45:29,487 - INFO - 创建瀑布流马赛克: waterfall_mosaic.jpg
2025-09-30 12:45:32,641 - INFO - ✅ 瀑布流马赛克创建成功 (356KB)
2025-09-30 12:45:32,641 - INFO - 创建自由拼接马赛克: freeform_mosaic.jpg
2025-09-30 12:45:35,800 - INFO - ✅ 自由拼接马赛克创建成功 (421KB)
```

### 布局效果对比
| 布局类型 | 适用场景 | 画布尺寸 | 文件大小 | 视觉特点 |
|----------|----------|----------|----------|----------|
| 网格布局 | 展示墙、相册 | 1240×630 | 285KB | 规整、对称 |
| 时间线布局 | 进度展示 | 2394×600 | 394KB | 流动、连续 |
| 瀑布流布局 | 艺术展示 | 930×800 | 356KB | 动态、灵活 |
| 自由拼接 | 创意设计 | 1200×900 | 421KB | 个性、多样 |

## � 相关文档

- [主项目文档](../README.md)
- [图像对齐模块](../Align/README.md)
- [延时摄影模块](../Timelapse/README.md)
- [PIL/Pillow文档](https://pillow.readthedocs.io/)

---

**模块版本**: v2.0.0  
**最后更新**: 2025-09-30  