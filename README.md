# AI Business Research Agent

Multilingual business research reports powered by Google Gemini, Tavily web research, and Stripe Checkout.

## Current features

- FastAPI API and health endpoint
- 11 output languages: English, Spanish, Portuguese, German, French, Simplified Chinese, Arabic, Hindi, Japanese, Indonesian, and Polish
- Tavily web search using five targeted queries and up to 15 deduplicated source records
- Gemini synthesis with source IDs, uncertainty handling, and separation of facts from assumptions
- B2B Lead Finder using public company-level web sources
- Stripe Checkout for one-time report purchases
- Signed Stripe webhook handling
- SQLite order persistence and report status tracking
- PDF report generation and download
- Per-order bearer access tokens; only a SHA-256 token hash is stored in SQLite

## Research quality and limitations

Web retrieval currently uses Tavily search snippets, not full independent source audits. Search snippets are untrusted input and are treated as reference data, not instructions. The model is asked to cite retrieved source IDs and distinguish facts from assumptions, but AI-generated interpretation can still be wrong. Review high-impact claims and verify primary sources before relying on them commercially.

If `TAVILY_API_KEY` is not configured, reports are generated without live web retrieval and are explicitly labelled as unverified AI synthesis. Do not sell those reports as current, sourced market intelligence.

Lead Finder returns research candidates based on public company-level snippets. It does not verify buying intent, guarantee contactability, or collect personal email addresses or phone numbers. Validate each company and use its official public contact route before outreach.

## Configuration

- `GEMINI_API_KEY` and `GEMINI_MODEL`: Google Gemini API
- `TAVILY_API_KEY`: Tavily web search API
- `STRIPE_SECRET_KEY`: Stripe account API key
- `STRIPE_WEBHOOK_SECRET`: signing secret for this app's Stripe webhook endpoint
- `PRODUCT_CURRENCY`: defaults to `pln`
- `RESEARCH_REPORT_PRICE_MINOR`: defaults to `4900` (PLN 49.00)
- `APP_BASE_URL`: public HTTPS origin of this app
- `DATABASE_PATH`: SQLite database path

The same Stripe account API key can be used as in `working-ebook-agent` if it has the required permissions. The webhook signing secret is unique per endpoint: create a new endpoint for this service and set its new `whsec_` value. Stripe Connect destination transfers and platform fees are not copied because this product sells its own reports.

Never commit API keys. Configure secrets only in the hosting provider's private environment settings. Use separate test and live keys.

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
- `GET /api/v1/languages`
- `POST /api/v1/research` — direct development endpoint
- `POST /api/v1/leads/find` — company-level B2B lead discovery; request fields: `industry`, `target_market`, `ideal_customer`, `language`, `max_results`
- `POST /api/v1/checkout` — creates a Stripe Checkout session and returns `order_id`, `checkout_url`, and a one-time `access_token`
- `POST /webhook/stripe` — Stripe webhook receiver
- `GET /api/v1/orders/{order_id}` — returns order status and the report when complete; requires `Authorization: Bearer <access_token>`
- `GET /api/v1/orders/{order_id}/report.pdf` — downloads the PDF; requires the same bearer token
- `GET /payment/success` and `GET /payment/cancel` — Checkout return pages

### Protecting customer reports

The checkout response includes a cryptographically random access token exactly once. The client must store it securely and send it in the HTTP Authorization header when requesting order status or the PDF. The server stores only its SHA-256 hash. Do not put this token in a public URL, analytics event, browser log, or support ticket.

The payment success page intentionally does not reveal order status or report contents. A customer-facing web portal and secure email delivery are separate follow-up features.

The SQLite startup migration adds the token-hash column to existing databases. Orders created before this security change have no token and cannot be accessed through the protected order endpoints; issue new orders or implement a verified recovery flow rather than bypassing authentication.

## Deployment

The Render blueprint uses a persistent disk mounted at `/var/data` for SQLite order storage. This requires a Render plan that supports persistent disks and may incur hosting costs. Configure `GEMINI_API_KEY`, `TAVILY_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `APP_BASE_URL`, and `DATABASE_PATH` in the host's private environment settings.

Create a new Stripe webhook endpoint pointing to `https://YOUR_HOST/webhook/stripe` and subscribe to:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`

## Before public launch

- Add rate limiting and abuse controls to public research endpoints
- Add a customer portal and secure email delivery/recovery flow
- Add webhook event-ID persistence for full Stripe event idempotency
- Add monitoring, privacy notices, retention controls, and a source verification workflow
- Run end-to-end tests with Stripe test mode and configured Gemini/Tavily keys
