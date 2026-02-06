"""启动后端服务"""
import subprocess
import os

# 切换到backend目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("backend")

# 使用 uv run 启动 uvicorn（自动使用虚拟环境）
subprocess.run([
    "uv", "run", "uvicorn",
    "app.main:app",
    "--reload",
    "--host", "0.0.0.0",
    "--port", "8000"
])
