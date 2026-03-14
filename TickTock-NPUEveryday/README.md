# TickTock NPU Everyday

████████╗██╗ ██████╗██╗  ██╗████████╗ ██████╗  ██████╗██╗  ██╗
╚══██╔══╝██║██╔════╝██║ ██╔╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝
   ██║   ██║██║     █████╔╝    ██║   ██║   ██║██║     █████╔╝ 
   ██║   ██║██║     ██╔═██╗    ██║   ██║   ██║██║     ██╔═██╗ 
   ██║   ██║╚██████╗██║  ██╗   ██║   ╚██████╔╝╚██████╗██║  ██╗
   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝

**🎯 项目简介**：基于深度学习和计算机视觉技术的NPU建筑物图像智能处理流水线  
**📥 输入**: NPU-Everyday 或 NPU-Everyday-Sample 文件夹中的建筑物图像序列  
**📤 输出**: {输入文件夹名称}_Output 文件夹中的完整处理结果

集成了图像统一放缩、**深度学习智能对齐**、**高质量延时摄影**、马赛克拼图和统计分析。支持GPU加速，提供三种对齐算法和自适应质量设置。

---

## 🚀 快速开始

### 方式1：一键启动脚本（推荐新用户）
```bash
# Windows用户
./run_pipeline.bat

# Linux用户
./run_pipeline.sh

# 交互式菜单选择：
# 1. 快速测试 (NPU-Everyday-Sample) - 30张图像，约4分钟
# 2. 完整处理 (NPU-Everyday) - 582+张图像，约1-2小时
# 3-5. 单步处理模式（仅执行特定功能）
# 6. 自定义步骤组合
```

### 方式2：命令行直接运行
```bash
# 安装依赖
pip install -r requirements.txt

# 完整流水线处理（推荐）
python pipeline.py NPU-Everyday-Sample

# 自定义步骤组合
python pipeline.py NPU-Everyday-Sample --steps resize align timelapse mosaic stats

# 对齐方法选择
python pipeline.py NPU-Everyday-Sample --align-method superpoint  # 深度学习方法（推荐）
python pipeline.py NPU-Everyday-Sample --align-method enhanced   # 增强传统方法
python pipeline.py NPU-Everyday-Sample --align-method auto       # 自动选择最佳方法

# 单步处理
python pipeline.py NPU-Everyday-Sample --resize-only    # 仅图像放缩
python pipeline.py NPU-Everyday-Sample --align-only     # 仅图像对齐
python pipeline.py NPU-Everyday-Sample --timelapse-only # 仅延时摄影
```

### 环境检查
```bash
# 检查运行环境和依赖
python test_environment.py
```

---

## 🎯 核心功能

### 🔄 步骤1：图像统一放缩 (Resize)
- **多设备支持**: 自动识别HUAWEI P30 Pro (3648×2736) 和 vivo X100 Pro (4096×3072)
- **智能放缩**: 统一放缩到4096×3072像素，保持最佳质量
- **高质量重采样**: 使用LANCZOS算法确保放缩质量
- **批量处理**: 自动处理整个文件夹的图像序列
- **📚 详细文档**: [Resize/README.md](Resize/README.md)

### 🎯 步骤2：深度学习智能对齐 (Align)
- **三种对齐方法**: SuperPoint(深度学习) / Enhanced(增强传统) / Auto(自动选择)
- **LoFTR深度学习**: 现代Transformer架构，100%成功率
- **GPU加速**: CUDA支持，处理速度提升10倍
- **智能回退**: 深度学习失败时自动回退到传统方法
- **夜间优化**: 特殊的夜间图像处理算法
- **目录结构保持**: 自动保持原有的文件夹结构
- **📚 详细文档**: [Align/README.md](Align/README.md)

### 🎬 步骤3：高质量延时摄影 (Timelapse)
- **动态分辨率**: 自动检测原始图片分辨率，生成三个质量等级
- **高质量版**: 100%原始分辨率(4096×3072) + CRF 18
- **标准版**: 75%分辨率(3072×2304) + CRF 23  
- **预览版**: 50%分辨率(2048×1536) + CRF 28
- **统一30fps**: 所有视频统一使用30帧/秒，流畅播放
- **智能压缩**: 根据质量等级自动调整文件大小
- **📚 详细文档**: [Timelapse/README.md](Timelapse/README.md)

### 🧩 步骤4：马赛克拼图生成 (Mosaic)
- **多种布局**: 网格马赛克、时间线马赛克、缩略图概览
- **智能内存管理**: 自动缩放避免内存溢出
- **高质量缩放**: LANCZOS算法保持图像质量
- **自适应布局**: 根据图像数量自动计算最优布局
- **详细报告**: 自动生成马赛克信息报告
- **📚 详细文档**: [Mosaic/README.md](Mosaic/README.md)

