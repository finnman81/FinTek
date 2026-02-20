# Anchorpoint

Industrial vertical knowledge web application for equipment service companies. Ingest manuals, SOPs, and technical documentation; get instant, cited answers via a chat interface.

## Features

- **Chat UI**: Next.js frontend (mobile-friendly) with non-streaming RAG answers and source citations.
- **Document ingestion**: PDF, Word, TXT, CSV, Markdown. Upload via web; background worker processes async.
- **Vector store**: Postgres with pgvector (Phase 0); pluggable to Pinecone later.
- **Usage tracking**: Per-tenant token accounting and soft caps.
- **Observability**: Structured JSON logging, latency tracking, CloudWatch-ready.
- **Model-agnostic backend**: OpenAI today; swap providers via configuration.

## Architecture (Production)

- **Frontend**: Next.js (Chat, Upload, Admin) on Vercel or static host.
- **Backend**: FastAPI (chat, documents, admin, auth) + background ingestion worker.
- **Database**: Postgres (single-AZ RDS) with pgvector extension.
- **Storage**: S3 for documents (Terraform).
- **Auth**: Placeholder headers (X-Tenant-ID, X-User-ID); Clerk integration ready.

See [docs/PRODUCTION_BUILD_PLAN.md](docs/PRODUCTION_BUILD_PLAN.md) and [docs/ARCHITECTURE_PROD.md](docs/ARCHITECTURE_PROD.md).

## Setup

### 1. Backend (FastAPI)

```bash
cd FinTek
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

- `OPENAI_API_KEY=sk-...`
- `DATABASE_URL=postgresql://user:pass@host:5432/anchorpoint` (Postgres with pgvector)

