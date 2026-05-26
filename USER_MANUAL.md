# SyphaKie — User Manual

> A unified AI generation platform for text, image, video, and audio — accessed through a dashboard or API.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Generating Content](#2-generating-content)
3. [Activity & History](#3-activity--history)
4. [Credits & Billing](#4-credits--billing)
5. [API Keys](#5-api-keys)
6. [Webhooks](#6-webhooks)
7. [Models & Leaderboard](#7-models--leaderboard)
8. [Batch Generation](#8-batch-generation)
9. [Notifications](#9-notifications)
10. [Account Settings](#10-account-settings)
11. [Organizations & Teams](#11-organizations--teams)
12. [Telegram Bot](#12-telegram-bot)
13. [OpenAI-Compatible API](#13-openai-compatible-api)
14. [FAQ & Troubleshooting](#14-faq--troubleshooting)

---

## 1. Getting Started

### Create an Account

1. Open the SyphaKie dashboard in your browser.
2. Click **Sign Up**, enter your email address and a password, then submit.
3. Your account is created with **1,000 free credits**.
4. Your API key is shown **once** — copy it and store it somewhere safe (a password manager, for example). You will not be able to see it again without rotating it.

### Log In

Enter your email and password on the login page. After logging in you are taken directly to the **Generate** tab.

### Your API Key

Every request to SyphaKie — whether from the dashboard or from your own code — is authenticated with an API key. The dashboard stores your key in your browser's local storage automatically. If you are integrating via the API, you must include the key in every request as the `X-API-Key` header.

---

## 2. Generating Content

The **Generate** tab is the main workspace. It supports four modalities.

### Choosing a Modality

Use the buttons at the top of the page to select what you want to create:

| Modality | What it produces |
|----------|-----------------|
| **Text** | Chat responses, summaries, translations, documents |
| **Image** | Still images from a text prompt or an uploaded image |
| **Video** | Short video clips from text or an image |
| **Audio** | Text-to-speech, speech transcription, or music |

### Mode: Auto vs Manual

- **Auto mode** — SyphaKie picks the best available model for your modality and task. Recommended for most users.
- **Manual mode** — You choose the exact provider and model. Useful when you need a specific model or are comparing outputs.

### Task Type

Each modality has sub-tasks. For example:

- **Text:** Chat, Summarisation, Translation
- **Image:** Text-to-image, Image-to-image, Image editing
- **Video:** Text-to-video, Image-to-video, Video editing, Lip sync
- **Audio:** Text-to-speech, Speech-to-text, Text-to-music

Select a task type from the dropdown before writing your prompt.

### Writing a Prompt

Type your prompt in the text area. For image and video tasks you can also upload a source file using the **Upload** button.

### Submitting

Click **Generate**. For most requests you will see the result within a few seconds. For longer tasks (video, some image workflows) the job may be queued and you will see a loading state until it completes.

### Viewing the Output

- **Text** results appear inline in the output area.
- **Image** results display as a preview with a download link.
- **Video** results display as a video player.
- **Audio** results display as an audio player.

### Saving to Favourites

Click the **Save** icon next to any result to add it to your Favourites. You can optionally add a note. Favourites are accessible from the **Activity** tab.

### History Sidebar

The right sidebar shows your recent generations. Click any item to re-view its output. You can also use the search box to find past generations by prompt text.

---

## 3. Activity & History

The **Activity** tab has four sub-tabs.

### History

A searchable, filterable log of all your past generations.

| Filter | Options |
|--------|---------|
| Modality | text, image, video, audio |
| Provider | openai, anthropic, google, fal, etc. |
| Status | success, failed |
| Date range | from / to |
| Free text search | matched against your prompt |
| Tag | custom tag strings |

Click any row to expand it and see full input, output, credits used, latency, and the model/provider that handled it.

**Tagging:** Click the tag icon on any row to add custom tags. Tags help you organise requests by project or purpose.

### Analytics

Charts showing your usage over time:

- Requests per day
- Credits spent per day
- Breakdown by modality, provider, and model
- Average latency percentiles (p50 / p90 / p99)
- Error rate

Use the **Days** dropdown to change the lookback window (1–90 days).

### Gallery

Browse image outputs you have generated. Filter by tag.

### Cache

Shows prompt-cache analytics — how many times previously-seen prompts were served from cache, and how many credits that saved. The cache automatically stores responses for 24 hours and re-uses them for identical prompts, so repeated calls with the same prompt and model cost 0 credits.

---

## 4. Credits & Billing

### What are credits?

Credits are the currency used to pay for generations. Different models cost different amounts per request. You can see the cost of each model in the **Models** tab.

### Free credits

New accounts receive 1,000 free credits. No payment method is required to start.

### Buying credits

Go to **Account → Billing** and choose a credit pack:

| Pack | Credits | Price |
|------|---------|-------|
| Starter | 500 | $5 |
| Growth | 1,500 | $12 |
| Pro | 5,000 | $35 |
| Scale | 15,000 | $90 |

Click **Buy** next to the pack you want. You are redirected to a Stripe checkout page. After payment, credits are added to your account instantly.

### Auto top-up

Auto top-up automatically buys more credits when your balance drops below a threshold, so you never run out mid-project.

**To enable:**

1. Buy credits at least once — this saves your payment method on file.
2. Go to **Account → Auto Top-up**.
3. Set a **Threshold** (e.g. 200 — trigger when balance drops below 200 credits).
4. Set an **Amount** — choose one of the standard credit pack sizes.
5. Save. From now on, whenever a generation causes your balance to drop below the threshold, SyphaKie automatically charges your saved card for the chosen pack size.

You will receive an in-app notification each time an auto top-up fires.

### Transaction history

**Account → Billing → Transactions** shows a full log: top-ups, auto top-ups, usage deductions, and any admin adjustments — with the balance after each event.

---

## 5. API Keys

### Why multiple API keys?

You can create multiple API keys for different integrations, team members, or projects. Each key can have independent limits.

### Creating a key

**Account → API Keys → New Key**

| Field | Description |
|-------|-------------|
| Name | A label for your own reference |
| Scope | Restrict the key to one modality (text, image, video, audio) — leave blank for full access |
| Expires in | Optional: number of days until the key auto-expires |
| Monthly credit limit | Optional: cap how many credits this key can spend per calendar month |

The full key value is shown **once** after creation. Copy it immediately.

### What the dashboard shows

After creation the dashboard only shows the key's **prefix** (e.g. `sk_live_ab12…`). This is intentional — full keys are only shown at creation time to prevent accidental exposure.

### Rotating a key

If a key is compromised or you just want to cycle it, click **Rotate** next to it. A new key value is generated; the old value stops working immediately. The new full value is shown once.

### Revoking a key

Click **Revoke** to permanently disable a key. This cannot be undone.

### Monthly limits

If a key's monthly credit limit is reached, that key returns a `402 SPENDING_LIMIT_EXCEEDED` error until the start of the next month (or until you reset the counter from **Account → API Keys**).

---

## 6. Webhooks

Webhooks let SyphaKie POST a JSON payload to a URL you control whenever something happens.

### Supported events

| Event | When it fires |
|-------|--------------|
| `generation.complete` | A generation finishes successfully |
| `generation.failed` | A generation fails |
| `credits.low` | Your balance drops below a low threshold |
| `pipeline.complete` | A multi-step pipeline run finishes |
| `finetune.complete` | A fine-tuning job finishes |

### Creating a webhook

**Webhooks → New Webhook**

1. Enter the **URL** SyphaKie should POST to.
2. Optionally enter a **Secret** — SyphaKie will include an `X-Syphakie-Signature` header (`sha256=<hmac>`) so you can verify requests are genuine.
3. Select which **events** should trigger this webhook.
4. Save.

### Delivery and retries

SyphaKie records every delivery attempt. If your endpoint returns a non-2xx status, SyphaKie retries with exponential back-off. You can view the full delivery log in **Webhooks → [webhook name] → Deliveries** and manually replay any failed delivery.

### Testing

Click **Send Test** next to a webhook to fire a test payload immediately. Use this to verify your endpoint is reachable and handles the format correctly.

### Payload format

```json
{
  "event": "generation.complete",
  "request_id": "abc123",
  "modality": "image",
  "provider": "fal",
  "model": "flux-pro",
  "credits_used": 20,
  "output_url": "https://...",
  "created_at": "2026-05-26T12:00:00Z"
}
```

The `X-Syphakie-Signature` header is `sha256=<HMAC-SHA256 of the raw body using your secret>`.

---

## 7. Models & Leaderboard

### Models tab

Browse every model available on the platform. Filter by:

- **Modality** — text, image, video, audio
- **Provider** — openai, anthropic, google, fal, stability, elevenlabs, etc.

Each model card shows:
- Display name and provider
- Cost per unit (credits per token or per image/video/audio minute)
- Average latency
- Quality score (community-derived)
- Whether it requires you to supply your own API key

### Leaderboard

The leaderboard ranks models within each modality based on community ratings. After any generation you can rate the output (thumbs up / thumbs down). These ratings are aggregated into a quality score visible to all users.

### Provider status

The **Status** page shows real-time provider uptime, error rates, and average latency over the last 24 hours. Check here if you are seeing unexpected errors from a specific provider.

---

## 8. Batch Generation

Batch generation lets you submit up to **50 prompts at once**. All prompts are processed in parallel in the background.

### Using the batch panel

On the **Generate** tab, scroll down to find the **Batch Panel**.

1. Enter one prompt per line (or paste a list).
2. Select modality, mode, and optionally a model — these settings apply to all prompts.
3. Click **Run Batch**.
4. A batch ID is returned. The panel polls for progress and shows each result as it completes.

### Checking batch status via API

```
GET /api/v1/jobs/batch/{batch_id}
```

Response includes the batch record (`total`, `completed`, `failed`, `status`) plus the full list of individual jobs.

### Batch statuses

| Status | Meaning |
|--------|---------|
| `running` | Some jobs are still in progress |
| `done` | All jobs succeeded |
| `partial` | All jobs finished but some failed |

---

## 9. Notifications

The **bell icon** in the sidebar shows your unread notification count.

Click it to open the notification drawer. Click any notification to navigate to the relevant page. Click **Mark all read** to clear the badge.

### Notification types

| Type | When you receive it |
|------|---------------------|
| Credits low | Your balance drops to a low level |
| Credits top-up | An auto top-up or manual purchase completes |
| Key expiring | An API key is close to its expiry date |
| Job done | An async generation job finishes |
| Team invite | You have been added to an organisation |
| Model deprecated | A model you have used is being retired |
| System | General platform announcements |

---

## 10. Account Settings

### Profile

Update your **display name**, **email address**, and **phone number** from **Account → Profile**.

### API Keys

Covered in [Section 5](#5-api-keys).

### Billing & Auto top-up

Covered in [Section 4](#4-credits--billing).

### Telegram integration

Connect your Telegram account to receive notifications and interact with SyphaKie through the Telegram bot. See [Section 12](#12-telegram-bot).

### Danger zone

The account page includes options to rotate your primary key and manage all secondary keys.

---

## 11. Organizations & Teams

Organisations let you share a credit pool and collaborate with teammates.

### Creating an organisation

**Account → Organizations → New Organization**

Enter a name and optional description. You become the **Owner** automatically. A shared credit pool starts empty.

### Inviting members

**Account → Organizations → [org name] → Invite**

Enter the email address and role of the person to add.

| Role | Can do |
|------|--------|
| **Viewer** | View generations and analytics |
| **Member** | Generate content, view history |
| **Admin** | Invite/remove members, top up credit pool |
| **Owner** | Everything, including deleting the org and transferring ownership |

The invitee receives an in-app notification.

### Credit pool

**Account → Organizations → Add Credits** — transfer credits from your personal balance to the org pool.

**Account → Organizations → Allot Credits** — distribute pool credits to a specific member's personal balance.

When making an API call, pass `"use_org_credits": true` in the request body to draw from the org pool instead of your personal balance.

### Switching active organization

**Account → Organizations → Switch** next to any org. Once switched, analytics and some features show organisation-level data.

### Transferring ownership

**Account → Organizations → Transfer Ownership** — select a new owner from current members. You remain as an admin.

### Leaving or deleting

- Members and admins can **Leave** an org.
- The Owner can **Delete** the org, which removes all members from it. The credit pool is not automatically refunded.

---

## 12. Telegram Bot

The Telegram integration lets you receive notifications in Telegram.

### Connecting

1. **Account → Telegram → Connect**
2. Click the link shown — it opens the SyphaKie Telegram bot.
3. Send `/start` in the bot chat.
4. Your account is linked. You will now receive notification messages in Telegram for the same events as the in-app notification system.

### Disconnecting

**Account → Telegram → Disconnect** — unlinks your Telegram account. In-app notifications continue to work normally.

---

## 13. OpenAI-Compatible API

SyphaKie exposes an OpenAI-compatible endpoint for text generation. Any tool or library that supports OpenAI's Chat Completions API can be pointed at SyphaKie with no code changes.

### Base URL

```
https://api.yourdomain.com/v1
```

### Authentication

Use your SyphaKie API key as the `Authorization: Bearer <key>` header — the same format as OpenAI.

### Chat completions

```http
POST /v1/chat/completions
Authorization: Bearer <your-syphakie-api-key>
Content-Type: application/json

{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "Explain quantum entanglement simply."}
  ],
  "stream": false
}
```

Streaming (`"stream": true`) is also supported.

### Model list

```http
GET /v1/models
Authorization: Bearer <your-syphakie-api-key>
```

Returns all active text models in OpenAI list format.

### Changing your base URL in popular tools

| Tool | Setting |
|------|---------|
| OpenAI Python SDK | `client = OpenAI(base_url="https://api.yourdomain.com/v1", api_key="sk_...")` |
| LangChain | `openai_api_base="https://api.yourdomain.com/v1"` |
| LiteLLM | `base_url="https://api.yourdomain.com/v1"` |

---

## 14. FAQ & Troubleshooting

### My API key stopped working

- The key may have expired — check the expiry date in **Account → API Keys**.
- The key's monthly credit limit may be exhausted — check **Account → API Keys** and either reset the counter or raise the limit.
- The key may have been rotated or revoked.
- If you see a `KEY_ROTATE_REQUIRED` error, your key is from an older era and you need to rotate it from the Account page to get a new full-value key.

### I can't see my full API key

The full key is only shown once — at creation or rotation. The dashboard shows only the prefix for security. To get a new key, click **Rotate** on any existing key.

### A generation returned an error

- Check the **Activity → History** tab for the error message on that request.
- If the error mentions a specific provider, check **Status** to see if that provider is having issues.
- Try switching to a different model or letting Auto mode choose.

### My video/audio generation is taking a long time

Video and audio jobs can take 30 seconds to several minutes depending on the model and length. The dashboard polls automatically and shows the result as soon as it is ready. If a job is still queued after 10 minutes, try submitting again.

### I was charged but my credits didn't appear

Wait up to 5 minutes for Stripe's webhook to process. If credits still haven't appeared, contact support with your Stripe payment intent ID (available in your Stripe email receipt).

### The cache tab shows credits saved — what does that mean?

The prompt cache stores responses for identical prompts for 24 hours. If you (or your application) sends the same prompt + model combination again within that window, SyphaKie returns the cached result and deducts 0 credits. The Cache tab shows the total credits you have saved this way.

### How do I use organisation credits in my API calls?

Add `"use_org_credits": true` to the generate request body. Make sure your account is a member of an org with a non-zero credit pool, and that you have at least Member role.

### How do I export my generation history?

Use the `GET /api/v1/usage` endpoint with pagination to retrieve all your records in JSON format. There is no CSV export from the dashboard currently.
