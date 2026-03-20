# AWS Backend Transition Plan — Munitor AI

## Objective

Migrate Munitor AI from OpenAI-dependent embedding and LLM services to a fully AWS-native backend using Amazon Bedrock, while transitioning the database from self-managed PostgreSQL to Aurora PostgreSQL. This enables multimodal embeddings (text + images from documents), reduces external API dependencies, and establishes the multi-tenant framework for scaling to new companies.

---

## Current State → Target State

| Component | Current | Target |
|-----------|---------|--------|
| **Embedding model** | OpenAI `text-embedding-3-small` (1536d, text-only) | Amazon Nova Multimodal Embeddings via Bedrock (1024d default, configurable) |
| **LLM (chat)** | OpenAI `gpt-4.1` | Amazon Bedrock (Claude via Anthropic on Bedrock) |
| **Reranker** | Local `cross-encoder/ms-marco-MiniLM-L-6-v2` (CPU inference) | Cohere Rerank 3.5 via Bedrock Rerank API |
| **Vector dimensions** | 1536 (hardcoded in schema) | 1024 default (configurable via `settings.yaml`) |
| **Modalities embedded** | Text only (PDF/DOCX text extracted, images discarded) | Text + page-level image renders (interleaved multimodal input) |
| **Database** | RDS PostgreSQL 16 (`db.t4g.micro`) with pgvector | Aurora PostgreSQL with pgvector (start `db.t4g.medium`, scale as needed) |
| **Embedding API call path** | App Runner / Lambda → NAT → OpenAI API (public internet) | App Runner / Lambda → VPC Endpoint → Bedrock (AWS backbone, no internet egress) |
| **LLM API call path** | App Runner → NAT → OpenAI API (public internet) | App Runner → VPC Endpoint → Bedrock (AWS backbone) |
| **Secrets** | `openai-api-key` in Secrets Manager | No API key needed — IAM role auth to Bedrock |

---

## Architecture Changes

### Network: Add Bedrock VPC Endpoint

Currently, Lambda and App Runner use the NAT gateway to reach the OpenAI API over the public internet. With Bedrock, traffic stays on the AWS backbone via a VPC interface endpoint.

```
BEFORE:
  App Runner / Lambda → NAT Gateway → Internet → OpenAI API

AFTER:
  App Runner / Lambda → VPC Endpoint (bedrock-runtime) → Bedrock API
  (no internet egress, no NAT charges for embedding/LLM calls)
```

**CDK change:** Add a VPC interface endpoint for `com.amazonaws.{region}.bedrock-runtime` in `VpcStack`. Attach it to private subnets with the Lambda and App Runner security groups.

**Cost benefit:** NAT gateway charges ~$0.045/GB for data processed. Embedding and LLM calls can generate meaningful traffic at scale. The VPC endpoint costs $0.01/hr/AZ (~$14.40/month for 2 AZs) but eliminates all NAT charges for Bedrock traffic.

### Database: RDS → Aurora PostgreSQL

Aurora PostgreSQL with pgvector replaces the current RDS PostgreSQL instance.

**Why Aurora over RDS:**
- Up to 67× faster vector loading with pgvector on Aurora (AWS published benchmark)
- Storage auto-scales transparently (no pre-allocated disk sizing)
- Read replicas for query scaling without custom replication setup
- Point-in-time recovery with continuous backup
- Same pgvector extension, same SQL, same Alembic migrations

**CDK change:** Replace `rds.DatabaseInstance` with `rds.DatabaseCluster` (Aurora Serverless v2 or provisioned) in `RdsStack`. Start with `db.t4g.medium` (2 vCPU, 4 GB) for dev — this handles the initial dataset and early tenants comfortably.

**Migration path:** Export/import via `pg_dump`/`pg_restore`, or use AWS DMS for zero-downtime cutover. Since the production dataset is a fresh start, a clean schema deploy via `alembic upgrade head` on the new Aurora instance is simplest.

### Embedding Provider: BedrockEmbeddingProvider

A new embedding provider that calls Nova Multimodal Embeddings through `boto3` Bedrock runtime.

**Location:** `src/llm/bedrock_provider.py`

**Interface contract** (extends existing `BaseEmbeddingProvider`):

