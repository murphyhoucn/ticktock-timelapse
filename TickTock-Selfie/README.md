# TickTock-Align-Face
TickTock Pic Align@Human Face

每天一张自拍照，时间长了就能拼成一个延时视频，但难的地方在于怎么把每天的人脸照片对齐。
输入Everyday文件夹，读取下面的所有照片，输出Everyday_align

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/murphyhoucn/TickTock-Align-Face.git
cd TickTock-Align-Face

# 2. 安装依赖
pip install -r requirements.txt

# 3. 放入照片到 Everyday 文件夹

# 4. 运行对齐（推荐智能版本）
python face_align_smart.py --keep-original-size

# 5. 生成延时视频
python create_video.py
```

## 功能特性

- 🎯 **精确人脸对齐**: 使用dlib的68点人脸关键点检测，实现高精度人脸对齐
- 📁 **批量处理**: 自动处理整个文件夹中的所有照片
- 🎬 **延时视频制作**: 一键将对齐后的照片制作成延时视频
- 📏 **自定义输出尺寸**: 支持自定义输出图片尺寸
- 🔍 **智能人脸检测**: 自动选择最大的人脸进行对齐
- 📊 **详细日志**: 实时显示处理进度和结果

## 安装

### 环境要求
- Python 3.8+
- Windows/Linux/Mac

``` bash
opencv-contrib-python                     4.11.0.86
opencv-python                             4.11.0.86
dlib                                      19.24.0  # ⚠️ 必须从conda-forge安装
imutils                                   0.5.4
numpy                                     1.26.4
pathlib                                   1.0.1
pathlib2                                  2.3.7.post1
```

### ⚠️ 重要：dlib安装说明

**Windows用户必看**：pip安装的dlib有BUG，必须使用conda：

```bash
# 正确的安装方式（推荐）
conda install -c conda-forge dlib -y

# ❌ 错误方式（会安装损坏的19.22.99版本）
# pip install dlib
```

详见：[TROUBLESHOOTING.md](TROUBLESHOOTING.md) 查看完整的问题排查指南


### 方法一：智能安装（推荐）

```bash
# 运行智能安装脚本，自动检测环境并安装合适的依赖
python install_dependencies.py
```

### 方法二：手动安装

根据需求选择合适的依赖包：

**基础版本（仅OpenCV，快速安装）**：
```bash
pip install -r requirements-minimal.txt
```

**完整版本（包含dlib，最高精度）**：
```bash
# ⚠️ Windows用户必须先用conda安装dlib
conda install -c conda-forge dlib -y

# 然后安装其他依赖
pip install opencv-python imutils
```

**Linux/Mac用户**：
```bash
pip install -r requirements.txt
```

**开发版本（包含测试工具）**：
```bash
pip install -r requirements-dev.txt
```

### 方法三：Windows用户专用（推荐）

```bash
# 第一步：安装dlib（必须！）
conda install -c conda-forge dlib -y

# 第二步：安装其他依赖
pip install opencv-python imutils

# 第三步：验证安装
python -c "import dlib; print('dlib版本:', dlib.__version__)"
```

### 验证安装

```bash
# 测试OpenCV版本（基础功能）
python face_align_opencv.py --help

# 测试智能版本（推荐）
python face_align_smart.py --help

# 测试dlib版本（最高精度）
python face_align_dlib.py --help
```

### 依赖说明

项目包含三个版本，依赖不同：
- **OpenCV版本**: 仅需要 `opencv-python`
- **dlib版本**: 需要 `dlib` + `shape_predictor_68_face_landmarks.dat`
- **智能版本**: 两者都需要，但可以自适应降级

## 使用方法

### 基本使用

1. 将每日自拍照片放入 `Everyday` 文件夹
2. 选择合适的人脸对齐程序：

#### 三种对齐方案

**方案一：纯dlib版本（最高精度）**：
```bash
# 使用dlib的68点关键点，保持原始尺寸1920x1080
python face_align_dlib.py --input Everyday --output Everyday_align --keep-original-size

# 缩放到指定尺寸
python face_align_dlib.py --input Everyday --output Everyday_align --size 512 512
```

**方案二：纯OpenCV版本（兼容性最好）**：
```bash
# 使用OpenCV人脸检测，保持原始尺寸
python face_align_opencv.py --input Everyday --output Everyday_align --keep-original-size

