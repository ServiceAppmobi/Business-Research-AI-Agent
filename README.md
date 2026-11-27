# AI Business Research Agent

Multilingual business research reports powered by Google Gemini, Tavily web research, and Stripe Checkout.

## Current features

- FastAPI API and health endpoint
- 11 output languages: English, Spanish, Portuguese, German, French, Simplified Chinese, Arabic, Hindi, Japanese, Indonesian, and Polish
- Tavily web search using five targeted queries and up to 15 deduplicated source records
- Gemini synthesis with source IDs, uncertainty handling, and separation of facts from assumptions
- B2B Lead Finder using public company-level web sources
- Stripe Checkout for one-time report purchases with three report tiers: Basic PLN 49, Professional PLN 99, Premium PLN 199
- Signed Stripe webhook handling with persistent event-ID idempotency and retry recovery
- SQLite order persistence and report status tracking
- PDF report generation and download
- Per-order bearer access tokens; only a SHA-256 token hash is stored in SQLite
- Customer portal at `/portal` for order status, report preview, and PDF download
- IP-based rate limits on public API endpoints (research: 5/min, lead finder: 5/min, checkout: 10/min; global default: 120/min)
- Optional transactional email delivery through Resend: secure order credentials after checkout and report-ready notification

## Research quality and limitations

Web retrieval currently uses Tavily search snippets, not full independent source audits. Search snippets are untrusted input and are treated as reference data, not instructions. The model is asked to cite retrieved source IDs and distinguish facts from assumptions, but AI-generated interpretation can still be wrong. Review high-impact claims and verify primary sources before relying on them commercially.

If `TAVILY_API_KEY` is not configured, reports are generated without live web retrieval and are explicitly labelled as unverified AI synthesis. Do not sell those reports as current, sourced market intelligence.

Lead Finder returns research candidates based on public company-level snippets. It does not verify buying intent, guarantee contactability, or collect personal email addresses or phone numbers. Validate each company and use its official public contact route before outreach.

## Configuration

- `GEMINI_API_KEY` and `GEMINI_MODEL`: Google Gemini API
- `TAVILY_API_KEY`: Tavily web search API
- `STRIPE_SECRET_KEY`: Stripe account API key
- `STRIPE_WEBHOOK_SECRET`: signing secret for this app's Stripe webhook endpoint
- `RESEND_API_KEY`: optional Resend API key for transactional email
- `EMAIL_FROM`: verified sender identity configured in Resend
- `ALLOW_DIRECT_AI_API`: defaults to `false`; set to `true` only for intentional, separately monitored direct AI API access. When false, `/api/v1/research` and `/api/v1/leads/find` return HTTP 403 to prevent unbilled Gemini/Tavily usage.
- `PRODUCT_CURRENCY`: defaults to `pln`
- Report pricing is defined in `app/payments.py`: Basic PLN 49, Professional PLN 99, Premium PLN 199. Checkout accepts `plan` (`basic`, `professional`, or `premium`); omitted plan defaults to Professional.
- `APP_BASE_URL`: public HTTPS origin of this app
- `DATABASE_PATH`: SQLite database path

The same Stripe account API key can be used as in `working-ebook-agent` if it has the required permissions. The webhook signing secret is unique per endpoint: create a new endpoint for this service and set its new `whsec_` value. Stripe Connect destination transfers and platform fees are not copied because this product sells its own reports.

Never commit API keys. Configure secrets only in the hosting provider's private environment settings. For email, verify your sending domain in Resend before setting `RESEND_API_KEY` and `EMAIL_FROM`. Use separate test and live keys.

## Local setup

Python 3.11+, Gemini API access, Tavily API access for live search, and a Stripe account with Checkout enabled.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## API

- `GET /health`

### API abuse protection

SlowAPI applies per-client-IP limits: 5 requests/minute for direct research, 5/minute for Lead Finder, and 10/minute for Checkout. Other routes inherit a default ceiling of 120 requests/minute. Limits are in-memory per app instance; use a shared Redis-backed limiter before scaling to multiple instances.
- `GET /api/v1/pricing` — returns the three available report packages and prices in PLN
- `GET /api/v1/languages`
- `POST /api/v1/research` — direct development endpoint; disabled by default unless `ALLOW_DIRECT_AI_API=true`
- `POST /api/v1/leads/find` — company-level B2B lead discovery; disabled by default unless `ALLOW_DIRECT_AI_API=true`; request fields: `industry`, `target_market`, `ideal_customer`, `language`, `max_results`
- `POST /api/v1/checkout` — creates a Stripe Checkout session and returns `order_id`, `checkout_url`, and a one-time `access_token`
- `POST /webhook/stripe` — Stripe webhook receiver
- `GET /api/v1/orders/{order_id}` — returns order status and the report when complete; requires `Authorization: Bearer <access_token>`
- `GET /api/v1/orders/{order_id}/report.pdf` — downloads the PDF; requires the same bearer token
- `GET /payment/success` and `GET /payment/cancel` — Checkout return pages

### Protecting customer reports

Checkout is enabled only when both `RESEND_API_KEY` and `EMAIL_FROM` are configured and the order-access email is successfully delivered. This prevents a customer from paying without receiving their secure portal credentials. The checkout response also includes a cryptographically random access token exactly once. The client must store it securely and send it in the HTTP Authorization header when requesting order status or the PDF. The server stores only its SHA-256 hash. Do not put this token in a public URL, analytics event, browser log, or support ticket.

The payment success page intentionally does not reveal order status or report contents. Customers can use `/portal` with their order reference and access token. When Resend is configured, the checkout flow emails the access details and successful report generation sends a ready notification. The access token is sent only in the email body, never in a URL. If Resend is not configured or email delivery fails, checkout and report generation continue; the checkout API still returns the access token to the client.

The SQLite startup migration adds the token-hash column to existing databases. Orders created before this security change have no token and cannot be accessed through the protected order endpoints; issue new orders or implement a verified recovery flow rather than bypassing authentication.

## Deployment

The Render blueprint uses a persistent disk mounted at `/var/data` for SQLite order storage. This requires a Render plan that supports persistent disks and may incur hosting costs. Configure `GEMINI_API_KEY`, `TAVILY_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `APP_BASE_URL`, and `DATABASE_PATH` in the host's private environment settings.

Create a new Stripe webhook endpoint pointing to `https://YOUR_HOST/webhook/stripe` and subscribe to:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`

## Before public launch

- Review rate-limit thresholds under real traffic and add a shared Redis-backed limiter before scaling to multiple instances
- Add email-based access recovery (requires a verified email ownership flow)
- Add delivery retry/monitoring for transactional email
- Add monitoring, privacy notices, retention controls, and a source verification workflow
- Run end-to-end tests with Stripe test mode and configured Gemini/Tavily keys
