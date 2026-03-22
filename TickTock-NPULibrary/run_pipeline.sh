#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

echo
echo "████████╗██╗ ██████╗██╗  ██╗████████╗ ██████╗  ██████╗██╗  ██╗"
echo "╚══██╔══╝██║██╔════╝██║ ██╔╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝"
echo "   ██║   ██║██║     █████╔╝    ██║   ██║   ██║██║     █████╔╝ "
echo "   ██║   ██║██║     ██╔═██╗    ██║   ██║   ██║██║     ██╔═██╗ "
echo "   ██║   ██║╚██████╗██║  ██╗   ██║   ╚██████╔╝╚██████╗██║  ██╗"
echo "   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝"
echo
echo "TickTock-NPU Everyday Library 一键启动脚本"
echo "NPU建筑物图像处理 - 完整工作流程"
echo "============================================================"
echo

# 检查Python环境
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python环境，请先安装Python 3.6+"
    read -p "按任意键退出..."
    exit 1
fi

# 优先使用python3，如果没有则使用python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Python环境检查通过"
echo

# 检查依赖包
echo "📦 检查依赖包..."
if ! $PYTHON_CMD -c "import cv2" &> /dev/null; then
    echo "⚠️ 未找到OpenCV，正在安装依赖包..."
    pip3 install -r requirements.txt || pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖包安装失败，请手动运行: pip install -r requirements.txt"
        read -p "按任意键退出..."
        exit 1
    fi
else
    echo "✅ 依赖包检查通过"
fi

echo
echo "请选择处理模式:"
echo "1. ⭐ 快速测试 (NPU-Everyday-Sample) - 快速测试"
echo "2. ⭐ 完整处理 (NPU-Everyday)"
echo "3. 仅图像放缩"
echo "4. 仅图像对齐"
echo "5. 仅延时摄影"
echo "6. 仅马赛克拼接"
echo "7. 仅统计分析"
echo "8. 自定义步骤"
echo "0. 退出"
echo

read -p "请输入选择 (0-8): " choice

case $choice in
    0)
        echo
        echo "感谢使用 TickTock-NPU Everyday Library！"
        exit 0
        ;;
    1)
        echo
        echo "🚀 开始快速测试处理..."
        echo "输入: NPU-Everyday-Sample"
        echo "输出: NPU-Everyday-Sample_Output"
        echo
        $PYTHON_CMD pipeline.py NPU-Everyday-Sample
        input_dir="NPU-Everyday-Sample"
        ;;
    2)
        echo
        echo "🚀 开始完整处理..."
        echo "输入: NPU-Everyday"
        echo "输出: NPU-Everyday_Output"
        echo
        $PYTHON_CMD pipeline.py NPU-Everyday
        input_dir="NPU-Everyday"
        ;;
    3)
        echo
        echo "🔄 仅执行图像放缩..."
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        $PYTHON_CMD pipeline.py "$input_dir" --resize-only
        ;;
    4)
        echo
        echo "📐 仅执行图像对齐..."
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        $PYTHON_CMD pipeline.py "$input_dir" --align-only
        ;;
    5)
        echo
        echo "🎬 仅执行延时摄影..."
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        $PYTHON_CMD pipeline.py "$input_dir" --timelapse-only
        ;;
    6)
        echo
        echo "🧩 仅执行马赛克拼接..."
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        $PYTHON_CMD pipeline.py "$input_dir" --mosaic-only
        ;;
    7)
        echo
        echo "📊 仅执行统计分析..."
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        $PYTHON_CMD pipeline.py "$input_dir" --stats-only
        ;;
    8)
        echo
        echo "🔧 自定义步骤组合"
        echo "可选步骤: resize, align, timelapse, mosaic, stats"
        read -p "请输入目录名 (默认: NPU-Everyday-Sample): " input_dir
        if [ -z "$input_dir" ]; then
            input_dir="NPU-Everyday-Sample"
        fi
        read -p "请输入步骤 (用空格分隔): " steps
        $PYTHON_CMD pipeline.py "$input_dir" --steps $steps
        ;;
    *)
        echo "❌ 无效选择，请重新运行脚本"
        read -p "按任意键退出..."
        exit 1
        ;;
esac

echo
echo "✅ 处理完成！"
echo "📁 输出文件夹: ${input_dir}_Output"
echo "📝 处理报告: ${input_dir}_Output/processing_report.md"
echo

# 检查是否为桌面环境，如果是则打开文件管理器
if [ -n "$DISPLAY" ]; then
    echo "按任意键查看输出文件夹..."
    read -n 1
    if command -v xdg-open &> /dev/null; then
        xdg-open "${input_dir}_Output" 2>/dev/null
    elif command -v nautilus &> /dev/null; then
        nautilus "${input_dir}_Output" 2>/dev/null
    elif command -v dolphin &> /dev/null; then
        dolphin "${input_dir}_Output" 2>/dev/null
    else
        echo "无法自动打开文件管理器，请手动查看: ${input_dir}_Output"
    fi
else
    echo "输出目录: $(pwd)/${input_dir}_Output"
fi

echo
echo "感谢使用 TickTock-NPU Everyday Library！"