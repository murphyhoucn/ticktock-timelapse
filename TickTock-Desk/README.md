# TimeLapse@Desk（工位时光流逝）

每天解锁电脑时自动用摄像头拍一张照片，MediaPipe 做人脸对齐，日积月累后合成一段延时视频——记录你在工位上的一年。

## 工作原理

```
Windows 解锁
   │  （任务计划程序触发器：工作站解锁时）
   ▼
pythonw.exe capture_once.py        ← 完全无窗口，无控制台
   │
   ├─ 读取 unlock_count.txt：今天已拍几张？
   │     ├─ 已达 3 张 → 立即退出（<1 秒，不开摄像头）
   │     └─ 未达上限 ↓
   ├─ 打开摄像头，预热 10 帧 + 稳定 1 秒后拍摄
   ├─ 原始照 + 水印 → photos/photo_YYYYMMDD_HHMMSS.jpg
   ├─ MediaPipe 人脸对齐 + 水印 → aligned_photos/aligned_photo_*.jpg
   └─ 计数 +1，写入 unlock_count.txt，退出
```

## 目录结构

```
TickTock-Desk/
├── timelapse/                # 核心包
│   ├── config.py             #   全部可调参数（目录/摄像头/水印/每日上限）
│   ├── counter.py            #   每日解锁计数（unlock_count.txt）
│   ├── camera.py             #   摄像头采集（参数设置/预热/拍摄）
│   ├── alignment.py          #   MediaPipe 人脸检测与对齐
│   ├── watermark.py          #   右下角半透明水印
│   ├── pipeline.py           #   完整流程编排
│   └── logging_setup.py      #   文件日志
├── capture_once.py           # ★ 主入口：任务计划程序调用（pythonw）
├── make_video.py             # FFmpeg 合成延时视频
├── check_camera.py           # 摄像头能力探测 / 画质检查（手动）
├── selftest.py               # 环境自检（手动）
├── run_timelapse.bat         # 手动双击运行（有窗口，调试用）
├── run_timelapse.ps1         # 过渡脚本：任务切换到 pythonw 直连后可删
├── update_task.bat / .ps1    # 一键把计划任务切换为 pythonw 直连（需 UAC 确认）
├── photos/                   # 原始照片（带水印）
├── aligned_photos/           # 对齐照片（带水印，做视频用这批）
├── logs/timelapse.log        # 运行日志（1MB 自动轮转 ×3）
├── unlock_count.txt          # 每日计数状态（格式：YYYY-MM-DD N）
└── NPU-Archive/              # 旧机器上的照片存档（只读，程序不使用）
```

## 环境准备

- Python 3.10（conda 环境 `dev`，已就绪）：`opencv-python`、`mediapipe`、`numpy`
- FFmpeg（仅制作视频需要）：已在 `D:\DevEnv\ffmpeg\bin`

依赖安装（新环境时）：

```bash
pip install -r requirements.txt
```

迁移或换机器后先自检：

```bash
python selftest.py        # 依赖、MediaPipe 模型、摄像头逐项检查
python check_camera.py    # 探测支持的分辨率、拍测试照分析清晰度
```

## 日常使用

### 自动模式（已配置完成）

任务计划程序 `\Murphy\TimeLapse解锁自动拍照`：

| 项 | 值 |
|---|---|
| 触发器 | 工作站解锁时（无需改动） |
| 程序 | `D:\DevEnv\miniconda3\envs\dev\pythonw.exe` |
| 参数 | `"D:\DevProj\TickTock-Timelapse\TickTock-Desk\capture_once.py"` |
| 起始于 | `D:\DevProj\TickTock-Timelapse\TickTock-Desk` |

`update_task.bat` / `update_task.ps1`（一键切换任务操作用）与过渡脚本 `run_timelapse.ps1` 已完成使命，可以直接删除；换电脑重新部署时可从 git 历史找回。

**为什么用 pythonw 而不是 powershell？**
`powershell.exe` 是控制台程序，即使加 `-WindowStyle Hidden`，窗口也是先创建再隐藏——这就是黑框"闪一下"的原因。`pythonw.exe` 属于 GUI 子系统，从进程创建起就没有控制台，配合程序内部的每日计数，整个链路真正零窗口。

火绒等安全软件提示"正在调用摄像头"属于预期行为（摄像头确实在工作），可加入信任列表。

### 手动命令

```bash
conda activate dev

python capture_once.py --verbose    # 拍一次（遵守每日计数，控制台可见过程）
python capture_once.py --force --verbose   # 强制拍，不消耗当日额度
python make_video.py                # 生成延时视频（三档）
run_timelapse.bat                   # 或直接双击
```

## 每日 3 次机制

**为什么在脚本层做，而不是 Windows 层？**
任务计划程序本身没有"解锁计数"能力。理论上可以统计安全日志里的解锁事件（Event ID 4801），但前提是：①组策略开启"审核其他登录/注销事件"（默认关闭）；②读取安全日志需要管理员权限，而本任务以普通用户运行。两层门槛都不可靠，所以选择脚本层计数：任务照常每次解锁触发，程序自己读 `unlock_count.txt` 决定拍还是退——达到上限后整个进程 1 秒内退出，无任何感知。

规则细节：

- 状态文件 `unlock_count.txt` 首行 `YYYY-MM-DD N`，跨天自动清零，文件损坏/删除也视为 0
- **拍摄成功才计数**：摄像头被占用等原因失败时不消耗当日额度
- 修改每日上限：`capture_once.py --limit 5`，或改 `timelapse/config.py` 的 `daily_limit`
- 手动重置：删除 `unlock_count.txt` 即可

## 配置参数（timelapse/config.py）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `daily_limit` | 3 | 每日最多成功拍摄次数 |
| `camera_index` | 0 | 摄像头索引 |
| `frame_width/height` | 1920×1080 | 目标分辨率（实际以摄像头支持为准） |
| `warmup_frames` | 10 | 预热帧数，让自动曝光/对焦收敛 |
| `settle_seconds` | 1.0 | 预热后额外稳定时间 |
| `target_size` / `eye_y_ratio` | 1920×1080 / 0.4 | 对齐画幅与眼睛中心位置 |
| `watermark_*` | Copyright Murphy / Qingdao / 0.7 | 水印文字与透明度 |

## 延时视频

```bash
python make_video.py                                       # 三档全出
python make_video.py --fps 12 --crf 20 --name my.mp4       # 自定义单档
```

- `timelapse_preview.mp4` 30fps 快速预览 / `timelapse_standard.mp4` 15fps 标准 / `timelapse_hq.mp4` 10fps 高质量
- `--fps` 越大播放越快；`--crf` 越小质量越高（0–51）

## 故障排查

| 现象 | 排查 |
|---|---|
| 解锁后没拍照片 | 看 `logs/timelapse.log`——`已达每日上限`属正常；无日志说明任务没触发，查任务计划程序"历史记录" |
| 想看静默运行的报错 | 先手动 `python capture_once.py --verbose` 复现，日志同样写入 `logs/timelapse.log` |
| 照片没对齐（无 aligned_ 文件） | 坐姿偏离摄像头太远/逆光，未检测到人脸；原始照已保存，不算失败 |
| 摄像头打不开 | 是否被会议软件占用；`python check_camera.py` 逐项检查 |
| 换了电脑/路径变了 | 更新任务计划程序里的绝对路径，并跑 `python selftest.py` |
