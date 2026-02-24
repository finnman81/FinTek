# Anchorpoint: Hosting & Mobile-Readiness Plan

## Current State Summary

| Layer | Technology | Status |
|-------|-----------|--------|
| **Frontend** | Next.js 14, React 18, Tailwind, Clerk auth | Built, needs mobile work |
| **Backend API** | FastAPI (Python 3.11), uvicorn | Built, running |
| **Background Workers** | Python ingestion worker, Postgres job queue | Built |
| **Database** | PostgreSQL 15 + pgvector extension | Built, multi-tenant |
| **Object Storage** | Local filesystem (S3 planned) | Needs migration |
| **LLM/Embeddings** | OpenAI (gpt-4.1-mini, text-embedding-3-small) | Working |
| **Infrastructure** | Terraform configs (ECS, RDS, S3, ALB, VPC) | Scaffolded, not deployed |
| **Mobile readiness** | Tailwind exists, no responsive breakpoints, no PWA | ~4/10 |

---

## Part 1: AWS Hosting Architecture

### Architecture Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │              Route 53 (DNS)                  │
                    │   app.anchorpoint.ai / api.anchorpoint.ai    │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────────────┐
                    │         CloudFront (CDN + WAF)               │
                    │   - HTTPS termination                        │
                    │   - Static asset caching                     │
                    │   - Geographic distribution                  │
                    │   - WAF rules (rate limiting, bot protection)│
                    └──────┬──────────────────┬────────────────────┘
                           │                  │
              ┌────────────▼──────┐   ┌───────▼──────────────────┐
              │   S3 (Frontend)   │   │   ALB (API + Workers)    │
              │   Next.js static  │   │   /api/v1/* routing      │
              │   export OR       │   │   health checks          │
              │   Amplify Hosting │   │   HTTPS listener         │
              └───────────────────┘   └───────┬──────────────────┘
                                              │
                              ┌────────────────┼────────────────┐
                              │                │                │
                    ┌─────────▼──┐   ┌─────────▼──┐   ┌────────▼───────┐
                    │ ECS Fargate│   │ ECS Fargate│   │  ECS Fargate   │
                    │ API Service│   │ API Service│   │  Worker Service│
                    │ (auto-     │   │ (auto-     │   │  (ingestion)   │
                    │  scaled)   │   │  scaled)   │   │                │
                    └─────┬──┬──┘   └──┬──┬──────┘   └────┬───────────┘
                          │  │         │  │                │
              ┌───────────▼──▼─────────▼──▼────────────────▼──────────┐
              │                    Private Subnets                     │
              │  ┌─────────────────┐  ┌────────────────────────────┐  │
              │  │  RDS PostgreSQL  │  │  S3 (Document Storage)    │  │
              │  │  + pgvector      │  │  - Per-tenant prefixes    │  │
              │  │  - Multi-tenant  │  │  - Lifecycle policies     │  │
              │  │  - Automated     │  │  - Server-side encryption │  │
              │  │    backups       │  │                            │  │
              │  └─────────────────┘  └────────────────────────────┘  │
              │                                                        │
              │  ┌─────────────────┐  ┌────────────────────────────┐  │
              │  │ Secrets Manager  │  │  CloudWatch               │  │
              │  │ - DB credentials │  │  - Logs, metrics, alarms  │  │
              │  │ - OpenAI key     │  │  - Per-tenant dashboards  │  │
              │  │ - Clerk secrets  │  │                            │  │
              │  └─────────────────┘  └────────────────────────────┘  │
              └────────────────────────────────────────────────────────┘
```

### Recommended Approach: Two Options for Frontend

**Option A: AWS Amplify Hosting (recommended)**
- Managed hosting for Next.js with SSR support
- Automatic builds from GitHub pushes
- Built-in custom domains, SSL, CDN (CloudFront under the hood)
- Stays 100% within AWS -- single bill, single console
- Preview deployments for PRs
- ~$0-15/month at low traffic

**Option B: Vercel**
- Best-in-class Next.js hosting (made by the same team)
- Zero-config deploys, edge functions, analytics
- Adds a second vendor outside AWS
- Free tier generous, Pro is $20/month
- Slightly better DX but adds vendor split

**Recommendation**: Start with **Amplify Hosting**. It keeps everything in AWS, and for your use case (internal tool used by 5-30 techs per customer) the traffic volume doesn't need Vercel's edge network. If you later find Amplify limiting, migrating to Vercel is straightforward since it's standard Next.js.

### Backend: ECS Fargate (already scaffolded)

Your existing Terraform already defines the right structure. Key additions needed:

| Component | Phase 0 (1-3 customers) | Phase 1 (5-10 customers) |
|-----------|------------------------|--------------------------|
| **ECS API** | 1 task, 0.5 vCPU / 1 GB | 2-4 tasks, auto-scaled |
| **ECS Worker** | 1 task (same cluster) | Separate service, auto-scaled |
| **RDS** | db.t3.small, single-AZ | db.t3.medium, multi-AZ |
| **S3** | Single bucket, tenant prefixes | Same, add lifecycle rules |
| **ALB** | 1 ALB, path-based routing | Same ALB |
| **CloudWatch** | Basic logs + alarms | Custom dashboards per tenant |

### Multi-Tenant Organization Strategy

Your database already has `tenant_id` logical isolation. For AWS resource organization at scale:

```
S3 bucket structure:
  anchorpoint-documents-{env}/
    ├── tenant_{uuid_1}/
    │   ├── uploads/
    │   └── processed/
    ├── tenant_{uuid_2}/
    │   ├── uploads/
    │   └── processed/
    └── ...

CloudWatch log structure:
  /ecs/anchorpoint/api      → all API logs (filter by tenant_id in structured logs)
  /ecs/anchorpoint/worker   → all worker logs

Secrets Manager:
  anchorpoint/shared/openai-api-key     → shared across tenants
  anchorpoint/shared/database-url       → shared DB
  anchorpoint/shared/clerk-secret-key   → shared auth
```

For the foreseeable future (up to ~50 tenants), **logical isolation** (single DB, `tenant_id` column) is the right call. Schema-per-tenant or DB-per-tenant only makes sense when you have enterprise customers demanding it.

### CI/CD Pipeline

```
GitHub (main branch)
    │
    ├─► GitHub Actions: Test
    │     - pytest (backend)
    │     - playwright (frontend)
    │
    ├─► GitHub Actions: Deploy Backend
    │     - Build Docker image
    │     - Push to ECR
    │     - Update ECS service (rolling deploy)
    │
    └─► Amplify Hosting: Deploy Frontend
          - Auto-triggered on push
          - Build Next.js
          - Deploy to CDN
```

### Environments

| Environment | Purpose | Infra |
|-------------|---------|-------|
| **dev** | Local development | Docker Compose (Postgres + app) |
| **staging** | Pre-prod testing, customer demos | Amplify preview + minimal ECS/RDS |
| **production** | Live customers | Full ECS/RDS/S3/CloudWatch |

For staging, you can use Terraform workspaces or a separate `tfvars` file to deploy a smaller, cheaper copy of the same infrastructure.

### Cost Estimate (Phase 0)

| Service | Config | Monthly Cost |
|---------|--------|-------------|
| ECS Fargate (API) | 1 task, 0.5 vCPU, 1 GB | ~$18 |
| ECS Fargate (Worker) | 1 task, 0.25 vCPU, 0.5 GB | ~$9 |
| RDS PostgreSQL | db.t3.small, single-AZ, 20 GB | ~$15 |
| ALB | Fixed + LCU | ~$20 |
| S3 | <100 GB | ~$3 |
| CloudWatch | Logs + basic metrics | ~$5 |
| Amplify Hosting | Low traffic | ~$5 |
| Secrets Manager | 3-4 secrets | ~$2 |
| Route 53 | 1 hosted zone | ~$1 |
| ECR | Image storage | ~$1 |
| **Total** | | **~$79/month** |

At $1,500+ MRR per customer, this is well under 5% of revenue even with a single customer.

---

## Part 2: Mobile Readiness for Field Use

Your target users are **field technicians** using phones on job sites. This is the most critical UX surface. The current frontend needs work in three areas:

### Priority 1: Responsive Layout Fixes

These are the immediate changes to make the existing pages work well on phones:

**Root Layout / Navigation**
- Add mobile hamburger menu (the current nav bar doesn't collapse)
- Add proper viewport meta tag
- Make navigation touch-friendly (44px+ tap targets)

**Chat Page (primary field interface)**
- Make message bubbles responsive (`ml-0 sm:ml-8`)
- Full-width input on mobile
- Larger send button for gloved/dirty hands
- Auto-scroll to latest message
- Consider voice input button (Web Speech API)

**Upload Page**
- Full-width file picker on mobile
- Large drag-drop zone that works with mobile file selection
- Clear status indicators (techs may have poor connectivity)

**Admin Page**
- `grid-cols-1` on mobile, `grid-cols-2` on tablet+
- Scrollable data tables

### Priority 2: Progressive Web App (PWA)

A PWA gives field techs an "app-like" experience without going through an app store:

**What it provides:**
- "Add to Home Screen" prompt on iOS/Android
- Full-screen mode (no browser chrome)
- App icon on home screen
- Offline fallback page ("No connection - try again")
- Push notifications (future: job alerts)
- Faster loading via service worker caching

**Implementation (using `next-pwa` or `@serwist/next`):**

```
web/
├── public/
│   ├── manifest.json          ← App manifest
│   ├── icons/
│   │   ├── icon-192x192.png   ← Home screen icon
│   │   ├── icon-512x512.png   ← Splash screen icon
│   │   └── apple-touch-icon.png
│   └── offline.html           ← Offline fallback
├── next.config.mjs            ← PWA plugin config
└── src/
    └── app/
        └── layout.tsx         ← Manifest link + theme-color meta
```

**manifest.json example:**
```json
{
  "name": "Anchorpoint",
  "short_name": "Anchorpoint",
  "description": "Field knowledge at your fingertips",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#0ea5e9",
  "icons": [
    { "src": "/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Priority 3: Field-Specific UX Enhancements

These are features that matter specifically for technicians in the field:

| Feature | Why It Matters | Complexity |
|---------|---------------|------------|
| **Offline fallback** | Job sites have spotty cell service | Low (service worker) |
| **Answer caching** | Re-access previous answers without network | Medium |
| **Large touch targets** | Gloves, dirty hands, bright sunlight | Low (CSS) |
| **High-contrast mode** | Outdoor readability | Low (Tailwind dark mode) |
| **Copy-to-clipboard** | Quickly grab part numbers, specs | Low |
| **Image support in chat** | Take a photo of a nameplate, ask about it | Medium (future) |
| **Voice input** | Hands-free querying | Medium (Web Speech API) |
| **Recent queries** | Quick access to past lookups | Low |

### Mobile Testing Strategy

Add mobile device emulation to your Playwright E2E tests:

```typescript
// playwright.config.ts
projects: [
  { name: 'Desktop Chrome', use: { ...devices['Desktop Chrome'] } },
  { name: 'Mobile iPhone', use: { ...devices['iPhone 14'] } },
  { name: 'Mobile Android', use: { ...devices['Pixel 7'] } },
]
```

---

## Part 3: Implementation Roadmap

### Phase 0: Deploy MVP (Week 1-2)

| Task | Details |
|------|---------|
| **Docker Compose for local dev** | Postgres + pgvector + API + worker + frontend |
| **ECR repository** | Create in AWS, push first image |
| **Terraform apply** | Deploy VPC, RDS, ECS, ALB, S3 |
| **Amplify Hosting setup** | Connect GitHub repo, configure build |
| **DNS + SSL** | Route 53 hosted zone, ACM certificate |
| **Secrets Manager** | Populate DATABASE_URL, OPENAI_API_KEY, CLERK keys |
| **Smoke test** | Upload doc, ask question, verify end-to-end |

### Phase 1: Mobile Ready (Week 3-4)

| Task | Details |
|------|---------|
| **Viewport + responsive nav** | Hamburger menu, meta tags |
| **Chat page responsive** | Touch-friendly, full-width on mobile |
| **PWA setup** | manifest.json, service worker, icons, offline page |
| **Upload page responsive** | Mobile file picker, status indicators |
| **Admin page responsive** | Single-column grid on mobile |
| **Mobile Playwright tests** | iPhone + Android device emulation |

### Phase 2: Production Hardening (Week 5-6)

| Task | Details |
|------|---------|
| **CI/CD pipeline** | GitHub Actions: test → build → push → deploy |
| **CloudWatch alarms** | CPU, memory, error rate, latency |
| **RDS automated backups** | Daily snapshots, 7-day retention |
| **WAF rules on ALB** | Rate limiting, SQL injection protection |
| **Staging environment** | Separate Terraform workspace |
| **Load testing** | k6 or Locust against staging |

### Phase 3: Multi-Customer Scale (Month 2-3)

| Task | Details |
|------|---------|
| **Tenant onboarding script** | Create tenant, user, S3 prefix, usage limits |
| **Per-tenant usage dashboards** | CloudWatch or admin page |
| **ECS auto-scaling** | CPU/memory target tracking policies |
| **Custom domain per tenant** (optional) | `{tenant}.anchorpoint.ai` via Route 53 |
| **Billing integration** | Stripe, tied to usage_logs |

---

## Key Decisions Summary

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Frontend hosting | AWS Amplify | Single vendor, managed Next.js, auto-deploy |
| Backend hosting | ECS Fargate | Already scaffolded, serverless containers, auto-scaling |
| Database | RDS PostgreSQL + pgvector | Already built, proven, single-AZ to start |
| CDN | CloudFront (via Amplify) | Automatic with Amplify, add separately for API later |
| Container registry | ECR | Native to ECS, no cross-vendor auth |
| CI/CD | GitHub Actions | Already have test workflow, extend to deploy |
| Secrets | AWS Secrets Manager | Already in Terraform, native ECS integration |
| Monitoring | CloudWatch | Built-in, sufficient for Phase 0-1 |
| Mobile strategy | Responsive CSS + PWA | No app store needed, instant updates, works offline |
| Multi-tenant isolation | Logical (tenant_id column) | Sufficient up to ~50 tenants, simple to manage |
| IaC | Terraform | Already written, version-controlled, reproducible |

---

## What You Already Have vs. What's Needed

```
✅ Already built / scaffolded:
   - FastAPI backend with multi-tenant routes
   - PostgreSQL schema with tenant isolation
   - pgvector integration
   - Background ingestion worker
   - Next.js frontend (pages, auth scaffold)
   - Terraform configs (VPC, ECS, RDS, S3, ALB)
   - Dockerfile for API
   - GitHub Actions test workflow

🔧 Needs work:
   - Frontend responsive/mobile CSS (Priority 1)
   - PWA configuration (Priority 2)
   - ECR repo + first image push
   - Terraform: add Amplify, ECR, worker task definition
   - CI/CD deploy workflow (GitHub Actions)
   - Secrets Manager population
   - DNS + SSL setup
   - Docker Compose for local dev
   - Tenant onboarding automation
```
