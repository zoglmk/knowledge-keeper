# Knowledge Keeper

AI 驱动的知识管理应用 - 一站式知识收集、整理、学习平台

## ✨ 功能特点

- 📥 **智能收藏**: 支持 URL、笔记、文件多种形式
- 🤖 **AI 摘要**: 自动生成内容摘要
- 🏷️ **智能标签**: AI 自动分析内容生成标签
- 🔍 **语义搜索**: 基于向量的智能搜索
- 💬 **知识问答**: 基于 RAG 的智能对话
- 📊 **数据统计**: 可视化展示知识库状态

## 🛠️ 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Zustand (状态管理)
- React Query (数据获取)
- Tailwind CSS (可选)

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy (异步)
- ChromaDB (向量数据库)

### AI 模型支持
- OpenAI (GPT-4, GPT-3.5)
- Claude (claude-3-opus, claude-3-sonnet)
- Google Gemini
- 豆包 (字节跳动)
- Deepseek

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- pnpm 或 npm

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，配置你的 AI API Key
# 例如使用豆包:
# AI_PROVIDER=doubao
# DOUBAO_API_KEY=your-api-key

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
pnpm install  # 或 npm install

# 启动开发服务器
pnpm dev  # 或 npm run dev
```

### 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 📁 项目结构

```
.
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/      # 可复用组件
│   │   ├── pages/           # 页面
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── services/        # API 服务
│   │   ├── stores/          # 状态管理
│   │   └── styles/          # 样式
│   └── ...
│
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模型
│   │   └── services/        # 业务服务
│   └── ...
│
└── README.md
```

## 🔧 配置说明

### AI 模型配置

在 `backend/.env` 文件中配置:

```env
# 选择 AI 提供商
AI_PROVIDER=doubao  # 可选: openai, claude, gemini, doubao, deepseek

# 豆包配置
DOUBAO_API_KEY=your-api-key
DOUBAO_MODEL=doubao-pro-4k
```

## 📄 API 文档

启动后端服务后，访问以下地址查看 API 文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📝 License

MIT License