```python
class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    """Amazon Nova Multimodal Embeddings via Bedrock."""

    def __init__(self, region: str, model_id: str, dimensions: int):
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id  # "amazon.nova-2-multimodal-embeddings-v1:0"
        self._dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""

    def embed_image(self, image_bytes: bytes, mime_type: str) -> list[float]:
        """Embed a single image."""

    def embed_multimodal(self, text: str, image_bytes: bytes, mime_type: str) -> list[float]:
        """Embed interleaved text + image (single chunk with both modalities)."""

    @property
    def dimensions(self) -> int:
        return self._dimensions
```

**Key differences from OpenAI provider:**
- No API key — uses IAM role credentials automatically via boto3's credential chain
- Supports image and multimodal input (new methods not on `BaseEmbeddingProvider`)
- Dimensions are explicitly requested in the API call (not implicit from model name)

**Factory change** (`src/llm/factory.py`): Add `bedrock` as a provider option:

```python
def create_embedding_provider(config):
    if config.provider == "bedrock":
        return BedrockEmbeddingProvider(
            region=config.region,
            model_id=config.model,
            dimensions=config.dimensions,
        )
    elif config.provider == "openai":
        return OpenAIEmbeddingProvider(config)
```

### LLM Provider: BedrockLLMProvider

A new LLM provider for chat/answer generation using Claude on Bedrock.

**Location:** `src/llm/bedrock_provider.py` (same file, separate class)

**Interface contract** (extends existing `BaseLLMProvider`):

```python
class BedrockLLMProvider(BaseLLMProvider):
    """Claude on Amazon Bedrock for chat and answer generation."""

    def __init__(self, region: str, model_id: str, temperature: float, max_tokens: int):
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id  # "anthropic.claude-sonnet-4-20250514-v1:0" or latest
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Synchronous generation."""

    async def generate_stream(self, system_prompt: str, user_prompt: str):
        """Streaming generation for chat responses."""
```

**Factory change** (`src/llm/factory.py`): Add `bedrock` to `create_llm_provider()`.

**Prompt compatibility:** See the dedicated Prompt Optimization section below — this is a significant workstream, not a drop-in swap.

### LLM Prompt Optimization (GPT-4.1 → Claude on Bedrock)

The existing prompts in `src/llm/prompts.py` were tuned over 12 eval iterations against GPT-4.1. Claude handles instructions differently in ways that matter for this pipeline:

**Known behavioral differences:**

| Behavior | GPT-4.1 | Claude |
|----------|---------|--------|
| Citation format adherence | Follows bracket format but sometimes drops page references | Tends to be more literal with format instructions — may actually improve citation correctness |
| Abstention | Can be overconfident — the LLM gate was added specifically to catch this | Claude is generally more conservative — may need to relax abstention thresholds |
| Structured output | Reliable with JSON-like output when prompted | Equally reliable, but may add preamble text before structured sections unless explicitly told not to |
| System prompt weight | Strong adherence | Strong adherence, but handles multi-part system prompts differently — prefers a single coherent block over multiple instructions |

**Prompt files requiring review and potential rework:**

| File | Prompt | Risk |
|------|--------|------|
| `src/llm/prompts.py` → `SYSTEM_PROMPT` | The main RAG system prompt defining answer format, citation rules, abstention behavior | Medium — Claude may interpret "do not answer if unsure" more aggressively |
| `src/llm/prompts.py` → `build_extract_sentences_messages` | Two-pass extraction prompt (extract relevant sentences with citations) | High — this is the most format-sensitive prompt; citation bracket format `[filename|p=X]` must be preserved exactly |
| `src/llm/prompts.py` → `build_compose_from_extracted_messages` | Composition prompt (assemble final answer from extracted sentences) | Medium — Claude may restructure the answer more than GPT-4.1 does |
| `src/retrieval/abstention.py` → `llm_relevance_gate` | The tie-breaker prompt that checks if context is relevant before abstaining | Low — this is a simple yes/no gate; should transfer cleanly |

**Recommended approach:**

1. **Phase 3a — Direct swap test:** Run the 86-question eval with Claude using the existing GPT-4.1 prompts unchanged. This establishes the baseline gap.
2. **Phase 3b — Targeted prompt rework:** Address the biggest regressions first. Likely candidates:
   - Add explicit "do not include any preamble" instruction to extraction prompts
   - Adjust abstention threshold (`abstain_min_top1_score`) if Claude's gate behaves differently
   - Test citation format preservation with Claude-specific examples in the prompt
3. **Phase 3c — Full eval cycle:** Run the complete eval again after prompt adjustments. Target: match or exceed v12 metrics.

