@echo off
chcp 65001 >nul
title TimeLapse@Desk - 每日拍照

REM 显示窗口信息
echo 解锁时间: %date% %time%
echo 正在自动执行拍照程序...

echo ======================================
echo    TimeLapse@Desk 每日拍照程序
echo ======================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python
    pause
    exit /b 1
)

REM 激活conda的dev环境
echo 正在激活conda环境...
call conda activate dev
if %errorlevel% neq 0 (
    echo 错误：无法激活conda环境 'dev'
    echo 请确保已安装conda并创建了dev环境
    pause
    exit /b 1
)

@REM REM 检查依赖包
@REM pip show opencv-python >nul 2>&1
@REM if %errorlevel% neq 0 (
@REM     echo 正在安装依赖包...
@REM     pip install -r requirements.txt
@REM     if %errorlevel% neq 0 (
@REM         echo 错误：安装依赖包失败
@REM         pause
@REM         exit /b 1
@REM     )
@REM )

REM 自动运行拍照对齐程序
echo 正在启动自动拍照对齐程序...
python timelapse_demo.py

REM 程序执行完毕
echo.
echo 程序执行完毕！