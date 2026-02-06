"""启动前端开发服务"""
import subprocess
import os

# 切换到frontend目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("frontend")

# 使用 bunx 启动 vite 开发服务器
subprocess.run(["bunx", "--bun", "vite", "--host"])
