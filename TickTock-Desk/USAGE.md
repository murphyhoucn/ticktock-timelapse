# TimeLapse@Desk 使用说明

## 功能介绍

这个程序可以帮助你每天自动拍摄工位照片，并进行人脸对齐处理，为制作延时视频做准备。

## 主要功能

1. **自动拍照**：调用摄像头拍摄照片，以时间戳命名
2. **人脸检测**：使用MediaPipe检测人脸关键点
3. **人脸对齐**：根据眼睛位置对齐人脸，确保视频中人脸位置一致
4. **双重保存**：保存原始照片和对齐后的照片

## 快速开始

### 方法一：使用批处理文件（推荐）

1. 双击 `run_timelapse.bat` 文件
2. 选择运行模式：
   - **完整模式**：包含人脸对齐处理（首次运行推荐）
   - **快速模式**：仅拍照，速度快3-5倍
3. 程序会自动：
   - 创建Python虚拟环境
   - 安装必要的依赖包
   - 运行拍照程序

### 方法二：手动运行

1. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行程序：
   ```bash
   python timelapse_demo.py
   ```

## 命令行参数

```bash
python timelapse_demo.py [选项]

选项：
  --camera INDEX    指定摄像头索引（默认：0）
  --output DIR      指定原始照片保存目录（默认：photos）
  --aligned DIR     指定对齐照片保存目录（默认：aligned_photos）
  --fast           快速模式：跳过人脸对齐处理，大幅提升速度

示例：
  python timelapse_demo.py                    # 完整模式
  python timelapse_demo.py --fast             # 快速模式（推荐日常使用）
  python timelapse_demo.py --camera 1 --fast  # 使用第二个摄像头，快速模式
```

## 文件结构

程序运行后会创建以下目录结构：

```
TimeLapse-Desk/
├── photos/              # 原始照片
│   ├── photo_20250926_143022.jpg
│   ├── photo_20250927_143015.jpg
│   └── ...
├── aligned_photos/      # 对齐后的照片
│   ├── aligned_photo_20250926_143022.jpg
│   ├── aligned_photo_20250927_143015.jpg
│   └── ...
└── venv/               # Python虚拟环境
```

## 使用建议

### 🚀 性能优化建议
- 目前感觉运行还是好慢！

### 💡 使用技巧

1. **定时运行**：可以使用Windows任务计划程序定时运行批处理文件
2. **摄像头调试**：如果默认摄像头不工作，尝试使用 `--camera 1` 或其他索引
3. **光线条件**：确保拍照时有足够的光线，以提高人脸检测准确性
4. **位置固定**：尽量保持相同的坐姿和位置，以获得更好的延时效果

### ⚡ 性能对比

- **完整模式**：拍照 + 人脸检测 + 对齐处理（约10-15秒）

## 制作延时视频

收集足够的对齐照片后，可以使用以下工具制作延时视频：

1. **FFmpeg**（推荐）：
   ```bash
   ffmpeg -framerate 10 -pattern_type glob -i "aligned_photos/*.jpg" -c:v libx264 -pix_fmt yuv420p timelapse.mp4
   ```

2. **其他视频编辑软件**：
   - Adobe Premiere Pro
   - DaVinci Resolve
   - OpenShot

## 故障排除

### 常见问题

1. **摄像头无法打开**
   - 检查摄像头是否被其他程序占用
   - 尝试不同的摄像头索引

2. **人脸检测失败**
   - 确保面部清晰可见
   - 检查光线是否充足
   - 避免遮挡面部

3. **依赖包安装失败**
   - 确保网络连接正常
   - 尝试使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### 技术支持

如果遇到问题，请检查：
1. Python版本（建议3.8+）
2. 摄像头驱动是否正常
3. 防火墙/杀毒软件是否阻止程序运行

## 未来功能计划

- [ ] GUI界面
- [ ] 自动视频合成
- [ ] 云端存储支持
- [ ] 多人脸检测
- [ ] 表情分析