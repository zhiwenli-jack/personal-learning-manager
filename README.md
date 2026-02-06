# 个人学习管理软件

基于 AI 的个人学习管理系统，支持资料上传、智能题目生成、答题测评、错题管理。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Vite + Axios
- **AI**: 通义千问 API (Qwen)
- **包管理**: uv (Python), bun/npm (JavaScript)

## 快速开始

### 1. 配置环境

编辑 `backend/.env` 文件，配置以下内容：

```env
# 通义千问 API（必填）
QWEN_API_KEY=your-api-key-here
QWEN_MODEL=qwen-plus

# SQLite 数据库（默认配置，无需修改）
DATABASE_URL=sqlite:///./study_manager.db
```

### 2. 安装依赖

```bash
# 安装后端依赖 (使用 uv)
cd backend
uv sync

# 安装前端依赖 (使用 bun)
cd ../frontend
bun install
```

### 3. 启动后端

```bash
python start_backend.py
```

后端启动后访问 http://localhost:8000/docs 查看 API 文档。

### 4. 启动前端

```bash
python start_frontend.py
```

前端启动后访问 http://localhost:5173

## 项目结构

```
个人学习管理软件/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 配置和数据库
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模式
│   │   └── services/      # 业务服务
│   ├── .env               # 环境变量配置
│   └── pyproject.toml
├── frontend/              # Vue 前端
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── router/       # 路由配置
│   │   └── views/        # 页面组件
│   └── package.json
├── start_backend.py       # 后端启动脚本
└── start_frontend.py      # 前端启动脚本
```

## 功能说明

1. **学习方向管理**: 创建编程、数学、语言等学习方向
2. **资料上传**: 上传学习资料，系统自动提炼知识点并生成题目
3. **测验模式**: 支持限时/不限时，100分制/等级制
4. **智能评分**: 客观题自动评分，主观题 AI 评分
5. **错题本**: 自动收集错题，支持复习和掌握标记

## API 文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 推送到 GitHub

本项目已初始化 Git 仓库，如需推送到 GitHub，请按以下步骤操作：

### 方法1：使用 GitHub CLI（推荐）

```bash
# 安装 GitHub CLI
winget install --id GitHub.cli

# 重启终端后，认证 GitHub
gh auth login

# 推送到远程仓库
cd "个人学习管理软件"
git remote add origin https://github.com/YOUR_USERNAME/personal-learning-manager.git
git push -u origin main
```

### 方法2：使用 Personal Access Token

#### 步骤1：创建 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens/new
2. 填写信息：
   - **Note**: `personal-learning-manager`
   - **Expiration**: `90 days` 或 `No expiration`
   - **Select scopes**: 勾选 `repo`（完整仓库访问权限）
3. 点击 "Generate token"
4. **复制生成的 Token**（格式：`ghp_xxxx...`）

#### 步骤2：配置并推送

```bash
cd "个人学习管理软件"

# 添加远程仓库（使用 Token）
git remote add origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/personal-learning-manager.git

# 推送代码
git branch -M main
git push -u origin main
```

替换：
- `YOUR_USERNAME`: 您的 GitHub 用户名
- `YOUR_TOKEN`: 刚才创建的 Personal Access Token

### 方法3：使用 SSH 密钥

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub: https://github.com/settings/ssh/new

# 配置远程仓库并推送
cd "个人学习管理软件"
git remote add origin git@github.com:YOUR_USERNAME/personal-learning-manager.git
git branch -M main
git push -u origin main
```

---

## 开发注意事项

- **数据库**: 项目使用 SQLite，数据文件 `study_manager.db` 会自动创建在 `backend/` 目录
- **API 超时**: 前端 API 请求超时设置为 3 分钟，适应 AI 处理时间
- **进度展示**: 资料上传后会显示实时生成进度（SSE 流式传输）
- **题目管理**: 支持查看、编辑、删除题目，可对题目进行"好题/待优化"评价

