# TickTock-Desk
TickTock@Desk（工位时光流逝）

我在网上发现了一个很有趣的项目，就是打工人或者是研究生，每天到工位上的时候，自动调用摄像头给自己拍张照片，然后时间久了，就能剪辑成一个视频。

## 🎯 项目特色
- ✅ **完全自动化**：Windows开机自动运行，静默执行无弹窗
- ✅ **高画质拍摄**：1920×1080全高清，充分利用摄像头最大能力  
- ✅ **精准人脸对齐**：使用MediaPipe AI模型，眼睛中心精确对齐
- ✅ **专业水印系统**：版权信息+时间戳+地点，半透明效果
- ✅ **智能图像处理**：不缩放保持画质，智能填充空白区域
- ✅ **任务计划集成**：Windows任务计划程序自动化执行

## 🌟 核心功能
1. **Python实现**：基于OpenCV + MediaPipe的专业图像处理
2. **无感触发**：系统解锁自动触发，完全静默运行
3. **智能命名**：按时间戳自动命名，便于管理和排序  
4. **双重输出**：原始照片 + 人脸对齐照片，满足不同需求
5. **AI人脸检测**：实时检测人脸关键点，精确对齐处理
6. **延时视频就绪**：对齐照片直接可用于制作高质量延时视频

## Demo 快速开始

现在已经有了一个功能完整的demo！

### 🚀 三种运行方式

#### 方式1：完全静默自动运行（推荐）
**使用PowerShell静默脚本**：`run_timelapse.ps1`
- 完全无窗口运行，适合自动化场景
- 系统任务计划程序调用
- 后台静默执行，不影响正常工作

#### 方式2：批处理一键运行  
**双击 `run_timelapse.bat`** - 传统方式
- 自动激活conda环境
- 自动安装依赖包
- 自动拍摄1920×1080高清照片
- 自动进行人脸对齐处理
- 完成后自动退出

#### 方式3：手动运行
```bash
# 激活conda环境
conda activate dev

# 运行程序
python timelapse_demo.py
```

### 📁 核心文件说明

#### 主程序文件
- **`timelapse_demo.py`** - 主程序，实现拍照+人脸对齐+水印系统
- **`camera_test.py`** - 摄像头能力测试，检测最佳参数设置

#### 自动化脚本  
- **`run_timelapse.ps1`** - PowerShell静默执行脚本（推荐）
- **`run_timelapse.bat`** - 传统批处理一键运行脚本

#### 系统集成
- **`test_system.py`** - 系统环境测试，检查摄像头和依赖
- **`requirements.txt`** - Python依赖包列表

#### 文档说明
- **`USAGE.md`** - 详细使用说明
- **`QUICKSTART.md`** - 新手快速开始指南  
- **`TASK_SCHEDULER_SETUP.md`** - Windows任务计划程序配置
- **`CAMERA_OPTIMIZATION.md`** - 摄像头优化说明

### ✨ 核心技术特性

#### 📷 图像采集系统
- ✅ **4K级高清拍照**：1920×1080分辨率，充分利用摄像头最大能力
- ✅ **智能摄像头优化**：自动检测并应用最佳参数设置（对比度、饱和度、锐度）
- ✅ **专业预热机制**：10帧预热+1秒稳定，确保图像质量最优

#### 🤖 AI人脸处理  
- ✅ **MediaPipe人脸检测**：Google AI模型，468个人脸关键点精确定位
- ✅ **精准眼部对齐**：眼睛中心对齐到固定位置，角度自动校正
- ✅ **无损画质处理**：不缩放保持原始分辨率，智能边界填充

#### 🎨 专业水印系统
- ✅ **版权保护水印**：自动添加"Copyright Murphy"版权信息
- ✅ **时间地点标记**：格式化时间戳"YYYY/MM/DD HH:MM Xi'An"  
- ✅ **半透明效果**：可调透明度，Consolas风格字体，无描边设计
- ✅ **智能定位**：右下角适当边距，避免过度遮挡画面内容