**Local Postgres (Docker):** Start Postgres + pgvector with one command. Use a single line in PowerShell (no `\`):

```powershell
docker run --name anchorpoint-pg -e POSTGRES_USER=anchorpoint -e POSTGRES_PASSWORD=anchorpoint -e POSTGRES_DB=anchorpoint -p 5432:5432 -d ankane/pgvector
```

Then set `DATABASE_URL=postgresql://anchorpoint:anchorpoint@localhost:5432/anchorpoint`. After first connect, run in the DB: `CREATE EXTENSION IF NOT EXISTS vector;`

Run migrations (after Postgres is up):

```bash
# Enable pgvector in DB: CREATE EXTENSION IF NOT EXISTS vector;
alembic upgrade head
```

Start the API:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Start the ingestion worker (separate terminal):

```bash
python -m src.workers.ingestion_worker
```

**One-command dev (API + worker + Next.js):** From the project root:

```bash
python scripts/run_dev.py
```

Starts all three; Ctrl+C stops them. API at http://127.0.0.1:8000, web at http://localhost:3000.

**Dev: default tenant** — To avoid entering Tenant ID every time, set in `.env`:

- `DEFAULT_TENANT_SLUG=claw-demo` (or `DEFAULT_TENANT_ID=084fd0d0-043c-4ac9-b995-4faa773c0b32`)

The API will use this tenant when the request does not send `X-Tenant-ID`. In the web app, set `NEXT_PUBLIC_DEFAULT_TENANT_ID` in `web/.env.local` to the same UUID so the UI sends it automatically.

### 2. Frontend (Next.js)

```bash
cd web
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000 and optionally NEXT_PUBLIC_DEFAULT_TENANT_ID
npm install
npm run dev
```

Open http://localhost:3000. Use Chat, Upload, and Admin. Set Tenant ID (or use a UUID from your `tenants` table) for API calls.

### 3. Optional: Streamlit (legacy)

```bash
streamlit run src/ui/app.py
```

Uses ChromaDB and SQLite (no Postgres required).

## Testing

Unit and integration tests use pytest. No database or API keys are required (mocked).

```bash
pip install -r requirements-dev.txt
python -m pytest tests -v
```

With coverage:

```bash
python -m pytest tests -v --cov=src --cov-report=term-missing
```

- **Unit tests** (`tests/unit/`): config, chunker, parsers, prompts, usage, retrieval engine, ingestion pipeline (mocked LLM/vector store).
- **Integration tests** (`tests/integration/`): API health, auth (tenant required), chat, documents (list/upload/status/delete), admin (usage, analytics).

Sample docs for integration/E2E: `python scripts/generate_sample_docs.py` (writes to test/sample_docs/).

**E2E (Playwright):** From `web/`, run `npm run e2e` (requires API and Next.js dev server, and a valid tenant). Uses `test/sample_docs/manual_pump_01.txt`. Set `E2E_TENANT_ID` if needed.

## Configuration

| Item | Where | Description |
|------|--------|--------------|
| API key | `.env` | `OPENAI_API_KEY` (required) |
| Branding | `config/settings.yaml` → `branding` | `product_name`, `customer_name`, `customer_logo`, `accent_color` |
| Chunking | `config/settings.yaml` → `ingestion` | `chunk_size`, `chunk_overlap` |
| Retrieval | `config/settings.yaml` → `retrieval` | `top_k`, `score_threshold`, `use_hybrid`, `use_reranker`, `vector_top_k`, `lexical_top_k`, `rrf_k`, `ef_search`, `final_context_chunks` |
| LLM | `config/settings.yaml` → `llm` | `model`, `temperature`, `max_tokens` |

**Retrieval: hybrid and fallback** — Default is hybrid (dense + lexical + RRF) with optional local cross-encoder reranker. To revert to dense-only during rollout, set in `config/settings.yaml`: `retrieval.use_hybrid: false` and `retrieval.use_reranker: false`. Run hybrid tuning with: `python scripts/tune_retrieval.py --tenant-slug claw-demo --questions claw_manuals/eval_questions_50.json --hybrid`.

## Ops and runbooks

- **Migrations:** After Postgres is up, run `alembic upgrade head`. Ensure `vector` extension is enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
- **Worker:** Run `python -m src.workers.ingestion_worker` (same env as API; requires `DATABASE_URL` and `OPENAI_API_KEY`). Processes pending rows in `ingestion_jobs`.
- **Health:** `/health` and `/api/v1/health` are shallow (no DB). `/api/v1/health/db` runs `SELECT 1` and returns 503 if the database is unreachable; use for load balancer or readiness.
- **Env vars:** See `.env.example`. Required: `OPENAI_API_KEY`, `DATABASE_URL` (for production). No secrets in repo; use GitHub Actions secrets or your provider’s secret store for CI.
- **Sample data:** Integration and E2E tests use `test/sample_docs/`. Generate with `python scripts/generate_sample_docs.py`.

### Seeding the knowledge base (test or customer data)

A **generic seed script** populates the RAG vector store from an index JSON. Use it for claw_manuals (testing) or customer manuals (production); only configuration changes.

**Environment variables:**

| Variable | Description |
|----------|-------------|
| `SEED_INDEX_PATH` | Path to index JSON (array of objects with `relative_path`). |
| `SEED_BASE_PATH` | Base directory where files live; full path = base_path + relative_path. |
| `SEED_TENANT_SLUG` | Tenant slug to use (created if missing). |
| `SEED_TENANT_NAME` | Display name when creating the tenant (optional). |

**Examples:**

```bash
# From claw_manuals (testing) — requires PDFs under claw_manuals/root/claw_manuals/
export SEED_INDEX_PATH=claw_manuals/root/claw_manuals/manual_index.json
export SEED_BASE_PATH=claw_manuals/root/claw_manuals
export SEED_TENANT_SLUG=claw-demo
python scripts/seed_from_index.py

# Or use the wrapper (Bash):
./scripts/seed_claw_manuals.sh          # run seed
./scripts/seed_claw_manuals.sh --dry-run   # list files only
./scripts/seed_claw_manuals.sh --limit 5   # ingest first 5 files
```

```bash
# From customer data (production)
export SEED_INDEX_PATH=/path/to/customer/index.json
export SEED_BASE_PATH=/path/to/customer/manuals
export SEED_TENANT_SLUG=acme-corp
python scripts/seed_from_index.py
```

**Options:** `--dry-run`, `--limit N`, `--index-path`, `--base-path`, `--tenant-slug`, `--tenant-name`. After seeding, set `NEXT_PUBLIC_DEFAULT_TENANT_ID` to the printed tenant UUID to use that tenant in the web app.

**Evaluation (optional):** Run retrieval eval against any tenant and question set to validate tuning (e.g. after changing chunking or prompts):

```bash
python scripts/eval_retrieval.py --tenant claw-demo --questions claw_manuals/eval_questions.json
python scripts/eval_retrieval.py --tenant <UUID> --questions /path/to/questions.json --verbose
```

Question set JSON: array of `{ "question": "...", "expected_source_contains": "..." }`. See `claw_manuals/eval_questions.json` for an example.

## Deployment (Cloud VM)

1. **Provision a VM** (e.g. AWS EC2, Azure VM, DigitalOcean Droplet). Recommended: 2 vCPU, 4 GB RAM.
2. **Install Python 3.11+** and clone the repo. Create a venv and `pip install -r requirements.txt`.
3. **Set environment variables** (e.g. in `.env` or systemd/supervisor env): `OPENAI_API_KEY`, and any overrides.
4. **Run Streamlit** with host binding so it’s reachable:
   ```bash
   streamlit run src/ui/app.py --server.address 0.0.0.0 --server.port 8501
   ```
5. **Put a reverse proxy in front** (e.g. Nginx) with HTTPS (e.g. Let’s Encrypt). Proxy to `http://127.0.0.1:8501`.
6. **Run as a service** (optional): use systemd or a process manager so the app restarts on failure and on reboot.

No auth is included in the MVP; the app is intended for single-tenant deployment (one VM per customer). Restrict access at the network or proxy layer if needed.

## Project layout

```
FinTek/
├── config/settings.yaml    # App and branding config
├── src/
│   ├── core/config.py      # Config loader
│   ├── llm/                # LLM and embedding providers (abstracted)
│   ├── vectorstore/        # ChromaDB implementation
│   ├── ingestion/          # Parsers, chunker, pipeline
│   ├── retrieval/          # RAG engine
│   ├── ui/                 # Streamlit app and components
│   ├── api/                # FastAPI placeholder (Phase 2)
│   └── utils/              # Logging, query store
├── data/                   # Raw docs, ChromaDB, SQLite (gitignored)
├── docs/                   # Architecture docs
├── Context/                # Strategy and planning
├── requirements.txt
└── README.md
```

## Phase 2 (Production)

The [FastAPI placeholder](src/api/routes.py) defines a health check and the pattern for future REST endpoints. In Phase 2, the frontend will call FastAPI instead of the engine directly; the retrieval and ingestion logic stays the same. See [docs/ARCHITECTURE_PROD.md](docs/ARCHITECTURE_PROD.md) for multi-tenant, PostgreSQL, and vector DB migration.

## License

Proprietary.
