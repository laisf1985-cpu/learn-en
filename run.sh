#!/bin/bash

# 英语背单词挑战 - 启动脚本

echo "📚 英语背单词挑战 - 启动中..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 启动应用
echo "🚀 启动应用..."
python app.py
