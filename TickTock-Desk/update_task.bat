@echo off
REM 一键更新计划任务：双击后 UAC 弹窗点"是"即可。
REM 把 \Murphy\TimeLapse解锁自动拍照 的操作切换为 pythonw 直连（消除黑框）。
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0update_task.ps1\"'"