### 📊 步骤5：统计分析 (Statistics)
- **GitHub风格图表**: 类似GitHub提交图的拍摄日历
- **详细报告**: Markdown格式的统计报告
- **时间范围分析**: 按日、月、年统计拍摄频率
- **设备分析**: 分析不同设备的拍摄比例
- **可视化输出**: PNG图表和Markdown报告
- **📚 详细文档**: [Stas/README.md](Stas/README.md)

---

## 🎬 工作流程

```
📷 原始图像序列 (NPU-Everyday / NPU-Everyday-Sample)
    ↓
🔄 步骤1：图像统一放缩 (Resize)
    │ 3648×2736 / 4096×3072 → 4096×3072
    │ 输出：{输入目录}_Output/Rescaled/
    ↓
🎯 步骤2：深度学习智能对齐 (Align)
    │ SuperPoint(LoFTR+GPU加速) / Enhanced(增强SIFT) / Auto(智能选择)
    │ 100%成功率，处理速度提升10倍
    │ 输出：{输入目录}_Output/Aligned/
    ↓
🎬 步骤3：高质量延时摄影 (Timelapse)  
    │ 动态分辨率检测，三质量等级(100%/75%/50%原分辨率)
    │ 统一30fps，CRF质量控制 (18/23/28)
    │ 输出：{输入目录}_Output/Timelapse/
    ↓
🧩 步骤4：马赛克拼图 (Mosaic)
    │ 网格布局 + 时间线布局 + 缩略图概览
    │ 输出：{输入目录}_Output/Mosaic/
    ↓
📊 步骤5：统计分析 (Statistics)
    │ GitHub风格图表 + Markdown报告
    │ 输出：{输入目录}_Output/Statistics/
    ↓
📦 完整结果汇总
    └── {输入目录}_Output/
        ├── processing_report.md  # 完整处理报告
        ├── Rescaled/            # 放缩后图像
        ├── Aligned/             # 对齐后图像
        ├── Timelapse/           # 延时摄影视频
        ├── Mosaic/              # 马赛克拼图
        └── Statistics/          # 统计分析
```

---

## 📁 项目结构

```
TickTock-NPUEveryday/
├── 📊 数据集
│   ├── NPU-Everyday/               # 完整数据集：所有月份的图像
│   │   ├── 2023.09/ ... 2025.09/
│   │   └── (582+ 张图像)
│   └── NPU-Everyday-Sample/        # 采样数据集：3个月份用于快速测试
│       ├── 2023.09/ (10张)
│       ├── 2024.09/ (10张)
│       └── 2025.09/ (10张)
│
├── 🔧 核心程序
│   ├── pipeline.py                 # 🚀 完整流水线主程序
│   ├── run_pipeline.bat            # 🖱️ Windows一键启动脚本
│   ├── test_environment.py         # 🔍 环境检查工具
│   └── main.py                     # 📜 原有主程序(兼容性)
│
├── 📦 功能模块
│   ├── Resize/                     # 图像统一放缩
│   │   ├── image_resizer.py        # 核心放缩算法
│   │   └── README.md               # 模块说明文档
│   ├── Align/                      # 深度学习智能对齐
│   │   ├── main_align.py           # 统一对齐接口
│   │   ├── superpoint.py           # 深度学习对齐(LoFTR)
│   │   ├── enhanced.py             # 增强传统对齐(SIFT+)
│   │   └── README.md               # 模块说明文档
│   ├── Timelapse/                  # 延时摄影制作
│   │   ├── create_timelapse.py     # FFmpeg视频生成
│   │   └── README.md               # 模块说明文档
│   ├── Mosaic/                     # 马赛克拼图生成
│   │   ├── mosaic_pic.py           # 马赛克拼图算法
│   │   └── README.md               # 模块说明文档
│   └── Stas/                       # 统计分析模块
│       ├── visual_report_generator.py  # Markdown报告生成， PNG图表生成
│       ├── statistics_*.py            # 其他统计工具
│       ├── visual_commit_*.py         # 其他统计工具
│       └── README.md                  # 模块说明文档
│
├── 📋 配置文件
│   ├── requirements.txt            # Python依赖包列表
│
└── 📤 输出示例 (自动生成)
    └── {输入目录}_Output/
        ├── Rescaled/               # 🔄 统一放缩后的图像
        ├── Aligned/                # 🎯 SIFT对齐后的图像
        ├── Timelapse/              # 🎬 延时摄影视频
        │   ├── timelapse_preview.mp4   (2048×1536 (50% 原分辨率) + CRF 28 → 30帧 0.2MB)
        │   ├── timelapse_standard.mp4  (3072×2304 (75% 原分辨率) + CRF 23 → 30帧 0.6MB)
        │   └── timelapse_hq.mp4        (4096×3072 (100% 原分辨率) + CRF 18 → 30帧 1.7MB)
        ├── Mosaic/                 # 🧩 马赛克拼图
        │   ├── mosaic_grid.jpg         # 网格布局
        │   ├── mosaic_timeline_*.jpg   # 时间线布局
        │   └── mosaic_info.md          # 拼图报告
        ├── Statistics/             # 📊 统计分析
        │   ├── NPU_Photo_Statistics_Report.md
        │   └── NPU_Photo_Commit_Chart.png
        └── processing_report.md    # 📝 完整处理报告
```

