#!/bin/bash

echo "====================================="
echo " 多智能体数据查询系统 - Web界面启动"
echo "====================================="
echo

# 检查环境变量
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "[错误] 未设置 DASHSCOPE_API_KEY 环境变量"
    echo
    echo "请先设置环境变量："
    echo "export DASHSCOPE_API_KEY=your_api_key"
    echo
    exit 1
fi

echo "环境变量已设置"
echo

# 检查数据库是否存在
if [ ! -f "data/company.db" ]; then
    echo "[警告] 业务数据库不存在，正在初始化..."
    cd data
    python init_db.py
    cd ..
    echo "业务数据库初始化完成"
    echo
fi

if [ ! -f "data/long_term_memory.db" ]; then
    echo "[警告] 记忆数据库不存在，正在初始化..."
    cd data
    python init_memory_db.py
    cd ..
    echo "记忆数据库初始化完成"
    echo
fi

echo "数据库检查完成"
echo

echo "正在启动Web服务器..."
echo
echo "访问地址: http://localhost:5000"
echo
echo "按 Ctrl+C 停止服务器"
echo "====================================="
echo

python app.py