**Cost note for Bedrock LLM selection:** Evaluate Claude model tiers on Bedrock based on the quality/cost tradeoff for your use case. Claude Haiku is significantly cheaper for the relevance gate (simple yes/no), while Sonnet is appropriate for answer generation. A split-model approach (Haiku for gate, Sonnet for answers) can reduce LLM costs meaningfully.

### Reranker: Cohere Rerank 3.5 on Bedrock

The current local cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) runs on CPU in both Lambda and App Runner. This works but has limitations:

- **Cold start overhead:** The model loads into memory on first request (~2-4 seconds on Lambda)
- **CPU-bound latency:** Reranking 20 passages takes ~200-400ms on CPU, which is a meaningful fraction of total query latency
- **Package size:** `sentence-transformers` + `torch` add ~500MB to the Docker image, slowing builds and Lambda cold starts
- **No GPU in current compute:** Both App Runner (1 vCPU) and Lambda (1024MB) run CPU inference only

**Cohere Rerank 3.5 on Bedrock replaces all of this:**

- Managed API call via the same Bedrock VPC endpoint — no model to load, no torch dependency
- Supports 100+ languages (relevant for multilingual industrial documentation)
- $2.00 per 1,000 queries (a query can contain up to 100 document chunks)
- Consistently faster than local CPU inference (~50-100ms via Bedrock vs ~200-400ms local)

**Cost estimate:** At 150K queries/month = 150 query-units (each query sends ≤100 chunks) × $0.002 = **$0.30/month**. At the current `rerank_top_n=20` chunks per query, each API call is a single query-unit.

**Implementation:**

Replace `CrossEncoderReranker` with `BedrockReranker`:

```python
class BedrockReranker:
    """Cohere Rerank 3.5 via Amazon Bedrock Rerank API."""

    def __init__(self, region: str, model_id: str = "cohere.rerank-v3-5:0"):
        self._client = boto3.client("bedrock-agent-runtime", region_name=region)
        self._model_id = model_id

    def rerank(
        self,
        query: str,
        passages: list[str],
        top_n: int = 10,
    ) -> list[tuple[int, float]]:
        """Rerank passages, return (original_index, score) sorted by relevance."""
        if not passages or not query.strip():
            return []

        sources = [
            {"inlineDocumentSource": {"textDocument": {"text": p}, "type": "TEXT"}}
            for p in passages
        ]

        response = self._client.rerank(
            queries=[{"type": "TEXT", "textQuery": {"text": query}}],
            sources=sources,
            rerankingConfiguration={
                "bedrockRerankingConfiguration": {
                    "modelConfiguration": {"modelArn": self._model_id},
                    "numberOfResults": top_n,
                }
            },
        )

        results = response.get("results", [])
        return [(r["index"], r["relevanceScore"]) for r in results]
```

**Changes to wiring:**

| File | Change |
|------|--------|
| `src/retrieval/reranker.py` | Add `BedrockReranker` class alongside existing `CrossEncoderReranker` |
| `src/api/deps.py` | Update `get_retrieval_engine()` to instantiate `BedrockReranker` when `reranker_provider=bedrock` |
| `config/settings.yaml` | Add `reranker_provider: bedrock` and `reranker_model: cohere.rerank-v3-5:0` |
| `src/core/config.py` | Add `reranker_provider` and `reranker_model` to `RetrievalConfig` |
| `src/retrieval/engine.py` | No change — the `reranker.rerank()` interface is identical |
| `requirements.txt` | Remove `sentence-transformers` and `torch` (saves ~500MB from Docker image) |

**Abstention threshold impact:** Cohere Rerank 3.5 produces relevance scores on a 0-1 scale (higher = more relevant). The current cross-encoder produces logit scores roughly centered around 0 (negative = irrelevant, positive = relevant). The `abstain_min_top1_score` (currently 0.02) and `abstain_min_margin` (currently 0.01) **must be recalibrated** for the new score distribution. Run `scripts/calibrate_abstention` against the eval set after switching.

**CDK change:** Add `bedrock:Rerank` permission to Lambda and App Runner IAM roles.

### Ingestion Pipeline: Multimodal Document Processing

The ingestion pipeline gains a parallel image extraction path alongside text extraction.

```
CURRENT FLOW:
  PDF → PyMuPDF text extraction → chunk text → embed text → pgvector

NEW FLOW:
  PDF → PyMuPDF text extraction → chunk text ──────────────────────┐
      → PyMuPDF page rendering  → page images (PNG, 150 DPI) ─────┤
                                                                   ▼
                                                   BedrockEmbeddingProvider
                                                   embed_multimodal(text, image)
                                                   per chunk: text + its source page image
                                                                   │
                                                                   ▼
                                                              Aurora pgvector
```

