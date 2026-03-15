@echo off
setlocal

:: 获取当前系统时间并调整格式 (YYYY-MM-DD HH:MM)
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set dt=%%a
set SHORT_TIME=%dt:~0,4%-%dt:~4,2%-%dt:~6,2% %dt:~8,2%:%dt:~10,2%

:: 执行 Git 命令
echo Running git status...
git status
echo Running git add...
git add .

:: 检查是否有需要提交的更改
git diff-index --quiet HEAD --
if %errorlevel% equ 0 (
    echo No changes to commit.
) else (
    echo Running git commit...
    :: 使用自带的 %COMPUTERNAME% 作为设备名
    git commit -m "[Auto] %COMPUTERNAME% @ %SHORT_TIME%"
    echo Running git push...
    git push
)

endlocal
pause