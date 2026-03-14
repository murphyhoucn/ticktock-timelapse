# TickTock Face Alignment Tool - 纯dlib版本

## 特点

### ✨ 纯dlib实现
- **高精度检测**: 使用dlib的HOG+SVM人脸检测器
- **68点关键点**: 利用dlib的shape_predictor进行精确的面部关键点定位
- **无OpenCV依赖**: 纯dlib实现，不包含任何OpenCV检测器备选方案

### 🎯 核心功能
- **原始尺寸保持**: 完美支持保持1920x1080原始图像尺寸
- **高精度对齐**: 基于68个面部关键点的精确对齐
- **批量处理**: 支持文件夹批量处理
- **灵活配置**: 支持自定义输出尺寸和关键点模型路径

## 使用方法

### 基本用法
```bash
# 保持原始尺寸对齐
python face_align_dlib.py --input input_folder --output output_folder --keep-original-size

# 指定输出尺寸
python face_align_dlib.py --input input_folder --output output_folder --size 512 512

# 自定义关键点模型路径
python face_align_dlib.py --input input_folder --output output_folder --keep-original-size --predictor my_model.dat
```

### 参数说明
- `--input, -i`: 输入文件夹路径
- `--output, -o`: 输出文件夹路径  
- `--size, -s`: 输出图像尺寸 (宽度 高度)
- `--keep-original-size`: 保持原始图像尺寸（忽略--size参数）
- `--predictor, -p`: dlib 68点关键点预测器模型路径 (默认: shape_predictor_68_face_landmarks.dat)

## 技术实现

### 关键点提取
从dlib的68个关键点中提取5个关键点：
- 左眼中心 (点36-41的平均值)
- 右眼中心 (点42-47的平均值)  
- 鼻尖 (点30)
- 左嘴角 (点48)
- 右嘴角 (点54)

### 对齐算法
1. **保持原始尺寸模式**: 
   - 计算双眼连线角度进行旋转校正
   - 平移调整使眼睛位于理想位置 (水平居中，垂直40%位置)
   - 不进行缩放，完全保持原始图像尺寸

2. **标准缩放模式**:
   - 基于5个关键点计算仿射变换矩阵
   - 将人脸对齐到标准模板位置

## 测试结果

在26张1920x1080图片上的测试结果：
- ✅ **成功率**: 100% (26/26)
- ✅ **尺寸保持**: 完美保持原始尺寸
- ✅ **对齐精度**: 基于68点关键点的高精度对齐
- ✅ **处理速度**: 每张图片约0.15秒

## 依赖要求

```
dlib >= 19.22.0
opencv-python >= 4.5.0
numpy >= 1.21.0
```

## 模型文件

需要下载dlib的68点关键点预测器模型：
- 文件名: `shape_predictor_68_face_landmarks.dat`
- 下载地址: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

## 示例输出

```
2025-09-26 23:43:52,390 - INFO - ✅ dlib人脸检测器初始化成功
2025-09-26 23:43:53,116 - INFO - ✅ dlib关键点预测器加载成功
2025-09-26 23:43:53,120 - INFO - 找到 26 张图片，开始处理...
...
2025-09-26 23:43:57,231 - INFO - 处理完成！成功对齐 26/26 张图片
```

这个纯dlib版本专为需要最高精度人脸对齐的场景设计，完全依赖dlib的先进算法，提供最佳的对齐质量。