**Implementation details:**

1. **Page rendering:** PyMuPDF (`fitz`) already supports `page.get_pixmap(dpi=150)` to render a page as a PNG. This is a one-line addition per page in `src/ingestion/parsers.py`. 150 DPI balances quality and file size (~200KB per page).

2. **Chunk-to-page mapping:** Each text chunk already tracks which page(s) it came from (parent-child chunker preserves page metadata). The image for a chunk is the rendered page it originated from.

3. **Interleaved embedding:** For each chunk, call `embed_multimodal(chunk_text, page_image_bytes, "image/png")`. Nova processes both modalities together and returns a single 1024-d vector that captures the semantic relationship between the text and its visual context.

4. **Storage:** The embedding vector stores in the same `document_chunks.embedding` column. No schema change beyond the dimension migration. Page images can optionally be stored in S3 for cache/retrieval but are not required in the DB.

5. **Text-only documents** (TXT, MD, CSV): Continue using `embed_text()` — no image path needed.

**Parser registry update** (`src/ingestion/parsers.py`): Each parser function returns a new field alongside text: `page_images: list[bytes | None]` — one image per page (or `None` for non-visual formats).

### Configuration Changes

**`config/settings.yaml` — target state:**

```yaml
llm:
  provider: bedrock
  model: anthropic.claude-sonnet-4-20250514-v1:0
  temperature: 0.1
  max_tokens: 2048
  region: us-east-1

embedding:
  provider: bedrock
  model: amazon.nova-2-multimodal-embeddings-v1:0
  dimensions: 1024          # configurable: 256, 384, 1024, 3072
  region: us-east-1
  multimodal: true           # enable page-image embedding alongside text
  page_render_dpi: 150       # resolution for PDF page renders
```

**`src/core/config.py` — additions to `EmbeddingConfig`:**

```python
@dataclass
class EmbeddingConfig:
    provider: str = "bedrock"
    model: str = "amazon.nova-2-multimodal-embeddings-v1:0"
    dimensions: int = 1024
    region: str = "us-east-1"
    multimodal: bool = True
    page_render_dpi: int = 150
    api_key: str = ""  # unused for Bedrock, retained for OpenAI fallback
```

**Environment variable overrides** (add to `_apply_env_overrides`):

```
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.nova-2-multimodal-embeddings-v1:0
EMBEDDING_DIMENSIONS=1024
EMBEDDING_REGION=us-east-1
LLM_PROVIDER=bedrock
LLM_MODEL=anthropic.claude-sonnet-4-20250514-v1:0
LLM_REGION=us-east-1
```

### Database Schema Migration

**Alembic migration 005: dimension change + embedding version tracking**

```python
"""005_bedrock_embedding_migration.py"""

def upgrade():
    # Update vector column dimension
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024)")

    # Drop and recreate HNSW index with new dimensions
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.execute("""
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)

    # Track active embedding model version
    op.execute("""
        INSERT INTO embedding_versions (model_name, dimensions, is_active)
        VALUES ('amazon.nova-2-multimodal-embeddings-v1:0', 1024, true)
        ON CONFLICT DO NOTHING
    """)

def downgrade():
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.execute("""
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)
```

Since this is a fresh start on production data, run `alembic upgrade head` on the new Aurora instance — no data to re-embed.

### CDK Infrastructure Changes