#### ⚡ 自动化运行
- ✅ **Windows任务计划集成**：系统解锁自动触发，完全无人值守
- ✅ **PowerShell静默执行**：隐藏窗口运行，不干扰正常工作
- ✅ **双重文件输出**：原始照片 + 对齐照片（均为1920×1080）
- ✅ **智能错误处理**：摄像头异常、人脸检测失败等情况的优雅处理

### 📸 输出效果展示

程序自动创建两个输出目录，所有照片均为1920×1080全高清分辨率：

#### 📁 `photos/` - 原始照片目录
- 🎯 **直接拍摄**：保持摄像头原始视角和构图
- 🏷️ **专业水印**：包含版权信息和时间地点标记  
- 📅 **时间命名**：`photo_20250926_165937.jpg` 格式，便于排序管理
- 💾 **完整保留**：保存所有拍摄细节，作为原始档案

#### 📁 `aligned_photos/` - 对齐照片目录  
- 👁️ **人脸居中**：眼睛中心精确对齐到固定位置
- 🔄 **角度校正**：自动旋转校正头部倾斜，保持水平
- 🖼️ **画面优化**：智能裁切和填充，专为延时视频优化
- 🎬 **延时就绪**：直接可用于制作高质量延时视频

### 🎬 延时视频制作

#### 📦 安装FFmpeg
- https://www.ffmpeg.org/download.html#build-windows

#### 🎥 制作视频的三种方法

**方法1：使用专用脚本（推荐，解决兼容性问题）**
```bash
# 一键制作三种质量的视频
python create_timelapse.py
```
自动生成：
- `timelapse_preview.mp4` - 快速预览版 (30fps)
- `timelapse_standard.mp4` - 标准版 (15fps) 
- `timelapse_hq.mp4` - 高质量版 (10fps)

**方法2：手动FFmpeg命令（适用于支持glob的版本）**
```bash
# 基础延时视频
ffmpeg -framerate 10 -pattern_type glob -i "aligned_photos/*.jpg" -c:v libx264 -pix_fmt yuv420p timelapse.mp4

# 高质量延时视频  
ffmpeg -framerate 15 -pattern_type glob -i "aligned_photos/*.jpg" -c:v libx264 -crf 18 -pix_fmt yuv420p -vf "scale=1920:1080" timelapse_hq.mp4
```

**方法3：文件列表方式（兼容所有FFmpeg版本）**
```bash
# 1. 创建文件列表
ls aligned_photos/*.jpg | sed 's/.*/"file &"/' > filelist.txt

# 2. 使用concat方式
ffmpeg -f concat -safe 0 -i filelist.txt -r 15 -c:v libx264 -crf 18 -pix_fmt yuv420p timelapse.mp4
```

**💡 参数说明**：
- `-r 15`：视频帧率，数值越大播放越快
- `-crf 18`：视频质量，0-51范围，18为高质量
- `-pix_fmt yuv420p`：像素格式，确保播放器兼容性

## 📚 详细文档

- 📖 **[USAGE.md](USAGE.md)** - 完整使用说明和高级配置
- 🚀 **[QUICKSTART.md](QUICKSTART.md)** - 新手5分钟快速开始
- ⏰ **[TASK_SCHEDULER_SETUP.md](TASK_SCHEDULER_SETUP.md)** - Windows任务计划程序配置
- 📷 **[CAMERA_OPTIMIZATION.md](CAMERA_OPTIMIZATION.md)** - 摄像头优化和故障排除
- 🎯 **[ALIGNMENT.md](ALIGNMENT.md)** - 人脸对齐算法详解

---

## 🏆 项目亮点

> **这不仅仅是一个拍照工具，而是一个完整的自动化工位记录解决方案！**

- 🤖 **真正的无人值守**：从系统启动到照片处理，全程自动化
- 🎨 **专业级图像处理**：AI驱动的人脸对齐，媲美商业软件效果  
- 📈 **企业级稳定性**：完善的错误处理，长期稳定运行
- 🔧 **高度可定制**：丰富的配置选项，适应不同使用场景