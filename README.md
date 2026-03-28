# AI RAG System

> Intelligent Learning Assistant — Documents · Vector Search · LLM Answer

基于 FastAPI + FAISS + bge-small-zh 的 RAG 学习助手，支持文档管理、智能问答、习题生成、笔记整理与题目解析。

---

## 功能特性

### 检索问答
- 向量相似度检索（bge-small-zh embedding）
- 结合 LLM（OpenAI-compatible API）生成回答
- 支持调节 Top-K 数量
- Markdown 渲染 + 源码切换

### 学习工具
| 模块 | 说明 |
|------|------|
| **生成习题** | 输入材料生成单选题/多选题/填空题/简答题，答案与解析集中在末尾；可结合知识库扩展 |
| **笔记生成** | 输入主题从知识库检索相关片段，生成结构化 Markdown 笔记；自动保存草稿 |
| **题目解析** | 输入任意题目（含可选答案），获取详细知识点讲解与延伸思考 |

### 文档管理
- 手动录入文档（标题 + 内容）
- Word `.docx` 拖拽导入（服务端解析）
- 文档列表过滤、查看、删除

---

## 技术架构

```
app/
├── main.py              # FastAPI 入口，CORS / 静态文件 / 生命周期管理
├── core/config.py       # 环境配置（Pydantic Settings）
├── routers/
│   ├── health.py        # 健康检查 & 索引状态
│   ├── search.py        # 检索 + LLM 问答
│   ├── documents.py     # 文档 CRUD
│   └── tools.py         # 习题生成 / 笔记生成 / 题目解析
├── services/
│   ├── retrieval.py     # FAISS 向量检索
│   ├── embedding.py     # bge-small-zh embedding
│   ├── faiss_store.py   # FAISS 索引持久化
│   ├── chunking.py      # 文本分块
│   ├── llm.py           # OpenAI-compatible LLM 调用
│   └── docx_text.py     # docx 文件文本提取
└── db/
    ├── database.py      # SQLite / PostgreSQL ORM 抽象
    ├── postgres.py      # 异步 PostgreSQL 连接池（可选）
    └── postgres_sync.py # 同步 PostgreSQL（可选）
```

- **Embedding**: `bge-small-zh`（1024 维）
- **向量索引**: FAISS IndexFlatIP（余弦相似度）
- **LLM**: OpenAI-compatible API（默认 Qwen 7B）
- **数据库**: SQLite（默认）/ PostgreSQL（可选）
- **Chunk**: 默认 ~400 字符，50 字符 overlap

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# .env 示例
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1   # 或你的代理地址
# DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # 可选：使用 PostgreSQL
```

### 3. 启动服务

```bash
cd /path/to/ai-rag-system
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 `http://localhost:8000` 打开 Web UI。

---

## 前端界面

- **Eco-themed UI**：柔和大地色系 + 森林绿主色调，支持亮色 / 暗色主题切换
- **语言**：内置中文 / English 双语，通过语言切换按钮即时切换
- **主题与语言**偏好自动保存至 `localStorage`

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 静态页面 |
| GET | `/health` | 健康检查 |
| GET | `/health/index` | 索引状态（文档数） |
| POST | `/search` | 检索 + LLM 问答 |
| GET | `/documents` | 文档列表 |
| POST | `/documents` | 创建文档 |
| DELETE | `/documents/{id}` | 删除文档 |
| POST | `/tools/generate-questions` | 生成习题 |
| POST | `/tools/generate-notes` | 生成笔记 |
| POST | `/tools/analyze-question` | 题目解析 |

---

## 扩展方向

- 切换 Embedding 模型（`sentence-transformers` 支持任意模型）
- 接入 PostgreSQL + pgvector 实现大规模向量存储
- 接入 LangChain / LlamaIndex 增强 LLM 调用链
- 部署至 Docker / Kubernetes