| Stack | Change |
|-------|--------|
| **VpcStack** | Add `bedrock-runtime` VPC interface endpoint |
| **RdsStack** | Replace `DatabaseInstance` with Aurora `DatabaseCluster` (PostgreSQL 16, pgvector, `db.t4g.medium`) |
| **SecretsStack** | Remove `openai-api-key` secret. Add Bedrock model config as SSM Parameter Store values (not secrets — they're not sensitive) |
| **IngestionStack** | Update Lambda IAM role: add `bedrock:InvokeModel` + `bedrock:Rerank` permissions. Remove NAT dependency for OpenAI (Bedrock goes through VPC endpoint) |
| **AppRunnerStack** | Update IAM role: add `bedrock:InvokeModel` + `bedrock:Rerank` permissions. Remove `OPENAI_API_KEY` env var injection |
| **ObservabilityStack** | Add Bedrock invocation metrics to CloudWatch dashboard (latency, throttling, error rate) |

**IAM policy for Bedrock access** (attached to both Lambda and App Runner roles):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-2-multimodal-embeddings-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "bedrock:Rerank",
      "Resource": "*"
    }
  ]
}
```

### Secrets Cleanup

Moving to Bedrock eliminates the `openai-api-key` secret entirely. Authentication is handled by IAM roles attached to the compute (Lambda execution role, App Runner instance role). No API keys to rotate, no secrets to manage for AI services.

**Remaining secrets** (4 instead of 6):
- `database-url` — Aurora connection string (90-day rotation retained)
- `cors-origins` — allowed CORS origins
- `entra-client-id` — Microsoft Entra ID client ID
- `entra-client-secret` — Microsoft Entra ID client secret
- `entra-tenant-id` — Microsoft Entra ID tenant ID

Note: `entra-tenant-id` is not sensitive — could move to SSM Parameter Store, but low priority.

### Lambda Handler Fixes

The current Lambda handler (`src/lambda_handlers/ingestion_handler.py`) has a known issue: it receives Secrets Manager secret **names** as environment variables, not resolved values. This must be fixed regardless of the Bedrock migration.

**Fix:** Add a secrets resolution layer at handler startup:

```python
import boto3
import json

_secrets_client = boto3.client("secretsmanager")

def _resolve_secret(secret_name: str) -> str:
    response = _secrets_client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]
