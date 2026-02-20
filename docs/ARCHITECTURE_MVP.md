# Phase 1: MVP Architecture — Local-First Streamlit Application

## Overview

The MVP is a **single-tenant, local-first** deployment designed to validate the product
with 1–3 early-adopter equipment service companies. It uses Streamlit as the UI,
ChromaDB for local vector storage, and OpenAI as the LLM backend.

The entire system runs on a single machine or VM with no external database dependencies
beyond the OpenAI API.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI                            │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Chat      │  │ Document     │  │ Admin Panel           │ │
│  │ Interface │  │ Upload       │  │ (Query Logs, Stats)   │ │
│  └─────┬─────┘  └──────┬───────┘  └───────────┬───────────┘ │
│        │               │                      │             │
└────────┼───────────────┼──────────────────────┼─────────────┘
         │               │                      │
         ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Retrieval    │  │ Ingestion    │  │ Query Logger     │  │
│  │ Engine       │  │ Pipeline     │  │                  │  │
│  │              │  │              │  │ (SQLite)         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                                  │
│  ┌──────┴───────┐  ┌──────┴───────┐                        │
│  │ LLM Provider │  │ Embedding    │                        │
│  │ (Abstracted) │  │ Provider     │                        │
│  │              │  │ (Abstracted) │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         │                 │                                  │
└─────────┼─────────────────┼──────────────────────────────────┘
          │                 │
          ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│  OpenAI API  │  │  ChromaDB        │
│  (GPT-4o)    │  │  (Local Storage) │
│              │  │  + Embeddings    │
└──────────────┘  └──────────────────┘
```

---

## Technology Stack

| Layer          | Technology              | Rationale                                      |
|----------------|-------------------------|-------------------------------------------------|
| **UI**         | Streamlit               | Fastest path to interactive UI; mobile-friendly |
| **Vector DB**  | ChromaDB (local)        | Zero infrastructure; file-based persistence     |
| **LLM**       | OpenAI GPT-4o           | Best reasoning for technical Q&A                |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective, high quality             |
| **Query Logs** | SQLite                  | Zero-config local database                      |
| **Ingestion**  | LangChain document loaders + custom parsers | Handles PDF, DOCX, TXT, CSV |
| **Chunking**   | Recursive character splitter with overlap   | Preserves context windows    |
| **Language**   | Python 3.11+            | Ecosystem maturity for ML/AI                    |

---

## Data Flow

### 1. Document Ingestion
```
Upload (PDF/DOCX/TXT/CSV)
    → File validation & metadata extraction
    → Text extraction (PyMuPDF / python-docx / csv)
    → Chunking (RecursiveCharacterTextSplitter)
        - chunk_size: 1000 tokens
        - chunk_overlap: 200 tokens
    → Metadata tagging (source, page, section, upload_date, doc_type)
    → Embedding generation (OpenAI text-embedding-3-small)
    → Store in ChromaDB collection (with metadata filters)
```

### 2. Query / Chat Flow
```
User question
    → Query embedding generation
    → ChromaDB similarity search (top-k=5, with metadata filters)
    → Retrieved chunks + metadata assembled into context
    → System prompt + context + user question → LLM
    → Structured response with source citations
    → Log query + response + sources to SQLite
    → Display in Streamlit chat interface
```

---

## Key Design Decisions (MVP)

1. **Local ChromaDB**: No cloud vector DB costs; data stays on-prem for customer trust
2. **Abstracted LLM layer**: `BaseLLMProvider` interface so we can swap OpenAI for Anthropic, local models, etc.
3. **Abstracted Vector Store**: `BaseVectorStore` interface so ChromaDB can be swapped for Pinecone/Weaviate later
4. **SQLite query logging**: Enables analytics without infrastructure; migrates to PostgreSQL later
5. **Single-tenant by design**: Each customer gets their own deployment (matches Phase 1 strategy)
6. **Source citation**: Every response includes document name, page number, and relevant section

---

## File Structure (MVP)

```
FinTek/
├── config/
│   └── settings.yaml           # App configuration (chunk sizes, model params, etc.)
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration loader
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Orchestrates full ingestion flow
│   │   ├── parsers.py          # File-type-specific text extractors
│   │   └── chunker.py          # Text chunking strategies
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseLLMProvider abstract class
│   │   ├── openai_provider.py  # OpenAI implementation
│   │   └── prompts.py          # System prompts & prompt templates
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseVectorStore abstract class
│   │   └── chroma_store.py     # ChromaDB implementation
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── engine.py           # RAG retrieval + response generation
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # (Future) FastAPI routes placeholder
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py              # Main Streamlit app entry point
│   │   ├── pages/
│   │   │   ├── chat.py         # Chat interface page
│   │   │   ├── upload.py       # Document upload page
│   │   │   └── admin.py        # Admin / analytics page
│   │   └── components/
│   │       ├── sidebar.py      # Navigation sidebar
│   │       └── chat_message.py # Chat message display component
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Application logging
│       └── query_store.py      # SQLite query logging
├── data/
│   ├── raw/                    # Uploaded source documents
│   ├── processed/              # Chunked + embedded data (ChromaDB files)
│   └── logs/                   # Query logs (SQLite DB)
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_vectorstore.py
├── docs/
│   ├── ARCHITECTURE_MVP.md     # This document
│   └── ARCHITECTURE_PROD.md    # Production architecture
├── Context/                    # Strategic planning documents
├── .env.example                # Environment variable template
├── .gitignore
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                   # Setup & usage instructions
```

---

## Deployment (MVP)

### Option A: Local Machine
- Customer's on-prem Windows/Linux server
- Run via `streamlit run src/ui/app.py`
- Data never leaves their network (except OpenAI API calls)

### Option B: Single VM (Cloud)
- AWS EC2 / Azure VM / DigitalOcean Droplet
- Nginx reverse proxy → Streamlit
- SSL via Let's Encrypt
- Isolated per customer

### Estimated Costs (per customer)
| Item           | Monthly Cost  |
|----------------|---------------|
| VM (2 vCPU)    | $20–40        |
| OpenAI API     | $30–100       |
| Domain + SSL   | ~$1           |
| **Total**      | **$51–141**   |

---

## Security Considerations (MVP)

- API keys stored in `.env` (never committed)
- Streamlit password protection via `st.secrets`
- Customer data isolated per deployment
- OpenAI API calls are the only external data transfer
- All uploaded documents stored locally on the deployment machine
