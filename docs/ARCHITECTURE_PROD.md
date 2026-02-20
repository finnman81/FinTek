# Phase 2–3: Production Architecture — Scalable Web Application

## Overview

This document outlines the migration path from the Streamlit MVP to a production-grade,
multi-tenant SaaS platform. The transition is designed to be **incremental** — the core
backend (ingestion, retrieval, LLM abstraction) remains the same while the UI, database,
auth, and deployment layers are upgraded.

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│                                                                     │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐  │
│  │  Next.js Web    │   │  Mobile PWA     │   │  Admin Dashboard │  │
│  │  (React + TS)   │   │  (Responsive)   │   │  (Next.js)       │  │
│  └────────┬────────┘   └────────┬────────┘   └────────┬─────────┘  │
│           │                     │                      │            │
└───────────┼─────────────────────┼──────────────────────┼────────────┘
            │                     │                      │
            └─────────────────────┼──────────────────────┘
                                  │
                           ┌──────┴──────┐
                           │  API Gateway │
                           │  (nginx)     │
                           └──────┬──────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────┐
│                        BACKEND LAYER                                │
│                                                                     │
│  ┌──────────────────────────────┴──────────────────────────────┐    │
│  │                     FastAPI Application                      │    │
│  │                                                              │    │
│  │  ┌────────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │    │
│  │  │ Auth       │  │ Chat     │  │ Ingestion │  │ Admin    │ │    │
│  │  │ Routes     │  │ Routes   │  │ Routes    │  │ Routes   │ │    │
│  │  └─────┬──────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘ │    │
│  │        │              │              │              │        │    │
│  │  ┌─────┴──────────────┴──────────────┴──────────────┴─────┐ │    │
│  │  │              Middleware Layer                            │ │    │
│  │  │  (Auth, Tenant Resolution, Rate Limiting, Logging)     │ │    │
│  │  └────────────────────────┬────────────────────────────────┘ │    │
│  └───────────────────────────┼──────────────────────────────────┘    │
│                              │                                       │
│  ┌───────────────────────────┼──────────────────────────────────┐    │
│  │               SERVICE LAYER (Same core as MVP)               │    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │ Retrieval    │  │ Ingestion    │  │ Analytics        │  │    │
│  │  │ Engine       │  │ Pipeline     │  │ Engine           │  │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │    │
│  │         │                 │                                  │    │
│  │  ┌──────┴───────┐  ┌──────┴───────┐                        │    │
│  │  │ LLM Provider │  │ Embedding    │                        │    │
│  │  │ (Pluggable)  │  │ Provider     │                        │    │
│  │  └──────────────┘  └──────────────┘                        │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                    │                    │
    ┌───────────────┼────────────────────┼───────────────┐
    │               │                    │               │
    ▼               ▼                    ▼               ▼
┌────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐
│Postgres│  │ Pinecone / │  │  Redis       │  │  S3 / Blob   │
│  (App  │  │ Weaviate   │  │  (Cache +    │  │  (Document   │
│  Data) │  │ (Vectors)  │  │   Sessions)  │  │   Storage)   │
└────────┘  └────────────┘  └──────────────┘  └──────────────┘
```

---

## Migration Path: MVP → Production

### Phase 2 (Customers 3–10): Standardized SaaS

| Component       | MVP (Phase 1)         | Phase 2                        |
|-----------------|-----------------------|--------------------------------|
| **Frontend**    | Streamlit             | Streamlit (improved) or early Next.js |
| **API**         | Direct function calls | FastAPI REST API               |
| **Vector DB**   | ChromaDB (local)      | ChromaDB (server mode) or Pinecone |
| **App DB**      | SQLite                | PostgreSQL                     |
| **Auth**        | Streamlit secrets     | JWT + API keys                 |
| **Deployment**  | Single VM per client  | Docker containers, config-driven |
| **File Storage**| Local filesystem      | S3-compatible (MinIO or AWS S3)|
| **Monitoring**  | Log files             | Structured logging + Sentry    |

### Phase 3 (Customers 10+): Multi-Tenant Platform

| Component       | Phase 2               | Phase 3                        |
|-----------------|-----------------------|--------------------------------|
| **Frontend**    | Streamlit / early Next| Next.js + Tailwind (PWA)       |
| **API**         | FastAPI               | FastAPI + WebSockets           |
| **Vector DB**   | ChromaDB / Pinecone   | Pinecone / Weaviate (managed)  |
| **App DB**      | PostgreSQL            | PostgreSQL (multi-tenant schema)|
| **Auth**        | JWT + API keys        | Auth0 / Clerk + RBAC           |
| **Deployment**  | Docker per tenant     | Kubernetes (EKS/GKE)           |
| **File Storage**| S3                    | S3 with lifecycle policies     |
| **Cache**       | None                  | Redis (sessions + query cache) |
| **CDN**         | None                  | CloudFront / Vercel Edge       |
| **CI/CD**       | Manual                | GitHub Actions → auto deploy   |

---

## Multi-Tenancy Strategy

### Data Isolation Model: Schema-per-Tenant (Recommended for Phase 2–3)

```
PostgreSQL
├── public schema          (shared: tenant registry, plans, global config)
├── tenant_fintek schema   (tenant-specific: users, query_logs, documents)
├── tenant_acme schema     (tenant-specific: users, query_logs, documents)
└── tenant_beta schema     (tenant-specific: users, query_logs, documents)