```

Call this once at cold start to resolve `DATABASE_URL` from the secret name. With Bedrock, the embedding/LLM providers use IAM — no API key secret to resolve.

---

## RAG Tuning Parameter Preservation

The following tuned parameters from `config/settings.yaml` and `docs/rag_tuning_status.md` carry forward unchanged:

| Parameter | Value | Source |
|-----------|-------|--------|
| `vector_top_k` | 40 | Demo preset, validated on 86-question eval |
| `lexical_top_k` | 50 | Demo preset |
| `rrf_k` | 30 | Sweep: 30 = 60 = 90 |
| `final_k` | 25 | Demo preset |
| `ef_search` | 40 | Sweep: 40 = 80 |
| `rerank_top_n` | 20 | Demo preset |
| `final_context_chunks` | 7 | Sweep: 7 > 5 > 3 |
| `abstain_min_top1_score` | 0.02 | Demo preset |
| `abstain_min_margin` | 0.01 | Demo preset |
| `content_type_boost` | 1.3 | Manual tuning |
| `model_number_boost` | 1.3 | Manual tuning |
| `use_llm_gate_on_abstain` | true | v10 gate probe, validated |
| `use_single_pass_fast` | true | Latency optimization |
| `hnsw_m` | 16 | Default, validated |
| `hnsw_ef_construction` | 200 | Default, validated |

**What will need re-tuning after migration:**

| Parameter | Why | Priority |
|-----------|-----|----------|
| `abstain_min_top1_score` | **Must change.** Cohere Rerank 3.5 outputs 0-1 relevance scores vs. the cross-encoder's logit scores centered around 0. The current threshold of 0.02 is meaningless on the new scale. Run `scripts/calibrate_abstention` after switching. | Critical |
| `abstain_min_margin` | Same reason — score distribution is completely different with Cohere Rerank | Critical |
| `chunk_size` / `child_size_words` | Multimodal embeddings may perform differently with shorter or longer chunks — run eval to confirm | Medium |
| `ef_search` | May need adjustment for 1024-d vectors (lower dimensionality can change HNSW search characteristics) | Low |

**Validation plan:** After initial ingestion on Aurora with Nova embeddings, run the full 86-question eval (`scripts/eval_comprehensive.py`) against `eval/datasets/fintek_gold.yaml`. Compare metrics to the v12 baseline:

| Metric | v12 Baseline (target to meet or exceed) |
|--------|----------------------------------------|
| Context Recall | 0.698 |
| Faithfulness | 0.894 |
| Citation Correct | 0.141 |
| Abstention Accuracy | 0.512 |
| Answer Relevance | 0.577 |
| Hallucinations | 0/86 |

---

## Multi-Tenant Scaling Framework

### Current model: shared database (retain)

All tenants share one Aurora instance, isolated by `tenant_id` on every data table. This is the current architecture and scales well to ~50+ tenants before Aurora instance sizing becomes a concern.

**New tenant onboarding flow:**

```
1. INSERT INTO tenants (id, name, slug) VALUES (...)
2. Configure Entra ID app registration for the new company
3. Upload documents to S3: tenants/{tenant_id}/uploads/...
4. S3 event → SQS → Lambda → Nova embeddings → Aurora
5. Done. No new infrastructure.
```

**What makes this work for scaling to new companies:**
- Bedrock is fully managed — no per-tenant compute to provision
- Aurora handles multi-tenant query load with read replicas if needed
- S3 key prefix isolates documents per tenant
- IAM is shared (same App Runner / Lambda roles serve all tenants)
- Each tenant's data is logically isolated but physically co-located

### Path to per-tenant isolation (if required)

Some enterprise customers may require stronger data isolation (regulatory, contractual). The architecture supports escalation:

**Level 1 — Row-level isolation (current):**
- `tenant_id` on all tables, enforced in application code
- PostgreSQL Row-Level Security (RLS) can be added as a defense-in-depth layer

**Level 2 — Schema-per-tenant:**
- Each tenant gets a dedicated PostgreSQL schema within the same Aurora cluster
- Connection routing by tenant: `SET search_path = tenant_{id}`
- Same Aurora instance, stronger isolation, minimal cost increase

**Level 3 — Database-per-tenant:**
- Separate Aurora cluster per customer
- Requires CDK stack parameterization: `RdsStack(tenant_id=...)` creates a dedicated cluster
- Higher cost (~$50+/month per cluster minimum), but full isolation
- Recommended only for customers with explicit contractual requirements

### CDK template reusability

The CDK stacks are already parameterized by environment (`dev`/`prod`). To scale to a new company:

1. Add a new entry in `stacks/config.py` with the company's account ID, naming prefix, and domain
2. Instantiate the same stack set with the new config
3. Deploy via `cdk deploy --context env=new-company-prod`

The VPC CIDR allocation table in `FIN-TEK_ARCHITECTURE.md` already reserves space for additional workloads (`10.3.0.0/16` available).

---

## Implementation Order

### Phase 1: Infrastructure (no application changes)

| Task | Priority | Effort |
|------|----------|--------|
| Add `bedrock-runtime` VPC endpoint to `VpcStack` | High | Small |
| Replace RDS with Aurora PostgreSQL in `RdsStack` | High | Medium |
| Update Lambda and App Runner IAM roles for Bedrock access | High | Small |
| Remove `openai-api-key` from `SecretsStack` | Medium | Small |
| Fix Lambda handler secrets resolution | High | Small |
| Fix Dockerfile build path in `deploy-dev.yml` | High | Small |
| Add `boto3` to `requirements.txt` | High | Small |

### Phase 2: Embedding Provider + Reranker

| Task | Priority | Effort |
|------|----------|--------|
| Implement `BedrockEmbeddingProvider` in `src/llm/bedrock_provider.py` | High | Medium |
| Add `embed_image` and `embed_multimodal` to `BaseEmbeddingProvider` | High | Small |
| Update `factory.py` to support `bedrock` provider | High | Small |
| Update `EmbeddingConfig` with `region`, `multimodal`, `page_render_dpi` | High | Small |
| Update `settings.yaml` defaults | High | Small |
| Add page rendering to PDF parser (`src/ingestion/parsers.py`) | High | Medium |
| Update `IngestionPipeline` to pass images alongside text chunks | High | Medium |
| Create Alembic migration 005 (vector dimension change) | High | Small |
| Implement `BedrockReranker` in `src/retrieval/reranker.py` | High | Medium |
| Update `deps.py` to instantiate `BedrockReranker` when `reranker_provider=bedrock` | High | Small |
| Add `reranker_provider` and `reranker_model` to config | High | Small |
| Remove `sentence-transformers` and `torch` from `requirements.txt` | Medium | Small |

### Phase 3: LLM Provider + Prompt Optimization

| Task | Priority | Effort |
|------|----------|--------|
| Implement `BedrockLLMProvider` in `src/llm/bedrock_provider.py` | High | Medium |
| Support streaming via Bedrock `invoke_model_with_response_stream` | High | Medium |
| Update `factory.py` to support `bedrock` LLM provider | High | Small |
| Update `LLMConfig` with `region` | High | Small |
| **Phase 3a:** Run 86-question eval with Claude using existing GPT-4.1 prompts unchanged — establish baseline gap | High | Medium |
| **Phase 3b:** Targeted prompt rework based on eval regressions (citation format, abstention preamble, extraction prompts) | High | Medium-Large |
| **Phase 3c:** Full eval cycle after prompt adjustments — target v12 parity | High | Medium |
| Evaluate split-model approach: Haiku for relevance gate, Sonnet for answers | Medium | Small |

### Phase 4: Validation + Eval Framework Update

| Task | Priority | Effort |
|------|----------|--------|
| Update `scripts/eval_comprehensive.py` to use Bedrock providers (embedding + LLM) instead of OpenAI | High | Medium |
| Update any eval helper scripts that call OpenAI directly (`scripts/calibrate_abstention`, `scripts/sweep_retrieval`, etc.) | High | Small |
| Deploy Aurora, run `alembic upgrade head` | High | Small |
| Ingest production dataset with Nova multimodal embeddings (use batch inference — see below) | High | Medium |
| Run 86-question eval on new stack, compare to v12 baseline | High | Medium |
| **Recalibrate abstention thresholds** for Cohere Rerank 3.5 score distribution (0-1 scale) | Critical | Medium |
| Run eval with Claude answers, compare to GPT-4.1 baseline | High | Medium |
| Load test: 150K queries/month simulation | Medium | Medium |

### Phase 5: Cleanup and Hardening

| Task | Priority | Effort |
|------|----------|--------|
| Remove `OpenAIEmbeddingProvider` and OpenAI LLM code (or keep as fallback) | Low | Small |
| Remove `sentence-transformers` / `torch` from Docker image if not done in Phase 2 | Medium | Small |
| Update CI/CD: remove OpenAI API key from GitHub secrets | Medium | Small |
| Add Bedrock metrics to CloudWatch dashboard | Medium | Small |
| Document runbook for new tenant onboarding | Medium | Small |
| Update `FIN-TEK_ARCHITECTURE.md` with final architecture | Medium | Medium |

---

## Batch Inference Workflow (Initial Production Data Load)

The production dataset will be pre-processed and loaded in batch rather than streaming through the real-time SQS → Lambda pipeline. This is more cost-effective and avoids rate-limit concerns during the initial bulk load.

### Workflow

```
STEP 1: Pre-process documents locally or on an EC2 instance
─────────────────────────────────────────────────────────────
  For each document:
    ├─ Parse text (PyMuPDF / python-docx / etc.)
    ├─ Chunk text (parent-child or flat, using existing IngestionPipeline logic)
    ├─ Render page images (PyMuPDF, 150 DPI PNG)
    └─ Write chunks + images to staging S3 bucket

  Output structure in S3:
    s3://industrial-{env}-staging/
      └─ batch-{timestamp}/
          ├─ manifest.jsonl          ← Bedrock batch input
          ├─ images/
          │   ├─ chunk-0001.png
          │   ├─ chunk-0002.png
          │   └─ ...
          └─ metadata/
              └─ chunk-mapping.json  ← maps recordId → document_id, tenant_id, page, text
