#!/bin/bash

echo "正在启动个人学习管理系统..."

# 启动后端（后台运行）
echo "启动后端服务..."
python start_backend.py &

# 启动前端（后台运行）
echo "启动前端服务..."
python start_frontend.py &

# 等待所有后台进程
wait