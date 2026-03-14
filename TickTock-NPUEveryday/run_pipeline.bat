@echo off
chcp 65001 >nul
echo.
echo ████████╗██╗ ██████╗██╗  ██╗████████╗ ██████╗  ██████╗██╗  ██╗
echo ╚══██╔══╝██║██╔════╝██║ ██╔╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝
echo    ██║   ██║██║     █████╔╝    ██║   ██║   ██║██║     █████╔╝ 
echo    ██║   ██║██║     ██╔═██╗    ██║   ██║   ██║██║     ██╔═██╗ 
echo    ██║   ██║╚██████╗██║  ██╗   ██║   ╚██████╔╝╚██████╗██║  ██╗
echo    ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝
echo.
echo TickTock-NPU Everyday Library 一键启动脚本
echo NPU建筑物图像处理 - 完整工作流程
echo ============================================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境，请先安装Python 3.6+
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 检查依赖包
echo 📦 检查依赖包...
pip show opencv-python >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未找到OpenCV，正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo ✅ 依赖包检查通过
)

echo.
echo "请选择处理模式:"
echo "1. 快速测试 (NPU-Everyday-Sample) - 快速测试"
echo "2. 完整处理 (NPU-Everyday)"
echo "3. 仅图像放缩"
echo "4. 仅图像对齐" 
echo "5. 仅延时摄影"
echo "6. 仅马赛克拼接"
echo "7. 仅统计分析"
echo "8. 自定义步骤"
echo "0. 退出"
echo.

set /p choice="请输入选择 (0-8): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :quick_test
if "%choice%"=="2" goto :full_process
if "%choice%"=="3" goto :resize_only
if "%choice%"=="4" goto :align_only
if "%choice%"=="5" goto :timelapse_only
if "%choice%"=="6" goto :mosaic_only
if "%choice%"=="7" goto :stats_only
if "%choice%"=="8" goto :custom
goto :invalid

:quick_test
echo.
echo 🚀 开始快速测试处理...
echo 输入: NPU-Everyday-Sample
echo 输出: NPU-Everyday-Sample_Output
echo.
python pipeline.py NPU-Everyday-Sample
goto :success

:full_process
echo.
echo 🚀 开始完整处理...
echo 输入: NPU-Everyday
echo 输出: NPU-Everyday_Output
echo.
python pipeline.py NPU-Everyday
goto :success

:resize_only
echo.
echo 🔄 仅执行图像放缩...
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
python pipeline.py %input_dir% --resize-only
goto :success

:align_only
echo.
echo 📐 仅执行图像对齐...
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
python pipeline.py %input_dir% --align-only
goto :success

:timelapse_only
echo.
echo 🎬 仅执行延时摄影...
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
python pipeline.py %input_dir% --timelapse-only
goto :success

:mosaic_only
echo.
echo 🧩 仅执行马赛克拼接...
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
python pipeline.py %input_dir% --mosaic-only
goto :success

:stats_only
echo.
echo 📊 仅执行统计分析...
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
python pipeline.py %input_dir% --stats-only
goto :success

:custom
echo.
echo 🔧 自定义步骤组合
echo 可选步骤: resize, align, timelapse, mosaic, stats
set /p input_dir="请输入目录名 (默认: NPU-Everyday-Sample): "
if "%input_dir%"=="" set input_dir=NPU-Everyday-Sample
set /p steps="请输入步骤 (用空格分隔): "
python pipeline.py %input_dir% --steps %steps%
goto :success

:invalid
echo ❌ 无效选择，请重新运行脚本
pause
exit /b 1

:success
echo.
echo ✅ 处理完成！
echo 📁 输出文件夹: %input_dir%_Output
echo 📝 处理报告: %input_dir%_Output\processing_report.md
echo.
echo 按任意键查看输出文件夹...
pause >nul
explorer %input_dir%_Output
goto :end

:end
echo.
echo "感谢使用 TickTock-NPU Everyday Library！"
pause