```

### Step 1: Generate JSONL manifest

A script processes all pre-chunked documents into Bedrock's batch input format:

```python
# Each line in manifest.jsonl:
{
    "recordId": "chunk-0001",
    "modelInput": {
        "inputText": "chunk text content here...",
        "inputImage": {
            "s3Uri": "s3://industrial-{env}-staging/batch-{timestamp}/images/chunk-0001.png"
        },
        "embeddingConfig": {
            "outputEmbeddingLength": 1024
        }
    }
}
```

For text-only chunks (TXT, MD, CSV sources), omit the `inputImage` field.

### Step 2: Submit Bedrock batch job

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")

response = bedrock.create_model_invocation_job(
    jobName=f"initial-embed-{timestamp}",
    modelId="amazon.nova-2-multimodal-embeddings-v1:0",
    roleArn="arn:aws:iam::{account}:role/industrial-{env}-bedrock-batch-role",
    inputDataConfig={
        "s3InputDataConfig": {
            "s3Uri": f"s3://industrial-{env}-staging/batch-{timestamp}/",
            "s3InputFormat": "JSONL",
        }
    },
    outputDataConfig={
        "s3OutputDataConfig": {
            "s3Uri": f"s3://industrial-{env}-staging/batch-{timestamp}/output/",
        }
    },
)

job_arn = response["jobArn"]
```

### Step 3: Monitor and poll

```python
while True:
    status = bedrock.get_model_invocation_job(jobIdentifier=job_arn)
    state = status["status"]  # "InProgress", "Completed", "Failed", etc.
    if state in ("Completed", "Failed", "Stopped"):
        break
    time.sleep(60)
```

Bedrock writes a `manifest.json.out` summary to the output S3 path with counts of processed/failed records.

### Step 4: Load vectors into Aurora

