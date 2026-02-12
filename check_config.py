"""
配置检查脚本
用于验证个人学习管理软件的配置是否正确
"""

import os
import sys
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("正在检查环境配置...")
    
    # 检查后端目录
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ 后端目录不存在")
        return False
    
    # 检查 .env 文件
    env_path = backend_path / ".env"
    if env_path.exists():
        print("✅ 找到 .env 文件")
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # 检查关键配置项
        if "QWEN_API_KEY" in env_content:
            print("✅ 在 .env 文件中找到 QWEN_API_KEY")
        else:
            print("❌ 在 .env 文件中未找到 QWEN_API_KEY")
            
        if "DATABASE_URL" in env_content:
            print("✅ 在 .env 文件中找到 DATABASE_URL")
        else:
            print("❌ 在 .env 文件中未找到 DATABASE_URL")
    else:
        print("❌ 未找到 .env 文件")
    
    # 检查环境变量
    api_key = os.environ.get('QWEN_API_KEY')
    if api_key:
        print("✅ 系统环境变量中找到 QWEN_API_KEY")
    else:
        print("❌ 系统环境变量中未找到 QWEN_API_KEY")
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print("✅ 系统环境变量中找到 DATABASE_URL")
    else:
        print("❌ 系统环境变量中未找到 DATABASE_URL")
    
    return True

def create_sample_env():
    """创建示例 .env 文件"""
    print("\n正在创建示例 .env 文件...")
    
    sample_env_content = '''# 个人学习管理软件配置文件
# 将此文件重命名为 .env 并填写实际值

# 通义千问 API 配置
# 请前往 https://dashscope.aliyun.com/ 获取API密钥
QWEN_API_KEY=your_actual_api_key_here

# 数据库配置 (MySQL 示例)
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/study_manager

# 或者使用 SQLite (无需安装 MySQL)
# DATABASE_URL=sqlite:///./study_manager.db
'''
    
    backend_path = Path("backend")
    env_path = backend_path / ".env"
    
    if not env_path.exists():
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(sample_env_content)
        print(f"✅ 已创建示例 .env 文件: {env_path.absolute()}")
    else:
        print(f"ℹ️  .env 文件已存在: {env_path.absolute()}")

def main():
    print("🔍 个人学习管理软件配置检查工具")
    print("=" * 50)
    
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"工作目录: {os.getcwd()}")
    
    # 检查环境
    check_environment()
    
    # 创建示例配置文件
    create_sample_env()
    
    print("\n📋 配置说明:")
    print("- 如果您还没有API密钥，请访问 https://dashscope.aliyun.com/ 获取")
    print("- 将正确的API密钥填入 .env 文件中")
    print("- 可以选择使用 MySQL 或 SQLite 数据库")
    print("- 修改完配置后重启后端服务")

if __name__ == "__main__":
    main()