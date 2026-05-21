# SyphaKie

**SyphaKie** is a self-hosted AI generation platform that unifies multiple AI providers (OpenAI, Anthropic, Google, FAL, Stability AI, ElevenLabs, Kling, Luma, Wan, Qwen, xAI) behind a single API and web interface. Generate text, images, video, and audio — with smart routing, credit billing, pipelines, A/B experiments, a Telegram bot, and full usage analytics — all from one place.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Telegram Bot](#telegram-bot)
- [Credits System](#credits-system)
- [Providers](#providers)
- [Frontend Pages](#frontend-pages)
- [Roadmap & Future Scope](#roadmap--future-scope)

---

## Features

### Core Generation
- **Multi-modal generation** — text, image, video, and audio from a single unified API
- **Auto routing** — the platform scores available models by cost, latency, and capability and picks the best one automatically
- **Manual routing** — select any specific model and provider directly
- **Task types** — fine-grained task classification (e.g. `text_to_image`, `image_to_video`, `text_to_speech`, `lip_sync`, etc.)
- **Streaming** — OpenAI-compatible SSE streaming for text generation
- **Async jobs** — fire-and-forget job queue with status polling (`queued → running → success/failed`)
- **File uploads** — attach images, video, audio, or documents as generation context

### Saved Generations & History
- **Request history** — every generation is logged with prompt, output, model, provider, status, latency, and credits
- **Output storage** — text outputs stored in DB; media files stored on disk and served via `/files/`
- **Favorites (saved generations)** — star any generation in history; view and manage your saved outputs
- **Gallery** — visual grid of all image/video/audio outputs with lightbox preview and download
- **CSV export** — download full history including outputs as a spreadsheet

### Analytics
- **Usage dashboard** — total requests, credits used, error rate, avg latency
- **Daily breakdown** — bar chart of requests per day with error highlighting
- **Model breakdown** — per-model request count, credits, avg latency, error rate
- **Latency percentiles** — p50, p75, p90, p95, p99 across all successful requests
- **By-modality split** — visual distribution of text / image / video / audio usage

### Prompt Templates
- **Template library** — save and name reusable prompts with optional model and modality bindings
- **Template variables** — define `{{variable_name}}` placeholders with labels and default values; the generate page renders input fields and substitutes values before sending

### Pipelines
- **Multi-step pipelines** — chain models across modalities (e.g. text → image → video)
- **Step placeholders** — `{{input}}` for the initial prompt, `{{step:N}}` for the output of step N
- **Interactive runner** — run pipelines step-by-step in the browser with per-step prompt editing and re-run
- **Cron scheduling** — set a standard 5-field cron expression on any pipeline; a background scheduler runs it automatically at the configured interval
- **Run history** — every pipeline execution is persisted with step outputs, total credits, and timestamps

### A/B Experiments
- **Weighted variants** — define multiple model/prompt variants with traffic weights
- **Result tracking** — log which variant was used for each generation
- **User ratings** — collect thumbs-up/down feedback on outputs
- **Model leaderboard** — aggregate ratings across models and providers

### Fine-tuning
- **Job submission** — create fine-tune jobs targeting OpenAI, Replicate, or FAL
- **External job tracking** — store the external provider job ID and poll for status
- **Training data management** — attach training data URLs and hyperparameters

### Organizations & Teams
- **Multi-tenant orgs** — create organizations, invite members by email, assign roles (owner / admin / member)
- **Org credits** — each org has its own credit pool; members can choose to charge personal or org credits per generation
- **Role-based access** — admin-only routes enforced at the API level

### Webhooks
- **Event subscriptions** — subscribe to events (`generation.success`, `generation.failed`, `pipeline.completed`, etc.)
- **Delivery tracking** — every webhook delivery attempt is logged with HTTP status and response body
- **Automatic retry** — failed deliveries are retried with exponential back-off
- **Manual replay** — re-send any past delivery from the Webhooks UI

### Telegram Bot (`@SyphaKieBot`)
- **Account linking** — connect your Telegram account to your SyphaKie account via a one-time token
- **Quick generation** — send a text prompt directly in chat and get a result back
- **Voice input** — send a voice message; it's transcribed and used as the generation prompt
- **Image-to-image** — send an image with a caption to use it as a reference
- **Inline mode** — use `@SyphaKieBot query` in any chat to generate without leaving the conversation
- **Usage summary** — `/usage` shows your credit balance and recent request stats
- **Top-up prompts** — bot notifies you when your balance is low
- **Broadcast** — admins can push messages to all connected Telegram users
- **Set default model** — `/setdefault` saves your preferred model per modality
- **Command menu** — all commands registered as a Telegram bot command menu

### Developer API
- **OpenAI-compatible proxy** — `POST /api/v1/chat/completions` and `GET /api/v1/models` with Bearer or X-API-Key auth; drop-in replacement for OpenAI SDK calls
- **API key management** — generate, list, and revoke keys from the Account page
- **Prompt cache** — optional prompt caching layer to reduce repeated provider calls
- **Admin panel** — manage users, adjust credits, view audit logs

### Billing & Credits
- **Credit system** — every generation costs credits calculated from provider pricing and units used
- **Starting balance** — 1000 credits on signup
- **Sidebar credit bar** — real-time white→purple gradient bar showing balance/1000
- **Stripe integration** — billing infrastructure wired up for paid top-ups
- **Auto top-up** — (infrastructure in place) configurable threshold and amount for automatic Stripe charges

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser / Telegram                │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────┐
│            Next.js 15 Frontend (port 3000)          │
│  Pages: generate, activity, pipelines, models, …    │
└────────────────────┬────────────────────────────────┘
                     │ REST (X-API-Key or Bearer)
┌────────────────────▼────────────────────────────────┐
│          FastAPI Backend (port 8000)                │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐ │
│  │ Routing Engine│  │ Scheduler  │  │ Telegram Bot│ │
│  └──────┬───────┘  └─────┬──────┘  └──────┬──────┘ │
│         │                │                │         │
│  ┌──────▼────────────────▼────────────────▼──────┐  │
│  │              Provider Adapters                 │  │
│  │  OpenAI · Anthropic · Google · FAL · Stability│  │
│  │  ElevenLabs · Qwen · xAI · Kling · Luma · Wan │  │
│  └───────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼────────────────────────────────┐
│              PostgreSQL Database                    │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React, Tailwind CSS, TypeScript |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2, Alembic |
| Database | PostgreSQL |
| Auth | API key (hashed) + email/password (bcrypt) |
| AI providers | OpenAI, Anthropic, Google, FAL, Stability AI, ElevenLabs, Qwen, xAI |
| Telegram | aiogram 3 |
| Scheduling | asyncio + croniter |
| Billing | Stripe (infrastructure) |
| File serving | FastAPI StaticFiles (`/files/`) |

---

## Project Structure

```
syphakie/
├── app/                          # FastAPI backend
│   ├── api/                      # Route handlers
│   │   ├── auth.py               # Login, register, API key management
│   │   ├── generate.py           # Generation endpoint + async job dispatcher
│   │   ├── usage.py              # History, analytics, summary endpoints
│   │   ├── favorites.py          # Save / unsave / list generations
│   │   ├── templates.py          # Prompt template CRUD
│   │   ├── pipelines.py          # Pipeline CRUD, run, PATCH (cron)
│   │   ├── models.py             # Model registry CRUD
│   │   ├── credits.py            # Balance read + admin adjust
│   │   ├── billing.py            # Stripe webhooks + top-up
│   │   ├── webhooks.py           # Webhook subscriptions + delivery
│   │   ├── experiments.py        # A/B experiment management
│   │   ├── finetune.py           # Fine-tune job submission
│   │   ├── leaderboard.py        # Aggregated model ratings
│   │   ├── orgs.py               # Organization + membership management
│   │   ├── notifications.py      # In-app notification feed
│   │   ├── jobs.py               # Async job status polling
│   │   ├── outputs.py            # Output retrieval by request ID
│   │   ├── admin.py              # Admin-only user/credit management
│   │   ├── cache.py              # Prompt cache management
│   │   └── proxy.py              # OpenAI-compatible proxy endpoints
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── api_key.py
│   │   ├── credit.py
│   │   ├── request_record.py     # Every generation attempt
│   │   ├── usage_log.py          # Per-generation cost breakdown
│   │   ├── favorite.py           # Saved generations
│   │   ├── pipeline.py           # Pipeline + PipelineRun
│   │   ├── prompt_template.py    # Saved prompt templates w/ variables
│   │   ├── job.py                # Async job queue
│   │   ├── webhook.py            # Webhook + WebhookDelivery
│   │   ├── organization.py       # Org + OrgMembership
│   │   ├── ab_experiment.py      # A/B experiments + results
│   │   ├── finetune_job.py       # Fine-tune job tracking
│   │   ├── model_registry.py     # Available models + pricing
│   │   ├── model_rating.py       # User ratings per output
│   │   ├── notification.py       # In-app notifications
│   │   ├── prompt_cache.py       # Cached prompt→response pairs
│   │   └── audit_log.py          # Admin audit trail
│   ├── providers/                # AI provider adapters
│   │   ├── base.py               # AdapterRequest / AdapterResponse
│   │   ├── openai_adapter.py
│   │   ├── anthropic_adapter.py
│   │   ├── google_adapter.py
│   │   ├── fal_adapter.py        # FAL.ai (images, video)
│   │   ├── stability_adapter.py
│   │   ├── elevenlabs_adapter.py
│   │   ├── qwen_adapter.py
│   │   └── xai_adapter.py
│   ├── routing/                  # Smart routing engine
│   │   ├── engine.py             # Model selection logic
│   │   ├── scorer.py             # Cost / latency / capability scoring
│   │   └── config.py             # Routing configuration
│   ├── services/
│   │   ├── generate.py           # GenerationService (orchestrates adapter calls)
│   │   ├── credits.py            # Credit deduction logic
│   │   ├── usage.py              # Usage log writes
│   │   ├── outputs.py            # Output persistence (disk + DB)
│   │   └── scheduler.py          # Cron pipeline scheduler (asyncio loop)
│   ├── telegram/                 # Telegram bot (aiogram 3)
│   │   ├── router.py             # Bot router + webhook receiver
│   │   ├── handlers/             # Command and message handlers
│   │   ├── keyboards.py          # Inline keyboard builders
│   │   ├── messages.py           # Message formatters
│   │   ├── service.py            # Bot business logic
│   │   └── notifier.py           # Push notifications to Telegram
│   ├── middleware/
│   │   └── rate_limit.py         # Per-key rate limiting
│   ├── db/
│   │   ├── session.py            # SQLAlchemy engine + SessionLocal
│   │   └── migrations/           # Alembic migrations (18 revisions)
│   ├── schemas/
│   │   └── generate.py           # Pydantic request/response schemas
│   ├── config.py                 # Settings via pydantic-settings / .env
│   └── main.py                   # FastAPI app factory + lifespan
│
├── frontend/                     # Next.js 15 frontend
│   ├── app/
│   │   ├── page.tsx              # Home (redirects to /generate)
│   │   ├── login/                # Login + register
│   │   ├── generate/             # Main generation UI
│   │   ├── activity/             # History + Analytics + Gallery tabs
│   │   ├── models/               # Model registry browser
│   │   ├── pipelines/            # Pipeline builder + runner + scheduler
│   │   ├── account/              # API keys, profile, billing
│   │   ├── webhooks/             # Webhook management
│   │   ├── experiments/          # A/B experiment management
│   │   ├── finetune/             # Fine-tune job management
│   │   ├── team/                 # Org + member management
│   │   ├── compare/              # Side-by-side model comparison
│   │   ├── evaluate/             # Output evaluation tools
│   │   ├── gallery/              # Media gallery
│   │   ├── status/               # Platform status page
│   │   └── analytics/            # Redirects to activity?tab=analytics
│   ├── components/
│   │   └── SidebarLayout.tsx     # App shell: nav, credits bar, notifications
│   └── lib/
│       ├── api.ts                # Typed API client (apiFetch, fetchModels, …)
│       └── auth.ts               # API key storage (localStorage)
│
├── outputs/                      # Generated media files (gitignored)
├── requirements.txt
├── alembic.ini
└── .env                          # Local secrets (never commit)
```

---

## Database Schema

| Table | Purpose |
|---|---|
| `users` | Accounts with email/password hash, role, Stripe customer ID |
| `api_keys` | Hashed API keys per user with prefix for display |
| `credits` | Current credit balance per user |
| `credit_transactions` | Audit trail of every credit change |
| `request_records` | Every generation attempt with input, output, status, latency |
| `usage_logs` | Per-request cost breakdown (units, cost_per_unit, credits_charged) |
| `favorites` | User-saved generations (links user → request_record) |
| `jobs` | Async job queue (queued → running → success/failed) |
| `pipelines` | Pipeline definitions with steps JSON, cron schedule |
| `pipeline_runs` | Individual pipeline executions with per-step outputs |
| `prompt_templates` | Saved prompts with optional variables JSONB |
| `model_registry` | Available models with provider, modality, pricing, task types |
| `model_ratings` | User thumbs-up/down per output |
| `ab_experiments` | A/B test definitions with weighted variants |
| `ab_results` | Which variant was used for each request |
| `finetune_jobs` | Fine-tuning job tracking with external provider job IDs |
| `webhooks` | Webhook endpoint subscriptions with event filters |
| `webhook_deliveries` | Every delivery attempt with HTTP status and response |
| `organizations` | Team orgs with name and credit pool |
| `org_memberships` | User→org assignments with role |
| `notifications` | In-app notification feed per user |
| `audit_logs` | Admin action audit trail |
| `prompt_cache` | Cached prompt→response pairs to avoid repeat provider calls |
| `telegram_connections` | Links Telegram user IDs to SyphaKie accounts |
| `telegram_auth_tokens` | One-time tokens for Telegram account linking |
| `telegram_states` | FSM state storage for the Telegram bot conversation flow |

---

## API Reference

All endpoints are prefixed `/api/v1`. Authentication is via `X-API-Key: sk-...` header.

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login → returns API key |
| GET | `/auth/keys` | List API keys |
| POST | `/auth/keys` | Create new API key |
| DELETE | `/auth/keys/{id}` | Revoke API key |

### Generation
| Method | Path | Description |
|---|---|---|
| POST | `/generate` | Generate (sync or async job) |
| GET | `/jobs/{id}` | Poll async job status |
| GET | `/outputs/{request_id}` | Fetch output for a completed request |

### Usage & Analytics
| Method | Path | Description |
|---|---|---|
| GET | `/usage` | Paginated request history with filters |
| GET | `/usage/summary` | Aggregate stats (total, credits, error rate) |
| GET | `/usage/daily` | Day-by-day breakdown |
| GET | `/usage/by-model` | Per-model breakdown |
| GET | `/usage/by-provider` | Per-provider breakdown |
| GET | `/usage/latency-percentiles` | p50–p99 latency stats |

### Favorites
| Method | Path | Description |
|---|---|---|
| POST | `/favorites` | Save a generation |
| DELETE | `/favorites/{request_id}` | Unsave |
| GET | `/favorites` | List saved generations with full request data |
| GET | `/favorites/ids` | Lightweight — just the set of saved request IDs |

### Templates
| Method | Path | Description |
|---|---|---|
| GET | `/templates` | List your templates |
| POST | `/templates` | Create template (supports `variables` JSONB) |
| DELETE | `/templates/{id}` | Delete template |

### Pipelines
| Method | Path | Description |
|---|---|---|
| GET | `/pipelines` | List your pipelines |
| POST | `/pipelines` | Create pipeline |
| GET | `/pipelines/{id}` | Get pipeline |
| PATCH | `/pipelines/{id}` | Update (e.g. set `cron_schedule`) |
| DELETE | `/pipelines/{id}` | Delete pipeline + runs |
| POST | `/pipelines/{id}/run` | Trigger a run |
| GET | `/pipelines/{id}/runs` | List runs |
| GET | `/pipelines/runs/{run_id}` | Get a specific run |

### Models
| Method | Path | Description |
|---|---|---|
| GET | `/models` | List models (filterable by modality, provider) |
| POST | `/models` | Register a model (admin) |
| PATCH | `/models/{id}` | Update model |
| DELETE | `/models/{id}` | Remove model |

### Credits & Billing
| Method | Path | Description |
|---|---|---|
| GET | `/credits` | Get current balance |
| POST | `/credits/adjust` | Adjust balance (admin only) |

### Organizations
| Method | Path | Description |
|---|---|---|
| POST | `/orgs` | Create org |
| GET | `/orgs/me` | Get your org membership |
| POST | `/orgs/invite` | Invite member by email |
| DELETE | `/orgs/members/{id}` | Remove member |

### OpenAI-Compatible Proxy
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/chat/completions` | Drop-in for OpenAI chat completions (streaming supported) |
| GET | `/api/v1/models` | OpenAI-compatible model list |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- API keys for whichever AI providers you want to use

### 1. Clone & set up the backend

```bash
git clone https://github.com/nitya2405/syphakie.git
cd syphakie

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env   # or create .env manually
```

Edit `.env` — see [Environment Variables](#environment-variables) below.

### 3. Create the database

```bash
# create DB and user in psql
psql -U postgres -c "CREATE USER syphakie WITH PASSWORD 'syphakie';"
psql -U postgres -c "CREATE DATABASE syphakie OWNER syphakie;"

# run all migrations
python -m alembic upgrade head
```

### 4. Set up the frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OPENAI_API_KEY` | Optional | OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key |
| `GOOGLE_API_KEY` | Optional | Google Gemini API key |
| `FAL_API_KEY` | Optional | FAL.ai API key (images, video) |
| `STABILITY_API_KEY` | Optional | Stability AI API key |
| `ELEVENLABS_API_KEY` | Optional | ElevenLabs API key (audio) |
| `QWEN_API_KEY` | Optional | Alibaba Qwen API key |
| `XAI_API_KEY` | Optional | xAI (Grok) API key |
| `OUTPUT_DIR` | No | Directory for media files (default: `outputs`) |
| `BASE_URL` | No | Backend base URL (default: `http://localhost:8000`) |
| `DEFAULT_CREDITS` | No | Starting credits for new users (default: `1000`) |
| `TELEGRAM_BOT_TOKEN` | Optional | Bot token from @BotFather |
| `TELEGRAM_BOT_USERNAME` | Optional | Bot username without @ |
| `TELEGRAM_WEBHOOK_URL` | Optional | Public HTTPS URL for Telegram webhooks (leave empty for polling) |
| `TELEGRAM_WEBHOOK_SECRET` | Optional | HMAC secret for webhook verification |

---

## Running Locally

**Terminal 1 — Backend**
```powershell
# from project root, venv activated
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend**
```powershell
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Telegram Bot

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token
2. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_BOT_USERNAME` in `.env`
3. Restart the backend — the bot starts in long-polling mode automatically
4. For production, set `TELEGRAM_WEBHOOK_URL` to your public HTTPS URL and the bot switches to webhook mode

**Available commands:**
```
/start     — Link your SyphaKie account
/generate  — Generate with the current default model
/usage     — View credit balance and recent stats
/setdefault — Set your default model per modality
/history   — Recent generation history
/help      — Command reference
```

Send any text, image, or voice message directly in the chat to generate without using a command.

---

## Credits System

Credits are an internal currency that abstract over raw provider costs:

- New accounts start with **1,000 credits**
- Each generation deducts credits based on the model's `cost_per_unit × units_used`
- The sidebar shows a live **gradient credit bar** (white at 0 → purple at 1,000+)
- Organization credit pools are separate from personal balances
- Admins can adjust any user's balance via `POST /api/v1/credits/adjust`

---

## Providers

| Provider | Modalities | Notes |
|---|---|---|
| OpenAI | text, image | GPT-4o, DALL-E 3, Whisper |
| Anthropic | text | Claude 3.x family |
| Google | text, image | Gemini 1.5/2.0, Imagen |
| FAL.ai | image, video | Flux, Kling, LTX, CogVideo via FAL |
| Stability AI | image | SDXL, SD3 |
| ElevenLabs | audio | TTS, voice cloning |
| Qwen | text, image | Alibaba Qwen models |
| xAI | text | Grok |

Provider adapters live in `app/providers/` and all implement the same `BaseAdapter` interface, making it straightforward to add new providers.

---

## Frontend Pages

| Route | Description |
|---|---|
| `/generate` | Main generation UI with prompt, modality, mode, model selector, template picker, and streaming |
| `/activity` | Three tabs: **History** (paginated request log with star/save, output column), **Analytics** (charts and stats), **Gallery** (media grid with lightbox) |
| `/models` | Browse and manage the model registry with provider keys |
| `/pipelines` | Build multi-step pipelines, run them interactively, set cron schedules |
| `/account` | Manage API keys, profile, and billing |
| `/webhooks` | Create webhook endpoints, view delivery history, replay failed deliveries |
| `/experiments` | Create and manage A/B experiments across model variants |
| `/finetune` | Submit and track fine-tuning jobs |
| `/team` | Org management — invite members, assign roles |
| `/compare` | Side-by-side model comparison for the same prompt |
| `/evaluate` | Structured evaluation tools for outputs |
| `/status` | Platform health and uptime |

---

## Roadmap & Future Scope

### Near-term (high value, low effort)

- **Request tagging** — add `tags TEXT[]` to `request_records`; filter by tag in History and Gallery. One migration, zero new endpoints needed beyond a filter parameter.

- **Webhook replay UI** — `WebhookDelivery` already stores the full payload. A single `POST /webhooks/deliveries/{id}/replay` endpoint and a button in the UI is all that's needed.

- **Per-API-key spending limits** — `monthly_credit_limit` and `credits_used_this_month` on `api_keys`. Enforce in the generation path. Useful for teams sharing keys.

- **Output search** — full-text search over `output_content` and prompts in `request_records` using PostgreSQL `tsvector`. No additional infrastructure needed.

- **Template sharing** — add `is_public BOOLEAN` to `prompt_templates` and a `GET /templates/public` endpoint. Community-contributed prompts with variables.

### Medium-term

- **Credit auto top-up** — Stripe is already wired. Add `auto_topup_threshold` and `auto_topup_amount` to `credits`; trigger a Stripe charge in the generation path when balance drops below threshold.

- **Prompt cache hit rate analytics** — surface cache hits/misses in the analytics dashboard. The `prompt_cache` table exists; just needs query logic and a chart.

- **Batch generation** — `POST /generate/batch` that accepts an array of prompts and runs them concurrently as async jobs. Results polled via `GET /jobs/batch/{batch_id}`.

- **Custom model endpoints (BYOM)** — allow users to register a custom HTTP endpoint as a "provider". The routing engine treats it like any other adapter.

- **Output versioning** — track multiple outputs for the same logical generation (regenerations). Link via `parent_request_id` on `request_records`.

- **Evaluation rubrics** — structured evaluation forms (clarity, accuracy, style) per modality, stored and averaged. Feeds into the leaderboard with more signal than thumbs-up/down.

### Long-term / Platform scale

- **Streaming pipeline runs** — SSE stream of per-step events so the UI updates in real time without polling.

- **Plugin system** — post-processing plugins (watermarking, upscaling, background removal) that run as pipeline steps without needing a full provider adapter.

- **SDK & CLI** — a first-party Python SDK (`pip install syphakie`) and CLI tool (`skie generate "a red panda"`) using the OpenAI-compatible proxy endpoint under the hood.

- **Self-hosted model inference** — integrate Ollama or vLLM as a local provider adapter. Zero marginal cost for text generation at the expense of hardware.

- **Multi-region output storage** — S3 / R2 / GCS backend for `outputs/` instead of local disk. Required for any multi-instance deployment.

- **SSO / OAuth** — Google and GitHub OAuth login in addition to email/password. The `users` table already has a `role` column; just needs an OAuth flow.

- **Real-time collaboration** — shared generation sessions where multiple team members can see and rate each other's outputs live (WebSocket-based).

- **Cost forecasting** — based on historical usage patterns, predict monthly spend and alert when on track to exceed a budget.

- **Fine-tune → deploy loop** — after a fine-tune job completes, one-click register the resulting model in the model registry so it immediately appears in the generate UI.

---

## Security Notes

- API keys are stored as bcrypt hashes; only the prefix is shown after creation
- Passwords are bcrypt-hashed (cost factor 12)
- Never commit `.env` to version control — add it to `.gitignore`
- Rate limiting middleware is applied globally
- Admin endpoints require `role = "admin"` verified server-side
- Webhook deliveries validate the HMAC secret header when configured

---

## License

MIT — see `LICENSE` for details.