```python
# Read output JSONL from S3 (each line has recordId + embedding vector)
# Cross-reference with chunk-mapping.json for metadata
# Bulk INSERT into document_chunks using SQLAlchemy or psycopg2 COPY

for record in output_records:
    chunk_meta = chunk_mapping[record["recordId"]]
    insert_chunk(
        tenant_id=chunk_meta["tenant_id"],
        document_id=chunk_meta["document_id"],
        text=chunk_meta["text"],
        embedding=record["modelOutput"]["embedding"],
        page=chunk_meta["page"],
        # ... other metadata
    )
```

Use `psycopg2.extras.execute_values` or Aurora's optimized COPY for bulk loading — Aurora pgvector supports up to 67× faster vector loading vs standard PostgreSQL.

### Step 5: Upload source documents to production S3

After vectors are loaded, upload the original documents to the production S3 bucket under the standard key convention:

```
s3://industrial-{env}-documents-{accountId}/tenants/{tenant_id}/uploads/{document_id}/{filename}
```

Create corresponding `documents` and `ingestion_jobs` rows with status `completed`.

### Batch script location

Create `scripts/batch_embed.py` — a standalone script that handles steps 1-4. It reuses the existing `IngestionPipeline` parsing and chunking logic but writes to S3/Bedrock batch instead of calling the embedding provider synchronously.

### Cost advantage

Bedrock batch inference is priced at approximately 50% of synchronous pricing. For a 100K-page initial load:
- Synchronous: ~$16.75 (text) + ~$10.00 (images) = ~$26.75
- Batch: ~$8.38 (text) + ~$5.00 (images) = **~$13.38**

---

## Cost Comparison: Current vs Target (Dev Environment)

| Resource | Current Monthly | Target Monthly |
|----------|----------------|----------------|
| NAT Gateway | ~$32 | ~$32 (retained for other outbound, but Bedrock traffic bypasses it) |
| RDS `db.t4g.micro` (Multi-AZ) | ~$24 | — (replaced by Aurora) |
| Aurora `db.t4g.medium` (single instance, dev) | — | ~$47 |
| Bedrock VPC Endpoint (2 AZs) | — | ~$14 |
| App Runner (1 idle instance) | ~$5 | ~$5 |
| Secrets Manager (6 → 5 secrets) | ~$2.40 | ~$2.00 |
| Bedrock Nova embeddings (dev volume) | — | <$1 |
| Bedrock Claude (dev volume) | — | ~$5 |
| Bedrock Cohere Rerank (dev volume) | — | <$1 |
| OpenAI API | ~$5 | $0 |
| S3 + SQS + Lambda | <$2 | <$2 |
| CloudWatch | ~$3 | ~$3 |
| Route53 | ~$1 | ~$1 |
| Amplify | ~$0 | ~$0 |
| **Total** | **~$75/month** | **~$112/month** |

The ~$37/month increase comes primarily from Aurora being larger than `db.t4g.micro` and the VPC endpoint. This is a dev environment cost; in production with real query volume, the elimination of OpenAI API costs offsets the increase. Aurora can start as `db.t4g.small` (~$29/month) for dev if cost is a concern.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Nova embedding quality doesn't match OpenAI on industrial text | Retrieval degradation | Run 86-question eval before cutover; keep OpenAI provider as fallback |
| Claude prompt behavior differs from GPT-4.1 | Answer quality regression | Follow the phased prompt optimization approach (3a/3b/3c); budget time for prompt rework, not just testing |
| Cohere Rerank score distribution breaks abstention logic | False abstains or missed abstains | **Critical:** Recalibrate abstention thresholds immediately after reranker swap. Scores change from logit-centered (around 0) to 0-1 relevance scale |
| Aurora migration causes downtime | Service interruption | Fresh start on production data — no live migration needed |
| Bedrock rate limits during bulk ingestion | Slow initial load | Use Bedrock batch inference for initial dataset; switch to sync for real-time |
| Nova multimodal image embedding adds latency to ingestion | Slower document processing | Page images are ~200KB at 150 DPI; Nova processes these in <500ms per chunk |
| VPC endpoint adds cost without proportional NAT savings | Wasted spend | Monitor NAT data processing charges; endpoint pays for itself above ~300GB/month of Bedrock traffic |
| Eval framework still calls OpenAI after migration | Cannot validate new stack | Update eval scripts to use Bedrock providers before running Phase 4 validation |
| Removing torch/sentence-transformers breaks other functionality | Build failure | Audit all imports of these packages before removal; the only consumer is `CrossEncoderReranker` |