Pinecone / Weaviate
├── namespace: fintek      (tenant-specific vector collections)
├── namespace: acme        (tenant-specific vector collections)
└── namespace: beta        (tenant-specific vector collections)
```

**Why schema-per-tenant:**
- True data isolation (critical for B2B trust)
- Easy to export/delete a single customer's data
- No risk of cross-tenant data leakage
- Can migrate individual tenants to dedicated infrastructure if needed

---

## Production Technology Stack

| Layer              | Technology                | Rationale                              |
|--------------------|---------------------------|----------------------------------------|
| **Frontend**       | Next.js 14+ (App Router)  | SSR, mobile-first, modern React        |
| **UI Framework**   | Tailwind CSS + shadcn/ui  | Rapid, consistent, accessible UI       |
| **API**            | FastAPI (Python)          | Async, auto-docs, type-safe            |
| **Auth**           | Clerk or Auth0            | Enterprise SSO, RBAC, zero custom auth |
| **App Database**   | PostgreSQL (Supabase or RDS) | Battle-tested, multi-tenant ready   |
| **Vector Database**| Pinecone (managed)        | Scalable, zero-ops, namespace isolation|
| **Cache**          | Redis (Upstash or ElastiCache) | Session store + query cache       |
| **File Storage**   | AWS S3 / Cloudflare R2    | Durable, cost-effective document store |
| **LLM**           | OpenAI (primary), Anthropic (fallback) | Model-agnostic via abstraction |
| **Embeddings**     | OpenAI or Cohere          | Pluggable via abstraction layer        |
| **Search**         | Hybrid: vector + BM25     | Better recall for technical terms      |
| **Monitoring**     | Sentry + Posthog          | Error tracking + product analytics     |
| **Deployment**     | Docker → Kubernetes       | Horizontal scaling, rolling deploys    |
| **CI/CD**          | GitHub Actions            | Automated testing + deployment         |

---

## Model-Agnostic LLM Design

The abstraction layer allows hot-swapping LLM providers without touching business logic:

```python
# All providers implement this interface
class BaseLLMProvider(ABC):
    def generate(self, messages, **kwargs) -> LLMResponse
    def stream(self, messages, **kwargs) -> Iterator[str]

class BaseEmbeddingProvider(ABC):
    def embed_text(self, text) -> list[float]
    def embed_batch(self, texts) -> list[list[float]]

# Configuration-driven provider selection
# settings.yaml:
#   llm:
#     provider: "openai"        # or "anthropic", "local", "azure_openai"
#     model: "gpt-4o"
#   embeddings:
#     provider: "openai"        # or "cohere", "local"
#     model: "text-embedding-3-small"
```

**Supported providers (current + planned):**
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)
- Azure OpenAI (for enterprise compliance)
- Local models via Ollama (for fully on-prem)
- Cohere (embeddings)

---

## API Design (FastAPI)

### Core Endpoints

```
POST   /api/v1/auth/login              # Authenticate user
POST   /api/v1/auth/refresh            # Refresh JWT token

POST   /api/v1/chat                     # Send message, get response
GET    /api/v1/chat/history             # Get conversation history
DELETE /api/v1/chat/history/{id}        # Delete conversation

POST   /api/v1/documents/upload         # Upload document(s)
GET    /api/v1/documents                # List all documents
DELETE /api/v1/documents/{id}           # Remove document + vectors
GET    /api/v1/documents/{id}/status    # Ingestion status

GET    /api/v1/admin/analytics          # Usage analytics
GET    /api/v1/admin/queries            # Query logs
GET    /api/v1/admin/knowledge-gaps     # Unanswered/low-confidence queries
GET    /api/v1/admin/users              # User management

GET    /api/v1/health                   # Health check
```

---

## Security (Production)

- **Authentication**: JWT tokens with refresh rotation
- **Authorization**: Role-based (Admin, Technician, Viewer)
- **Data Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Tenant Isolation**: Schema-per-tenant + namespace-per-tenant
- **API Rate Limiting**: Per-tenant and per-user limits
- **Audit Logging**: All admin actions logged
- **SOC 2 path**: Structured for future compliance

---

## Estimated Production Costs (per month, at 10 tenants)

| Service            | Estimated Cost  |
|--------------------|-----------------|
| Vercel (Frontend)  | $20             |
| AWS ECS / Fly.io   | $50–150         |
| PostgreSQL (RDS)   | $30–80          |
| Pinecone           | $70–200         |
| Redis (Upstash)    | $10–30          |
| S3 Storage         | $5–20           |
| OpenAI API         | $300–1,000      |
| Monitoring         | $30–50          |
| **Total**          | **$515–1,530**  |

At $2,500 MRR per customer x 10 = $25,000 MRR → healthy margins.

---

## Scaling Triggers

| Signal                         | Action                                    |
|--------------------------------|-------------------------------------------|
| 5+ customers on Streamlit      | Begin Next.js frontend migration          |
| Query latency > 3s             | Add Redis caching layer                   |
| 10+ customers                  | Migrate to multi-tenant Kubernetes        |
| Enterprise inquiry             | Deploy Azure OpenAI + dedicated infra     |
| >100k documents per tenant     | Evaluate Weaviate for hybrid search       |
