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
# 解析命令行参数
NO_DESC=false
while getopts "n" opt; do
    case $opt in
        n)
            NO_DESC=true
            ;;
        \?)
            echo "Usage: $0 [-n]"
            echo "  -n  Skip description input (commit with subject only)"
            exit 1
            ;;
    esac
done
echo "Running git status..."
git status

echo "Running git add..."
git add .

# 检查是否有更改需要提交
if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    echo "Running git commit..."
    
    # 构建 commit message
    SUBJECT="[Auto] $git_user@$server_name | $short_time"
    
    if [ "$NO_DESC" = true ]; then
        # -n 模式：直接使用subject，不询问description
        echo "Committing with subject only (-n mode)..."
        git commit -m "$SUBJECT"
    else
        # 交互模式：询问是否添加 description
        echo "Enter description (press Enter to skip):"
        read -r DESCRIPTION
        
        if [ -z "$DESCRIPTION" ]; then
            # 用户直接回车，只有subject
            echo "Committing with subject only..."
            git commit -m "$SUBJECT"
        else
            # 用户输入了 description，使用多行commit message
            echo "Committing with description..."
            git commit -m "$SUBJECT" -m "$DESCRIPTION"
        fi
    fi

    echo "Running git push..."
    git push
fi