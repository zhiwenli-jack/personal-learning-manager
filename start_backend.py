"""启动后端服务"""
import subprocess
import os
import signal
import sys

# 切换到backend目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("backend")

# 使用 Popen 启动 uvicorn（可控制子进程）
process = subprocess.Popen([
    "uv", "run", "uvicorn",
    "app.main:app",
    "--reload",
    "--host", "0.0.0.0",
    "--port", "8000"
])

def cleanup(signum, frame):
    """收到终止信号时同步关闭子进程"""
    print("\n正在关闭后端服务...")
    process.terminate()
    process.wait()
    sys.exit(0)

# 注册信号处理 - 监听终端关闭信号
signal.signal(signal.SIGTERM, cleanup)  # 终止信号
signal.signal(signal.SIGINT, cleanup)   # Ctrl+C 中断信号

# 等待子进程
try:
    process.wait()
except KeyboardInterrupt:
    cleanup(None, None)
