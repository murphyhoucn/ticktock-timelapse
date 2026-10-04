@echo off
chcp 65001 >nul
cd /d %~dp0
title TimeLapse@Desk - 手动拍照

echo === TimeLapse@Desk 手动拍照（调试用） ===
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到 Python，请先安装或激活 conda 环境
    pause
    exit /b 1
)

REM 激活 conda dev 环境
call conda activate dev
if %errorlevel% neq 0 (
    echo 错误：无法激活 conda 环境 'dev'
    pause
    exit /b 1
)

REM 手动运行不受每日次数限制时加 --force；这里默认遵守计数
python capture_once.py --verbose

echo.
echo 执行完毕，退出码 %errorlevel%
pause
