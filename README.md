# AI RAG System

> Intelligent Learning Assistant — Document Management, Vector Search, and LLM-Powered Responses

AI RAG System is a Retrieval-Augmented Generation learning assistant built on FastAPI, FAISS, and the bge-small-zh embedding model. It provides document management, intelligent Q&A, exercise generation, note organization, question analysis, study planning, and translation capabilities.

---

## Features

### Retrieval-Augmented Q&A
- Vector similarity search powered by bge-small-zh embeddings (1024 dimensions)
- LLM responses generated via OpenAI-compatible API based on retrieved context
- Adjustable Top-K parameter for retrieval granularity
- Markdown rendering with source reference toggling

### Exercise Generation
- Generate single-choice, multiple-choice, fill-in-the-blank, and essay questions from source materials
- Answers and detailed analysis consolidated at the end of each output
- Optional knowledge base augmentation for expanded question generation

### Note Generation
- Input a topic to retrieve relevant content chunks from the knowledge base
- Generate structured Markdown notes automatically
- Auto-saved drafts for continued editing

### Question Analysis
- Submit any question (with optional answer choices) for detailed explanation
- Provides knowledge point breakdowns, problem-solving strategies, and extended reflection

### Study Plan Generation
- Personalized weekly study plans tailored to user proficiency level
- Accounts for known topics, weak areas, preferred learning style, target subject, plan duration, and daily available hours
- Optionally enhanced with knowledge base content

### Translation Assistant
- Three translation modes: Direct Translation, Refined Translation, Polished Translation
- Supports 12 languages: Chinese, English, Japanese, Korean, French, German, Spanish, Russian, Arabic, Italian, Portuguese (with auto-detection)

### Document Management
- Manual document entry (title and content)
- Word `.docx` drag-and-drop import with server-side text extraction
- Document listing with filtering, viewing, and deletion

---

## Technical Architecture

```
app/
|-- main.py              # FastAPI entry point; CORS, static files, lifecycle management
|-- core/
|   |-- config.py        # Environment configuration via Pydantic Settings
|-- routers/
|   |-- health.py        # Health check and index status
|   |-- search.py        # Retrieval and LLM Q&A
|   |-- documents.py      # Document CRUD operations
|   |-- tools.py          # Exercise generation, note generation, question analysis, translation
|   |-- study_plan.py     # Personalized study plan generation
|   |-- settings.py       # Static page routing
|-- services/
|   |-- retrieval.py      # FAISS vector retrieval
|   |-- embedding.py      # bge-small-zh embedding via sentence-transformers
|   |-- faiss_store.py    # FAISS index persistence
|   |-- chunking.py       # Text chunking
|   |-- llm.py            # OpenAI-compatible LLM invocation
|   |-- docx_text.py      # .docx file text extraction
|   |-- study_plan_generator.py  # Fallback study plan generation
|   |-- index_queue.py    # Background indexing worker
|-- db/
|   |-- database.py       # SQLite ORM abstraction
|   |-- postgres.py       # Async PostgreSQL connection pool (optional)
|   |-- postgres_sync.py  # Sync PostgreSQL (optional)
```

### Core Technologies
- **Embedding Model**: bge-small-zh (1024 dimensions, normalized)
- **Vector Index**: FAISS IndexFlatIP (inner product for cosine similarity)
- **LLM**: OpenAI-compatible API (default: Qwen 7B)
- **Database**: SQLite (default) / PostgreSQL (optional)
- **Text Chunking**: Default ~400 characters with 50-character overlap
- **Async Processing**: ThreadPoolExecutor for CPU-bound embedding computation
- **Background Workers**: Queue-based indexing worker for document processing

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# .env example
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1   # or your proxy address
# DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # Optional: use PostgreSQL
```

### 3. Start the Service

```bash
cd /path/to/ai-rag-system
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access `http://localhost:8000` to open the Web UI.

---

## Frontend Interface

- **Design**: Eco-themed UI with warm earth tones and forest green accents, supporting light/dark theme switching
- **Internationalization**: Built-in Chinese/English bilingual support with real-time language toggle
- **Persistence**: Theme and language preferences saved to localStorage

---

![Overview](overview.jpg)


## API Reference

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Static page (home) |
| GET | `/health` | Health check |
| GET | `/health/index` | Index status (document count) |
| POST | `/search` | Vector search + LLM Q&A |

### Document Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/documents` | Document list |
| POST | `/documents` | Create document |
| DELETE | `/documents/{id}` | Delete document |

### Learning Tools

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/generate-questions` | Generate exercises |
| POST | `/tools/markdown-notes` | Generate study notes |
| POST | `/tools/analyze-question` | Analyze questions |

### Study Planning

| Method | Path | Description |
|--------|------|-------------|
| POST | `/study-plan/generate` | Generate personalized study plan |

### Translation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/translate` | Translate text |

### Page Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/qa` | Q&A page |
| GET | `/questions` | Exercise generation page |
| GET | `/notes` | Note generation page |
| GET | `/analysis` | Question analysis page |
| GET | `/study-plan` | Study plan page |
| GET | `/translation` | Translation page |
| GET | `/settings` | Settings page |

---

## Extension Possibilities

- Swap embedding models (sentence-transformers supports arbitrary models)
- Integrate PostgreSQL + pgvector for large-scale vector storage
- Integrate LangChain / LlamaIndex for enhanced LLM orchestration
- Deploy via Docker / Kubernetes for production environments
