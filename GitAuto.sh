#!/bin/bash

# 获取主机名作为设备名
server_name=$(hostname)

# 获取 Git 用户名，如果没有配置则默认显示 UnknownUser
git_user=$(git config --global --get user.name)
if [ -z "$git_user" ]; then
    git_user="UnknownUser"
fi

# 调整时间格式为: YYYY-MM-DD HH:MM
short_time=$(date "+%Y-%m-%d %H:%M")

echo "Running git status..."
git status

echo "Running git add..."
git add .

# 检查是否有更改需要提交
if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    echo "Running git commit..."
    # 优雅融合：[Auto] 用户名 on 设备名 @ 时间
    git commit -m "[Auto] $git_user on $server_name @ $short_time"

    echo "Running git push..."
    git push
fi