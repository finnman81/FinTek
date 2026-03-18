# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Munitor AI is an industrial RAG (Retrieval-Augmented Generation) knowledge app with:
- **FastAPI backend** (port 8000) — chat, documents, admin, auth, feedback APIs
- **Next.js 14 frontend** (port 3000) — Chat, Upload, Admin pages
- **PostgreSQL + vector extension** (port 5432) — data store with vector embeddings
- **Ingestion worker** — background process for document parsing/embedding

### Starting services

Docker must be running before starting PostgreSQL. Start services in this order:

1. **Docker daemon:** `sudo dockerd &>/tmp/dockerd.log &` (wait ~3s)
2. **PostgreSQL:** `sudo docker start munitor-pg` (or create if first run — see README)
3. **Run migrations:** Set `DATABASE_URL` to the local Postgres connection string (see `.env.example` for format), then run `alembic upgrade head`
4. **FastAPI:** `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000` (ensure `DATABASE_URL` env var is set)
5. **Next.js:** `cd web && npm run dev` (port 3000)
6. **Worker (optional):** `python3 -m src.workers.ingestion_worker` (ensure `DATABASE_URL` env var is set)

Or use the convenience script `python3 scripts/run_dev.py` (starts API + worker + Next.js together).

### Important caveats

- The injected `DATABASE_URL` secret may point to a different port (e.g. 5433). The local Docker PostgreSQL runs on port 5432. **Override `DATABASE_URL` explicitly** when running backend commands. Use the connection string format from `.env.example` with `localhost:5432` as the host.
- `~/.local/bin` must be on PATH for Python CLI tools (alembic, ruff, uvicorn). The update script handles this.
- `npm install --legacy-peer-deps` is needed in `web/` due to a peer dependency conflict between `@clerk/nextjs@^4.29.0` and `next@14.2.0`.
- The `.gitignore` has a blanket `lib/` pattern (for Python venvs). Use `git add -f` when adding files under `web/src/lib/`.

### Lint and test commands

See README for full details. Quick reference:
- **Python lint:** `ruff check .` (from project root)
- **Python tests:** `python3 -m pytest tests -v --tb=short` (90 pass, 9 pre-existing failures)
- **Frontend lint:** `cd web && npx next lint`
- **Frontend build:** `cd web && npx next build`
- **Frontend E2E:** `cd web && npm run e2e` (requires running API + Next.js + valid tenant)

### Dev tenant for testing

A dev tenant can be created via: `sudo docker exec munitor-pg psql -U munitor -d munitor -c "INSERT INTO tenants (id, name, slug) VALUES ('00000000-0000-0000-0000-000000000001', 'Dev Tenant', 'dev-tenant') ON CONFLICT DO NOTHING;"`

Use tenant ID `00000000-0000-0000-0000-000000000001` in the UI or as `X-Tenant-ID` header for API calls.