---

## 📱 设备支持

NPU-Everyday的图片使用了两个不同的手机拍摄：
- **HUAWEI P30 Pro**: 3648×2736 像素 → 自动放缩到4096×3072
- **vivo X100 Pro**: 4096×3072 像素 → 保持原尺寸

**技术规格**:
- **统一尺寸**: 4096×3072 像素
- **放缩方法**: 高质量LANCZOS重采样
- **输出质量**: 95% JPEG质量

---

## ⚡ 性能指标

### 处理速度参考 (基于NPU-Everyday-Sample)
| 步骤 | 图像数量 | 耗时 | 主要操作 |
|------|---------|------|----------|
| **图像放缩** | 30张 | ~13秒 | LANCZOS重采样 |
| **图像对齐** | 30张 | ~3分钟 | SIFT特征匹配 |
| **延时摄影** | 30张 | ~6秒 | FFmpeg H.264编码 |
| **马赛克拼图** | 30张 | ~18秒 | 多布局生成 |
| **统计分析** | 30张 | ~1秒 | 图表生成 |
| **总计** | 30张 | **~4分钟** | 完整流水线 |

### 输出文件大小参考
| 输出类型 | 文件大小 | 说明 |
|----------|----------|------|
| 延时摄影视频 | 3.8-6.5MB | 3个不同质量版本 |
| 马赛克拼图 | 各种尺寸 | 从32×32到682×682像素 |
| 统计图表 | <1MB | PNG格式GitHub风格图表 |

---

## 🛠️ 系统要求


### 测试平台
- ✅ **Linux (Ubuntu 20.04.6 LTS x86_64 )**
- ✅ **Windows 11**

---

## 📖 详细文档

- 🔧 [环境配置说明 (requirements.txt)](requirements.txt) - 依赖包安装说明
- 🧪 [环境测试工具 (test_environment.py)](test_environment.py) - 环境和功能测试

### 模块详细文档
- [🔄 图像放缩模块 (Resize/README.md)](Resize/README.md)
- [🎯 图像对齐模块 (Align/README.md)](Align/README.md)
- [🎬 延时摄影模块 (Timelapse/README.md)](Timelapse/README.md)
- [🧩 马赛克拼图模块 (Mosaic/README.md)](Mosaic/README.md)
- [📊 统计分析模块 (Stas/README.md)](Stas/README.md)

---

## 🎯 适用场景

- 🏗️ **建筑物延时摄影** - 建筑施工过程记录
- 🌅 **城市景观变化** - 城市发展变迁记录  
- 🔬 **科研观测** - 长期观测数据可视化
- 🎨 **艺术创作** - 创意延时摄影项目
- 📊 **数据可视化** - 时间序列数据展示
- 🖼️ **图像艺术** - 马赛克拼图艺术创作

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/murphyhoucn/TickTock-NPUEveryday.git
cd TickTock-NPUEveryday

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python test_environment.py
```

---

## 🏗️ 技术架构总结

### 🚀 核心技术栈
- **深度学习框架**: PyTorch + Kornia + LoFTR Transformer
- **计算机视觉**: OpenCV + PIL + SIFT/SuperPoint特征检测
- **视频处理**: FFmpeg H.264编码，CRF质量控制
- **GPU加速**: CUDA支持，RTX 3080优化
- **图像处理**: LANCZOS高质量重采样算法

### 🎯 性能优势
- **对齐成功率**: 从24.1% → **100%** (SuperPoint方法)
- **处理速度**: GPU加速提升 **10倍** (1.3秒/对 vs 19秒/对)
- **质量控制**: 三档质量设置，动态分辨率适配
- **内存优化**: 支持大批量图像序列处理
- **错误恢复**: 智能回退和异常处理机制

### 🔧 创新特性
- **三种对齐算法**: SuperPoint(深度学习) / Enhanced(增强传统) / Auto(智能选择)
- **动态分辨率**: 自动检测原图分辨率，生成三档质量视频
- **统一接口**: MainAlign统一管理，简化使用流程
- **目录结构保持**: 完整保持原有文件组织结构
- **详细报告**: Markdown格式的完整处理报告

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📞 技术支持

如遇到问题，请：
1. 查看 `pipeline.log` 日志文件
2. 检查 `processing_report.md` 处理报告
3. 在GitHub提交Issue，包含错误信息和环境详情

---

**🎉 TickTock-NPUEveryday v2.0.0**  
*最后更新: 2025-09-30*  