# 缩放到指定尺寸
python face_align_opencv.py --input Everyday --output Everyday_align --size 256 256
```

**方案三：智能切换版本（推荐）**：
```bash
# 自动选择最佳方法，优先dlib，失败时切换OpenCV
python face_align_smart.py --input Everyday --output Everyday_align --keep-original-size
```

3. 对齐后的照片将保存在指定的输出文件夹

### 高级用法

```bash
# 自定义输入输出文件夹
python face_align_dlib.py --input photos --output aligned_photos
python face_align_opencv.py --input photos --output aligned_photos
python face_align_smart.py --input photos --output aligned_photos

# 自定义关键点模型路径（仅dlib版本）
python face_align_dlib.py --predictor custom_model.dat --input Everyday --output Everyday_align

# 创建延时视频
python create_video.py

# 自定义视频参数
python create_video.py --input Everyday_align --output my_timelapse.mp4 --fps 15 --duration 0.2
```

### 快速测试

```bash
# 获取测试图片
python get_test_pic.py

# 测试dlib对齐效果
python test_dlib_alignment.py

# 运行综合测试
python test.py
```

## 项目结构

```
TickTock-Align-Face/
├── face_align_dlib.py         # 纯dlib版本（最高精度）
├── face_align_opencv.py       # 纯OpenCV版本（最佳兼容性）
├── face_align_smart.py        # 智能切换版本（推荐）
├── create_video.py           # 延时视频制作工具
├── get_test_pic.py          # 测试图片获取工具
├── test.py                  # 综合测试程序
├── test_dlib_alignment.py   # dlib对齐效果测试
├── requirements.txt         # 完整依赖（包含dlib）
├── requirements-minimal.txt # 最小依赖（仅OpenCV）
├── requirements-full.txt    # 完整依赖（同requirements.txt）
├── requirements-dev.txt     # 开发依赖（包含测试工具）
├── install_dependencies.py  # 智能安装脚本
├── shape_predictor_68_face_landmarks.dat  # dlib关键点模型
├── dlib-19.22.99-cp310-cp310-win_amd64.whl  # dlib预编译包
├── Everyday/               # 输入照片文件夹
├── Everyday_align_opencv/  # OpenCV版本输出文件夹
├── Everyday_align_smart/   # 智能版本输出文件夹
├── timelapse_HD.mp4       # 高清延时视频
├── timelapse_preview.mp4  # 预览延时视频
├── README.md             # 主要说明文档  
├── README_dlib.md        # dlib版本详细说明
└── LICENSE              # 许可证
```

## 技术原理

1. **人脸检测**: 使用dlib的HOG+SVM人脸检测器
2. **关键点定位**: 使用dlib的68点人脸关键点检测器
3. **人脸对齐**: 基于眼睛、鼻尖、嘴角等关键点进行仿射变换
4. **标准化输出**: 将所有人脸对齐到相同的标准位置和尺寸

## 参数说明

### 人脸对齐程序参数

**所有版本通用参数**：
- `--input`, `-i`: 输入文件夹路径（默认: Everyday）
- `--output`, `-o`: 输出文件夹路径（默认: Everyday_align）
- `--size`, `-s`: 输出图像尺寸 [宽度 高度]（如: --size 512 512）
- `--keep-original-size`: 保持原始图像尺寸（忽略--size参数）

**face_align_dlib.py 特有参数**：
- `--predictor`, `-p`: dlib关键点预测器模型路径（默认: shape_predictor_68_face_landmarks.dat）

### create_video.py 参数

- `--input`, `-i`: 输入文件夹路径（默认: Everyday_align）
- `--output`, `-o`: 输出视频文件名（默认: timelapse.mp4）
- `--fps`: 视频帧率（默认: 10）
- `--duration`: 每张图片显示时长/秒（默认: 0.1）

### 测试程序参数

- `get_test_pic.py`: 无参数，自动获取测试图片
- `test_dlib_alignment.py`: 无参数，测试dlib对齐效果
- `test.py`: 综合测试，无需参数

## 注意事项

1. 确保照片中有清晰可见的人脸
2. 建议使用相同的拍摄角度和距离
3. 光线条件尽量保持一致
4. 支持的图片格式：JPG、PNG、BMP、TIFF
5. 第一次运行需要下载约100MB的人脸检测模型

## 三种方案对比

| 特性 | dlib版本 | OpenCV版本 | 智能版本 |
|------|----------|------------|----------|
| **精度** | ⭐⭐⭐⭐⭐ 最高 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 高 |
| **兼容性** | ⭐⭐ 需要模型 | ⭐⭐⭐⭐⭐ 最好 | ⭐⭐⭐⭐ 好 |
| **速度** | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 快 | ⭐⭐⭐ 中等 |
| **依赖** | dlib + OpenCV | 仅OpenCV | dlib + OpenCV |
| **关键点** | 68点精确定位 | 眼部检测 | 自适应选择 |
| **适用场景** | 专业级对齐 | 快速处理 | 通用推荐 |

### 选择建议

- 🎯 **追求最高精度**: 使用 `face_align_dlib.py`
- 🚀 **快速处理/兼容性**: 使用 `face_align_opencv.py`  
- 🎭 **平衡性能和精度**: 使用 `face_align_smart.py`（推荐）

## 常见问题

**Q: 提示找不到dlib关键点模型文件？**
A: 确保 `shape_predictor_68_face_landmarks.dat` 文件在项目根目录，或使用OpenCV版本

**Q: dlib出现兼容性错误？**
A: 推荐使用智能版本 `face_align_smart.py`，它会自动处理dlib兼容性问题

**Q: 某些照片对齐失败？**
A: 检查照片中是否有清晰的正面人脸，侧脸或模糊的照片可能对齐失败

**Q: 如何提高对齐质量？**
- 保持拍摄角度一致，确保人脸在画面中央
- 光线充足，避免过度曝光或欠曝
- 使用dlib版本获得最高精度

**Q: 可以处理多人照片吗？**
A: 程序会自动选择最大的人脸进行对齐，建议使用单人自拍照

**Q: 如何选择输出尺寸？**
- 保持原始尺寸：`--keep-original-size`（推荐用于最终作品）
- 指定尺寸：`--size 512 512`（适合快速预览）

## 示例效果

### 对齐前后对比
- 对齐前：人脸位置、大小、角度不统一
- 对齐后：所有人脸都对齐到标准位置，制作延时视频更流畅

### 延时视频效果
将连续多天的自拍照对齐后制作成延时视频，可以清晰看到：
- 发型变化
- 面部表情变化  
- 季节变化（服装、背景等）
- 时间流逝的痕迹

## 📊 实际测试结果

### 处理统计
- ✅ **成功对齐**: 62/62 张图片 (100%)
- 🎬 **视频生成**: 
  - `timelapse_simple.mp4` (256x256，12.4秒，186KB)
  - `timelapse_1920x1080_fixed.mp4` (1920x1080，5.2秒，1.7MB)
- 📁 **输出文件夹**: 
  - `Everyday_align_simple` (256x256缩放版本)
  - `Everyday_align_original` (保持原始1920x1080尺寸)

### 🎯 输出尺寸选择建议

#### 1. **保持原始尺寸（1920x1080）**- 推荐用于最终作品
- ✅ 优点：画质最佳，细节丰富
- ❌ 缺点：文件较大，处理时间长
- 🎯 适合：最终延时视频制作
- 💡 使用：`python face_align_smart.py --keep-original-size`

#### 2. **缩放到小尺寸（256x256）**- 推荐用于快速预览
- ✅ 优点：处理速度快，文件小
- ❌ 缺点：画质较低
- 🎯 适合：测试效果，快速预览
- 💡 使用：`python face_align_opencv.py --size 256 256`

#### 3. **中等尺寸（512x512）**- 平衡选择
- ✅ 优点：画质和文件大小平衡
- 🎯 适合：日常处理和分享
- 💡 使用：`python face_align_dlib.py --size 512 512`

## 更新日志

### v2.0 (当前版本)
- ✅ 重构为三种方案：纯dlib、纯OpenCV、智能切换
- ✅ 完善的测试工具和对比功能
- ✅ 优化原始尺寸保持功能
- ✅ 提供预编译dlib支持
- ✅ 详细的使用文档和方案对比

### v1.0 (历史版本)
- ✅ 基础人脸对齐功能
- ✅ 延时视频制作
- ✅ 批量处理支持

## 开发计划

- [ ] 添加更多人脸检测模型支持
- [ ] 支持视频输入直接处理
- [ ] 添加人脸美化和滤镜功能
- [ ] 支持批量调整亮度/对比度
- [ ] 添加GUI界面
- [ ] 支持更多输出视频格式和编码器
- [ ] 添加人脸表情变化检测
- [ ] 支持多人脸场景的高级处理

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

