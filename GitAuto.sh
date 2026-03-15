#!/bin/bash

# 获取主机名作为设备名
server_name=$(hostname)

# 调整时间格式为: YYYY-MM-DD HH:MM (例如 2026-03-14 23:09)
short_time=$(date "+%Y-%m-%d %H:%M")

echo "Running git status..."
git status

echo "Running git add..."
git add .

if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    echo "Running git commit..."
    # 优雅拼接: [Auto] 设备名 @ 时间
    git commit -m "[Auto] $server_name @ $short_time"

    echo "Running git push..."
    git push
fi