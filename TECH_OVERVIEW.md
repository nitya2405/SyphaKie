# SyphaKie — Technical Overview

> Developer reference for architecture, data models, API contracts, configuration, and extension points.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Layout](#2-repository-layout)
3. [Environment & Configuration](#3-environment--configuration)
4. [Database Schema](#4-database-schema)
5. [Alembic Migrations](#5-alembic-migrations)
6. [API Reference](#6-api-reference)
7. [Generation Service & Provider Routing](#7-generation-service--provider-routing)
8. [Credit & Billing System](#8-credit--billing-system)
9. [Prompt Cache](#9-prompt-cache)
10. [Async Jobs & Batch Processing](#10-async-jobs--batch-processing)
11. [Webhook System](#11-webhook-system)
12. [Notification System](#12-notification-system)
13. [Authentication & API Keys](#13-authentication--api-keys)
14. [OpenAI Compatibility Proxy](#14-openai-compatibility-proxy)
15. [Telegram Bot](#15-telegram-bot)
16. [Organizations & RBAC](#16-organizations--rbac)
17. [Frontend Architecture](#17-frontend-architecture)
18. [Running Locally](#18-running-locally)
19. [Adding a New Provider](#19-adding-a-new-provider)
20. [Security Notes](#20-security-notes)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Next.js 15 Frontend                  │
│    App Router  ·  Tailwind CSS  ·  localStorage auth     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (X-API-Key)
                         ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend  (Python 3.12)             │
│                                                          │
│  /api/v1/*  ──►  Route handlers (app/api/*.py)          │
│                         │                                │
│               GenerationService                          │
│          ┌──────────────┴──────────────┐                 │
│          │    Provider adapters        │                 │
│   OpenAI │ Anthropic │ Google │ FAL …  │                 │
│          └─────────────────────────────┘                 │
│                         │                                │
│  SQLAlchemy ORM  ──►  PostgreSQL                         │
│  Alembic migrations                                      │
│  Local file storage  (OUTPUT_DIR)                        │
└─────────────────────────────────────────────────────────┘
                         │
           ┌─────────────┴──────────────┐
           │  External services          │
           │  Stripe · Telegram · FAL    │
           └─────────────────────────────┘
```

**Backend:** FastAPI with async route handlers. All database work uses SQLAlchemy 2 (ORM style with `Session`). Async generation and batch jobs run as FastAPI `BackgroundTasks`.

**Frontend:** Next.js 15 App Router. All pages are client components (`"use client"`). Auth state lives in `localStorage` (`syphakie_api_key`). Every API call adds `X-API-Key: <stored_key>`.

**Database:** PostgreSQL. Schema managed entirely by Alembic.

**File storage:** Generated outputs (images, audio, video) are saved to `OUTPUT_DIR` on disk. `BASE_URL` is prepended to build public URLs. In production, replace this with S3 or equivalent.

---

## 2. Repository Layout

```
syphakie/
├── app/                       # FastAPI application
│   ├── main.py                # App factory, CORS, router mounts
│   ├── config.py              # Pydantic Settings (reads .env)
│   ├── api/
│   │   ├── deps.py            # Shared FastAPI dependencies
│   │   ├── auth.py            # Signup, login, key management
│   │   ├── generate.py        # POST /generate + batch
│   │   ├── jobs.py            # Job status polling
│   │   ├── billing.py         # Stripe, credit packs, auto top-up
│   │   ├── credits.py         # Balance, admin adjustments
│   │   ├── usage.py           # Analytics, request history
│   │   ├── cache.py           # Prompt cache analytics
│   │   ├── models.py          # Model registry queries
│   │   ├── webhooks.py        # Webhook CRUD + delivery
│   │   ├── notifications.py   # In-app notifications
│   │   ├── templates.py       # Prompt templates
│   │   ├── pipelines.py       # Multi-step pipeline runs
│   │   ├── finetune.py        # Fine-tuning jobs
│   │   ├── experiments.py     # A/B experiments
│   │   ├── favorites.py       # Saved generations
│   │   ├── outputs.py         # File upload / retrieval
│   │   ├── leaderboard.py     # Community model ratings
│   │   ├── orgs.py            # Organisations, memberships
│   │   ├── admin.py           # Admin-only model management
│   │   └── proxy.py           # OpenAI-compatible proxy
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py        # Re-exports all models (required for Alembic)
│   │   ├── user.py
│   │   ├── api_key.py
│   │   ├── credit.py
│   │   ├── credit_transaction.py
│   │   ├── job.py
│   │   ├── batch.py
│   │   ├── request_record.py
│   │   ├── prompt_cache.py
│   │   ├── notification.py
│   │   ├── webhook.py
│   │   ├── pipeline.py
│   │   ├── prompt_template.py
│   │   ├── favorite.py
│   │   ├── finetune_job.py
│   │   ├── ab_experiment.py
│   │   ├── model_registry.py
│   │   ├── model_rating.py
│   │   ├── organization.py
│   │   ├── org_membership.py
│   │   ├── audit_log.py
│   │   ├── telegram_connection.py
│   │   └── telegram_auth_token.py
│   ├── schemas/               # Pydantic request/response models
│   │   └── generate.py        # GenerateRequest, GenerateResponse
│   ├── services/
│   │   └── generate.py        # GenerationService — core routing logic
│   └── db/
│       ├── session.py         # SessionLocal, engine
│       └── migrations/        # Alembic env + version files
│           ├── env.py
│           └── versions/
├── frontend/                  # Next.js application
│   ├── app/                   # App Router pages
│   ├── components/
│   │   └── SidebarLayout.tsx  # Persistent shell (nav, credits, notifs)
│   ├── lib/
│   │   ├── api.ts             # apiFetch wrapper + typed API calls
│   │   └── auth.ts            # localStorage key helpers
│   ├── .env.example
│   └── package.json
├── .env.example               # Backend env template
├── USER_MANUAL.md             # End-user documentation
├── TECH_OVERVIEW.md           # This file
└── README.md                  # Quick start
```

---

## 3. Environment & Configuration

Backend configuration is loaded by `app/config.py` using Pydantic `BaseSettings`. All values can be overridden by environment variables or a `.env` file in the repo root.

### Backend (`/.env`)

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql://postgres:...@localhost:5432/syphakie` | SQLAlchemy async-compatible URL |
| `OUTPUT_DIR` | `outputs` | Relative path for saved files |
| `BASE_URL` | `http://localhost:8000` | Prepended to output file URLs |
| `DEFAULT_CREDITS` | `1000` | Credits granted on new user signup |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `STRIPE_SECRET_KEY` | `""` | Leave blank to disable billing |
| `STRIPE_WEBHOOK_SECRET` | `""` | Stripe webhook signature secret |
| `OPENAI_API_KEY` | `""` | Auto-skipped if blank |
| `ANTHROPIC_API_KEY` | `""` | |
| `GOOGLE_API_KEY` | `""` | |
| `XAI_API_KEY` | `""` | |
| `QWEN_API_KEY` | `""` | |
| `FAL_API_KEY` | `""` | Covers Kling, Luma, Hailuo, Runway, etc. |
| `STABILITY_API_KEY` | `""` | Stability AI / SDXL |
| `ELEVENLABS_API_KEY` | `""` | TTS and audio |
| `TELEGRAM_BOT_TOKEN` | `""` | Required to enable Telegram bot |
| `TELEGRAM_BOT_USERNAME` | `""` | Without `@` |
| `TELEGRAM_WEBHOOK_URL` | `""` | Blank = long-polling (dev mode) |
| `TELEGRAM_WEBHOOK_SECRET` | `""` | Optional HMAC secret |

CORS middleware reads `ALLOWED_ORIGINS`, splits on comma, and trims whitespace:

```python
# app/main.py
allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, ...)
```

### Frontend (`/frontend/.env.local`)

| Variable | Default | Notes |
|----------|---------|-------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## 4. Database Schema

All models live in `app/models/`. The sections below document every table and column.

### users

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | String UNIQUE | |
| name | String | |
| phone_number | String | |
| password_hash | String NULL | bcrypt |
| role | String | `user` \| `admin` \| `reseller` |
| is_active | Boolean | default true |
| stripe_customer_id | String NULL | |
| stripe_payment_method_id | String NULL | saved for off-session charges |
| org_id | UUID FK→users NULL | currently-active org |
| created_at | DateTime | |
| updated_at | DateTime | |

### api_keys

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| key_hash | String UNIQUE | SHA-256 of full key — used for lookup |
| key_prefix | String | first 8 chars — safe to display |
| key_value | String NULL | full plaintext — returned once at creation |
| label / name | String | user-visible label |
| is_active | Boolean | |
| last_used | DateTime NULL | |
| expires_at | DateTime NULL | |
| scope | String NULL | `null` = all; or `text`, `image`, etc. |
| monthly_credit_limit | Integer NULL | |
| credits_used_this_month | Integer | reset manually or on month rollover |
| created_at | DateTime | |

### credits

One row per user.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK UNIQUE | |
| balance | Integer | default 1000 |
| auto_topup_threshold | Integer NULL | trigger balance |
| auto_topup_amount | Integer NULL | must match a pack size |
| updated_at | DateTime | |

### credit_transactions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| amount | Integer | positive = topup, negative = usage |
| type | String | `topup` \| `usage` \| `refund` \| `adjustment` \| `auto_topup` |
| stripe_payment_intent | String NULL | |
| description | String | |
| balance_after | Integer | balance snapshot |
| created_at | DateTime | |

### jobs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID indexed | |
| batch_id | UUID FK→batches NULL | |
| prompt | Text NULL | |
| status | String | `queued` \| `running` \| `success` \| `failed` |
| modality | String | |
| model_id | String NULL | |
| provider | String NULL | |
| input_payload | JSON | full GenerateRequest dict |
| output_url | Text NULL | |
| output_content | Text NULL | |
| error_message | Text NULL | |
| credits_used | Integer NULL | |
| request_id | String NULL | links to request_records |
| created_at / started_at / completed_at | DateTime | |

### batches

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK CASCADE indexed | |
| total | Integer | number of prompts submitted |
| completed | Integer | succeeded jobs (atomic increment) |
| failed | Integer | failed jobs (atomic increment) |
| status | String | `running` \| `done` \| `partial` |
| created_at | DateTime | |

### request_records

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| provider | String | |
| model_id | String | |
| modality | String | |
| routing_mode | String | `auto` \| `manual` |
| status | String | `pending` \| `success` \| `failed` |
| input_payload | JSON | |
| output_content | String NULL | |
| output_path / output_url | String NULL | |
| credits_deducted | Integer | |
| latency_ms | Integer | |
| tags | String[] | PostgreSQL ARRAY |
| error_message | String NULL | |
| created_at / completed_at | DateTime | |

### prompt_cache

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| cache_key | String UNIQUE indexed | sha256(modality+model_id+prompt) |
| modality / model_id | String | |
| prompt_text | Text | truncated to 2000 chars |
| output_content / output_url | Text NULL | |
| output_type | String | |
| credits_saved | Numeric(10,4) | accumulated savings |
| hit_count | Integer | incremented on each cache hit |
| last_hit_at | DateTime NULL | |
| created_at / expires_at | DateTime | default TTL 24 h |

### notifications

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK CASCADE | |
| type | String | `credits_low` \| `key_expiring` \| `job_done` \| `system` \| `credits_topup` \| `team_invite` \| `model_deprecated` |
| title | String | |
| body | String NULL | |
| link | String NULL | frontend route |
| is_read | Boolean | |
| created_at | DateTime | |

### webhooks

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID indexed | |
| url | String | |
| secret | String NULL | for HMAC signature |
| events | JSON | array of event strings |
| is_active | Boolean | |
| created_at | DateTime | |

### webhook_deliveries

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| webhook_id | UUID indexed | |
| request_id | String NULL | |
| event | String | |
| payload | JSON | |
| status | String | `pending` \| `delivered` \| `failed` |
| attempts | Integer | |
| last_response_code | Integer NULL | |
| last_error | Text NULL | |
| next_retry_at | DateTime NULL | |
| delivered_at / created_at | DateTime | |

### pipelines

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID indexed | |
| name | String | |
| description | Text NULL | |
| steps | JSON | `[{step, modality, model_id, provider, prompt_template, params?}]` |
| is_public | Boolean | |
| cron_schedule | String NULL | standard 5-field cron |
| last_run_at | DateTime NULL | |
| created_at | DateTime | |

### prompt_templates

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK CASCADE | |
| name | String | |
| prompt | Text | |
| modality | String NULL | |
| model_id | String NULL | |
| params | JSONB NULL | extra generation params |
| variables | JSONB NULL | `{"var_name": {label, default}}` |
| is_public | Boolean | |
| created_at | DateTime | |

### finetune_jobs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID indexed | |
| provider | String | `openai` \| `replicate` \| `fal` |
| base_model_id | String | |
| display_name | String NULL | |
| external_job_id | String NULL | provider's job ID |
| status | String | `queued` \| `running` \| `succeeded` \| `failed` \| `cancelled` |
| training_file_url | Text | |
| result_model_id | String NULL | set on completion |
| params | JSON NULL | |
| error_message | Text NULL | |
| credits_used | Integer NULL | |
| created_at / completed_at | DateTime | |

### ab_experiments / ab_results

**ab_experiments**

| Column | Type |
|--------|------|
| id | UUID PK |
| user_id | UUID |
| name | String |
| modality | String |
| variants | JSON — `[{model_id, provider, weight}]` (weights sum to 100) |
| status | String — `active` \| `paused` \| `concluded` |
| winner_model_id | String NULL |
| created_at / concluded_at | DateTime |

**ab_results**

| Column | Type |
|--------|------|
| id | UUID PK |
| experiment_id | UUID |
| model_id | String |
| request_id | String |
| latency_ms / credits_used | Numeric |
| rating | Integer NULL (user feedback) |
| created_at | DateTime |

### model_registry

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| provider | String | |
| model_id | String | |
| modality | String | |
| display_name | String | |
| cost_per_unit | Numeric(10,6) | credits per token or per image |
| unit_type | String | `token` \| `image` \| `video` \| `audio` \| `minute` |
| avg_latency_ms | Integer | |
| quality_score | Numeric(3,2) | 0.0–1.0 |
| task_type | String NULL | primary task |
| task_types | String[] NULL | all supported tasks |
| vendor | String NULL | underlying vendor (e.g. Kling via FAL) |
| is_active | Boolean | |
| requires_user_key | Boolean | |
| created_at | DateTime | |
| UNIQUE | (provider, model_id) | |

### organizations / org_memberships

**organizations**

| Column | Type |
|--------|------|
| id | UUID PK |
| name | String |
| slug | String UNIQUE |
| owner_id | UUID FK→users |
| description | String NULL |
| credits_balance | Integer default 2500 |
| stripe_customer_id | String NULL |
| created_at | DateTime |

**org_memberships**

| Column | Type |
|--------|------|
| id | UUID PK |
| org_id | UUID FK CASCADE |
| user_id | UUID FK CASCADE |
| role | String — `owner` \| `admin` \| `member` \| `viewer` |
| invited_by | UUID NULL |
| joined_at | DateTime |

### audit_logs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK NULL | |
| org_id | UUID NULL | |
| action | String | `signup` \| `login` \| `generate` \| `key_rotated` \| `credits_added` \| `org_created` \| `org_updated` \| `ownership_transferred` |
| resource_type | String NULL | `org` \| `model` \| `user` |
| resource_id | String NULL | |
| meta | JSONB NULL | arbitrary context |
| ip_address | String NULL | |
| created_at | DateTime | |

### telegram_connections / telegram_auth_tokens

**telegram_connections**

| Column | Type |
|--------|------|
| id | UUID PK |
| user_id | UUID UNIQUE |
| chat_id | BigInteger UNIQUE |
| username | String NULL |
| is_active | Boolean |
| connected_at | DateTime |
| preferences | JSONB default {} |

**telegram_auth_tokens**

| Column | Type |
|--------|------|
| id | UUID PK |
| user_id | UUID FK CASCADE |
| token | String UNIQUE — random |
| expires_at | DateTime — 5 min |
| used_at | DateTime NULL |
| created_at | DateTime |

---

## 5. Alembic Migrations

Migrations live in `app/db/migrations/versions/`. Run with:

```bash
alembic upgrade head
```

To create a new migration after changing a model:

```bash
alembic revision --autogenerate -m "describe_change"
```

Always review the generated file before applying — autogenerate misses array columns, custom types, and index changes.

**Migration history (chronological):**

| File | Change |
|------|--------|
| `9a4a5feb1e34` | Initial schema |
| `6f87d45936d9` | Usage log enhancements |
| `ee221b6d33c0` | request_records table |
| `c9d1e2f3a4b5` | User auth fields |
| `e2f3a4b5c6d7` | ModelRegistry task_type, vendor |
| `f3a4b5c6d7e8` | task_types ARRAY |
| `a1b2c3d4e5f6` | Multi-provider routing |
| `b2c3d4e5f6a7` | Notifications, webhooks, templates, pipelines |
| `fe0c71d4f4c6` | User provider keys (later removed) |
| `c3d4e5f6a7b8` | Job and Batch tables |
| `b0e3c5051278` | output_content on request_records |
| `d4e5f6a7b8c9` | Org enhancements, audit logs |
| `f6a7b8c9d0e1` | Credit estimation |
| `e5f6a7b8c9d0` | Remove BYOK |
| `g7h8i9j0k1l2` | Telegram models |
| `h8i9j0k1l2m3` | Telegram preferences |
| `j0k1l2m3n4o5` | Favorites, template variables, pipeline cron |
| `k1l2m3n4o5p6` | Fine-tuning, A/B experiments, leaderboard ratings |
| `l2m3n4o5p6q7` | Auto top-up config, batch counter columns |
| `229c938c6fb6` | Merge heads |

---

## 6. API Reference

All routes are mounted at `/api/v1/` in `app/main.py`. Authentication is via `X-API-Key` header (checked in `app/api/deps.py`).

### Dependency injection

```python
# app/api/deps.py
get_db()            # yields Session
get_current_user()  # looks up User by hashed API key, raises 401 if invalid
get_current_api_key() # returns the ApiKey ORM row (for limit checking)
```

### Route summary by module

#### auth.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/signup` | None | Create account; returns full API key once |
| POST | `/auth/login` | None | Returns full API key (fails with 409 if key predates secure storage) |
| GET | `/me` | Key | Returns profile with prefix-only key |
| PATCH | `/me` | Key | Update name / phone |
| POST | `/auth/keys` | Key | Create secondary key |
| GET | `/auth/keys` | Key | List keys (prefix shown, not full value) |
| POST | `/auth/keys/{id}/rotate` | Key | Rotate key — new value shown once |
| PATCH | `/auth/keys/{id}` | Key | Update monthly limit |
| POST | `/auth/keys/{id}/reset-usage` | Key | Reset credits_used_this_month |
| DELETE | `/auth/keys/{id}` | Key | Revoke key |

#### generate.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/generate` | Key | Synchronous or async (if `async_job: true`) generation |
| POST | `/generate/batch` | Key | Submit up to 50 prompts as background batch |

**GenerateRequest schema:**
```python
class GenerateRequest(BaseModel):
    prompt: str
    modality: str = "text"          # text | image | video | audio
    mode: str = "auto"              # auto | manual
    model: str | None = None        # manual mode: exact model_id
    task_type: str | None = None    # e.g. text_to_image
    use_org_credits: bool = False
    async_job: bool = False
```

**GenerateResponse schema:**
```python
class GenerateResponse(BaseModel):
    request_id: str
    modality: str
    provider: str
    model: str
    output: OutputObject          # {type, content, url, mime_type}
    meta: MetaObject              # {latency_ms, credits_used, credits_remaining, units_used, unit_type, routing_mode}
```

#### jobs.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/jobs` | Key | List recent jobs (`?limit=`) |
| GET | `/jobs/{id}` | Key | Get job detail |
| GET | `/jobs/{id}/status` | Key | Poll status (`status`, `error_message`, `completed_at`) |
| GET | `/jobs/batch/{batch_id}` | Key | Batch record + all child jobs |

#### billing.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/billing/packs` | None | List credit packs |
| GET | `/billing/transactions` | Key | Transaction history |
| GET | `/billing/auto-topup` | Key | Get threshold/amount/has_payment_method |
| PATCH | `/billing/auto-topup` | Key | Set threshold and/or amount |
| POST | `/billing/checkout` | Key | Create Stripe checkout session |
| POST | `/billing/webhook` | Stripe sig | Handle payment completion |

#### usage.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/usage/summary` | Key | Aggregate stats |
| GET | `/usage/by-model` | Key | Per-model breakdown (`?days=`) |
| GET | `/usage/by-provider` | Key | Per-provider breakdown |
| GET | `/usage/daily` | Key | Daily time-series |
| GET | `/usage/latency-percentiles` | Key | p50/p75/p90/p95/p99 |
| GET | `/usage` | Key | Paginated request history with filters |
| PATCH | `/usage/{request_id}/tags` | Key | Set tags array |

#### cache.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/cache/stats` | Key | Global cache totals |
| GET | `/cache/entries` | Key | Top entries by hit_count |
| DELETE | `/cache/entries/{id}` | Admin | Delete single entry |
| DELETE | `/cache/flush` | Admin | Flush entire cache |

#### webhooks.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/webhooks` | Key | List |
| POST | `/webhooks` | Key | Create (`url`, `secret?`, `events[]`) |
| PATCH | `/webhooks/{id}` | Key | Update |
| DELETE | `/webhooks/{id}` | Key | Delete |
| GET | `/webhooks/{id}/deliveries` | Key | Last 50 deliveries |
| POST | `/webhooks/{id}/test` | Key | Send test payload now |
| POST | `/webhooks/deliveries/{id}/replay` | Key | Replay delivery |

#### orgs.py
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/orgs/create` | Key | Create org |
| GET | `/orgs/mine` | Key | List user's orgs |
| GET | `/orgs/me` | Key | Active org detail + members |
| GET | `/orgs/{id}` | Key | Specific org |
| POST | `/orgs/switch/{id}` | Key | Set active org |
| PATCH | `/orgs/{id}` | Admin/Owner | Update name/description |
| DELETE | `/orgs/{id}` | Owner | Delete org |
| POST | `/orgs/{id}/credits/add` | Admin/Owner | Move personal → org pool |
| POST | `/orgs/{id}/leave` | Member | Leave org |
| PATCH | `/orgs/{id}/transfer-owner` | Owner | Change owner |
| POST | `/orgs/invite` | Admin/Owner | Add member by email |
| PATCH | `/orgs/member-role` | Owner | Change member role |
| DELETE | `/orgs/member/{user_id}` | Admin/Owner | Remove member |
| POST | `/orgs/credits/allot` | Admin/Owner | Allot pool credits to member |

#### proxy.py (OpenAI-compatible)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/chat/completions` | Bearer key | Chat completions; streaming supported |
| GET | `/v1/models` | Bearer key | Model list in OpenAI format |

---

## 7. Generation Service & Provider Routing

`app/services/generate.py` — `GenerationService.run(user, request)`.

### Flow

```
1. Validate user is active, has credits
2. Check monthly credit limit on API key
3. Build cache_key = sha256(modality + model_id + prompt)
4. Query prompt_cache — if hit: return cached output (0 credits)
5. Select provider/model:
   - mode == "auto": query model_registry ordered by quality_score DESC,
                     filter by modality + task_type, skip unavailable keys
   - mode == "manual": use request.model directly
6. Call provider adapter (see below)
7. Deduct credits: cost_per_unit × units_used
   - If use_org_credits: deduct from org.credits_balance
   - Else: deduct from credit.balance
8. Write RequestRecord
9. Store result in prompt_cache (TTL 24 h)
10. Fire async webhook: generation.complete or generation.failed
11. Return GenerateResponse
```

### Provider adapters

Each provider is a function (or class method) in `generate.py`:

| Provider key | Used for |
|-------------|---------|
| `openai` | GPT text models |
| `anthropic` | Claude text models |
| `google` | Gemini text models |
| `xai` | Grok |
| `qwen` | Qwen models |
| `stability` | SDXL image generation |
| `elevenlabs` | TTS and audio |
| `fal` | Image, video, audio via Fal.ai (wraps Kling, Luma, Hailuo, Runway, ByteDance, Wan, etc.) |
| `replicate` | Fine-tuned models |

`PLATFORM_KEYS` dict maps provider name → `settings.*_API_KEY`. Any provider with an empty key is excluded from auto-routing.

### Adding a new provider

See [Section 19](#19-adding-a-new-provider).

---

## 8. Credit & Billing System

### Credit packs (hardcoded in `billing.py`)

```python
CREDIT_PACKS = {
    "pack_500":   {"credits": 500,   "price_cents": 500},
    "pack_1500":  {"credits": 1500,  "price_cents": 1200},
    "pack_5000":  {"credits": 5000,  "price_cents": 3500},
    "pack_15000": {"credits": 15000, "price_cents": 9000},
}
```

### Stripe checkout flow

1. `POST /billing/checkout` creates a Stripe `PaymentIntent` / `CheckoutSession` with `setup_future_usage="off_session"` so the card is saved.
2. On success, Stripe fires `checkout.session.completed` to `POST /billing/webhook`.
3. The webhook handler:
   - Adds credits to `Credit.balance`
   - Creates a `CreditTransaction` (type `topup`)
   - Saves `stripe_payment_method_id` on the `User` row
   - Creates a `credits_topup` notification

### Auto top-up

Triggered from `app/api/billing.py::trigger_auto_topup(db, user, current_balance)`:

```python
if current_balance < credit.auto_topup_threshold:
    # attempt off-session Stripe charge
    pi = stripe.PaymentIntent.create(
        amount=pack_price_cents,
        currency="usd",
        customer=user.stripe_customer_id,
        payment_method=user.stripe_payment_method_id,
        confirm=True,
        off_session=True,
    )
    # on success: add credits, create CreditTransaction, notify
```

Called in `POST /generate` after every synchronous generation (inside a try/except — failure is silent to avoid breaking the generation response).

### Monthly API key limits

Checked in `POST /generate` before routing:

```python
if current_key.monthly_credit_limit is not None:
    used = current_key.credits_used_this_month or 0
    if used >= current_key.monthly_credit_limit:
        raise HTTPException(402, {"code": "SPENDING_LIMIT_EXCEEDED", ...})
```

After a successful sync generation, `credits_used_this_month` is incremented. Reset manually via `POST /auth/keys/{id}/reset-usage`.

---

## 9. Prompt Cache

Cache key: `sha256(f"{modality}:{model_id}:{prompt}")` (exact match — no fuzzy/semantic matching).

| Config | Value |
|--------|-------|
| Default TTL | 24 hours |
| Eviction | Expired entries are cleaned up lazily on access |
| Hit behaviour | Provider is not called; 0 credits deducted; `hit_count` incremented |

Cache is checked before the provider is called. A cache miss proceeds normally and the result is stored.

To disable caching for a specific request, there is currently no API flag — modify `GenerationService` to skip the lookup if needed.

---

## 10. Async Jobs & Batch Processing

### Single async job

Pass `async_job: true` in `GenerateRequest`. The endpoint immediately returns `{job_id, status: "queued"}` and registers a `BackgroundTask`.

```python
background_tasks.add_task(_run_job, str(job.id), str(current_user.id), body)
```

`_run_job` opens its own `SessionLocal` (BackgroundTasks run after the response is sent, so the request session is closed). It updates `job.status` to `running`, calls `GenerationService.run()`, then sets `success` or `failed`.

### Batch generation

`POST /generate/batch` creates one `Batch` row and one `Job` row per prompt, then registers a `_run_batch_job` background task for each.

**Race-condition-safe counter update:**

```python
# Atomic — safe under concurrent job completions
db.execute(
    _sa_update(Batch)
    .where(Batch.id == uuid(batch_id))
    .values(
        completed=Batch.completed + (1 if succeeded else 0),
        failed=Batch.failed + (0 if succeeded else 1),
    )
    .execution_options(synchronize_session=False)
)
db.commit()
# After increment: check if all jobs done, update batch.status
```

Do not replace this with a read-then-write pattern — two tasks finishing simultaneously would produce an incorrect count.

---

## 11. Webhook System

### Dispatch

```python
# Called from GenerationService and other event sources
dispatch_webhook(db, user_id, event, payload)
```

Creates a `WebhookDelivery` row and schedules an async `_deliver` task.

### Delivery

```
POST <webhook.url>
Content-Type: application/json
X-Syphakie-Event: <event>
X-Syphakie-Signature: sha256=<hmac-sha256(secret, raw_body)>
```

Status → `delivered` on 2xx, `failed` otherwise.

### Retry schedule

```
next_retry_at = now + timedelta(minutes=5 * delivery.attempts)
```

Exponential-ish back-off; manual replay available at any time.

---

## 12. Notification System

```python
# Create a notification anywhere in the codebase:
from app.models.notification import Notification

notif = Notification(
    user_id=user.id,
    type="credits_low",      # see allowed types in Section 4
    title="Credits running low",
    body="You have 50 credits remaining.",
    link="/account",
)
db.add(notif)
db.commit()
```

Frontend polls `GET /api/v1/notifications?limit=10` on every route change (via `useEffect` in `SidebarLayout.tsx`).

---

## 13. Authentication & API Keys

### Request authentication

Every protected endpoint depends on `get_current_user`:

```python
def get_current_user(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key = db.query(ApiKey).filter_by(key_hash=key_hash, is_active=True).first()
    if not api_key or (api_key.expires_at and api_key.expires_at < now()):
        raise HTTPException(401)
    api_key.last_used = now()
    return db.query(User).filter_by(id=api_key.user_id, is_active=True).first()
```

### Key storage security

- The full key value (`key_value`) is stored in plaintext in the database, returned exactly once (signup/login/rotate), and then never exposed again through the API.
- The `key_hash` (SHA-256) is used for all lookups.
- The `key_prefix` (first 8 chars) is safe to display and helps users identify keys.
- `/me` returns `key_prefix + "…"` only.

### Scope enforcement

If `api_key.scope` is non-null, `GenerationService` raises 403 if `request.modality != api_key.scope`.

---

## 14. OpenAI Compatibility Proxy

`app/api/proxy.py` translates OpenAI `ChatCompletion` requests to `GenerationService.run()` calls.

- Uses `Bearer` token from `Authorization` header (same value as `X-API-Key`).
- Supports `stream: true` — yields SSE `data: {"choices": [...]}` chunks.
- `GET /v1/models` returns all active text models in OpenAI list format.

Integration is zero-config for clients that support a `base_url` override.

---

## 15. Telegram Bot

The Telegram integration runs as a separate async process alongside FastAPI.

- **Long-polling mode** (dev): bot polls Telegram for updates.
- **Webhook mode** (prod): Telegram POSTs to `TELEGRAM_WEBHOOK_URL`. Set in `.env`.

**Auth flow:**
1. User requests `POST /telegram/token` → returns a one-time token (5-min TTL).
2. User opens Telegram bot deep link containing the token.
3. Bot receives `/start <token>`, looks up `TelegramAuthToken`, links `TelegramConnection`.

**Notification delivery:** wherever the notification system creates a `Notification` row, the Telegram integration can optionally push the same message to the user's linked chat.

---

## 16. Organizations & RBAC

Roles (ascending permission level): `viewer` < `member` < `admin` < `owner`.

| Action | Minimum role |
|--------|-------------|
| View analytics | viewer |
| Generate content | member |
| Invite members | admin |
| Add credits to org pool | admin |
| Allot pool credits to member | admin |
| Update org name/description | admin |
| Remove members | admin |
| Transfer ownership | owner |
| Delete org | owner |

Credit deduction with `use_org_credits: true` deducts from `Organization.credits_balance`. The org pool is not automatically topped up — an owner/admin must manually transfer personal credits.

---

## 17. Frontend Architecture

### Pages

All pages are under `frontend/app/` and use the Next.js 15 App Router. Every page that requires auth wraps content in `SidebarLayout`.

| Route | File | Feature |
|-------|------|---------|
| `/` | `page.tsx` | Home / redirect |
| `/login` | `login/page.tsx` | Email + password |
| `/generate` | `generate/page.tsx` | Main generation UI, batch panel |
| `/activity` | `activity/page.tsx` | History, Analytics, Gallery, Cache tabs |
| `/account` | `account/page.tsx` | Profile, keys, billing, Telegram, orgs |
| `/models` | `models/page.tsx` | Model browser, leaderboard |
| `/webhooks` | `webhooks/page.tsx` | Webhook management |

### Auth

```typescript
// lib/auth.ts
localStorage.setItem("syphakie_api_key", key)   // on login
localStorage.getItem("syphakie_api_key")          // on every API call
localStorage.removeItem("syphakie_api_key")       // on logout
```

### API client

```typescript
// lib/api.ts
export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": getApiKey() ?? "",
      ...options?.headers,
    },
  });
  if (!res.ok) throw new ApiError(res.status, await res.json());
  return res.json();
}
```

### SidebarLayout

`components/SidebarLayout.tsx` is the persistent shell rendered on every authenticated page. It:
- Fetches and displays credit balance on every render.
- Polls notifications on every route change.
- Handles dark/light mode toggle (persisted to `localStorage`).
- Contains the logout button.

---

## 18. Running Locally

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+

### Backend

```bash
cd syphakie
cp .env.example .env          # fill in DATABASE_URL and at least one provider key
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload  # runs on :8000
```

### Frontend

```bash
cd frontend
cp .env.example .env.local    # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                    # runs on :3000
```

### Seeding models

The `model_registry` table must be populated for generation to work. Run the seed script (if present) or insert rows manually:

```sql
INSERT INTO model_registry (id, provider, model_id, modality, display_name, cost_per_unit, unit_type, is_active)
VALUES (gen_random_uuid(), 'openai', 'gpt-4o', 'text', 'GPT-4o', 0.01, 'token', true);
```

---

## 19. Adding a New Provider

1. **Add the API key** to `.env.example` and `app/config.py`:
   ```python
   MYPROVIDER_API_KEY: str = ""
   ```

2. **Add the provider to `PLATFORM_KEYS`** in `app/services/generate.py`:
   ```python
   PLATFORM_KEYS = {
       ...
       "myprovider": settings.MYPROVIDER_API_KEY,
   }
   ```

3. **Implement a provider adapter** in `generate.py` — a function that takes the prompt and returns `(output_content, output_url, units_used)`.

4. **Register it in the routing logic** — add a branch in the main provider dispatch.

5. **Insert model_registry rows** for all models this provider offers (modality, cost_per_unit, unit_type, task_types, quality_score, is_active).

6. **Write and run a migration** if new config columns are needed.

---

## 20. Security Notes

- **API keys** are SHA-256 hashed before storage. The plaintext is stored separately (`key_value`) for the one-time reveal flow. Consider moving to hash-only storage for higher security environments and requiring users to copy at creation time.
- **Stripe webhook** endpoint verifies `Stripe-Signature` header using `STRIPE_WEBHOOK_SECRET`. Never process Stripe events without this check.
- **Telegram webhook** optionally verifies `X-Telegram-Bot-Api-Secret-Token` using `TELEGRAM_WEBHOOK_SECRET`. Enable it in production.
- **CORS** is restricted to `ALLOWED_ORIGINS`. Set this to your production domain(s) before deploying.
- **Admin endpoints** check `current_user.role == "admin"`. There is no separate admin token — promote users by updating the `role` column in the database directly.
- **SQL injection** is not a risk via SQLAlchemy ORM. The one raw SQL path is the atomic Batch counter update — it uses bound parameters via SQLAlchemy `update()`.
- **Output files** are served directly from disk (`OUTPUT_DIR`). In production, serve them from a CDN or object storage bucket, not from the FastAPI process.
- **`.env` must not be committed.** The `.gitignore` excludes it. Verify with `git status` before pushing.
