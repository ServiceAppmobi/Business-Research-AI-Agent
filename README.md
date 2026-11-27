# AI Business Research Agent

Multilingual business research report API powered by Google Gemini, with live web source retrieval and paid orders through Stripe Checkout.

## Current features
- FastAPI API and health endpoint
- 11 output languages
- Tavily web search (five targeted queries, up to 15 deduplicated source records)
- Gemini synthesis with source IDs and explicit uncertainty instructions
- Source references attached to every report\n- B2B Lead Finder endpoint using company-level public web sources\n- Lead qualification with fit rationale, public signals, and source URLs (no personal contact harvesting)
- Stripe Checkout one-time payment endpoint
- Signed Stripe webhook handling
- SQLite order persistence and report status endpoint\n- PDF report download endpoint

## Research quality and limitations
Web retrieval uses Tavily search snippets, not full independent source audits. Search snippets are untrusted input and are treated as reference data, not instructions. The model is asked to cite retrieved source IDs and distinguish facts from assumptions, but AI-generated interpretation can still be wrong. Review high-impact claims and verify primary sources before relying on them commercially.

If TAVILY_API_KEY is not configured, reports are generated without live web retrieval and are explicitly labelled as unverified AI synthesis. Do not sell those reports as current, sourced market intelligence.

## Configuration
- GEMINI_API_KEY and GEMINI_MODEL: Google Gemini API
- TAVILY_API_KEY: Tavily web search API
- STRIPE_SECRET_KEY: Stripe account API key
- STRIPE_WEBHOOK_SECRET: signing secret for this app's Stripe webhook endpoint
- PRODUCT_CURRENCY: defaults to pln
- RESEARCH_REPORT_PRICE_MINOR: defaults to 4900 (PLN 49.00)
- APP_BASE_URL: public HTTPS origin of this app
- DATABASE_PATH: SQLite database path

The same Stripe account API key can be used as in working-ebook-agent if it has the required permissions. The webhook signing secret is unique per endpoint: create a new endpoint for this service and set its new whsec_ value. Stripe Connect Express destination transfers and platform fees are not copied because this product sells its own reports.

Never commit API keys. Configure secrets only in the hosting provider's private environment settings. Use separate test and live keys.

## Local setup
Python 3.11+, Gemini API access, Tavily API access for live search, and a Stripe account with Checkout enabled.

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs.

## API
- GET /health
- GET /api/v1/languages
- POST /api/v1/research (direct development endpoint)\n- POST /api/v1/leads/find (company-level B2B lead discovery; request: industry, target_market, ideal_customer, language, max_results)
- POST /api/v1/checkout (creates a paid order and returns the Stripe Checkout URL)
- POST /webhook/stripe (Stripe webhook receiver)
- GET /api/v1/orders/{order_id} (checks order status and returns the report when complete)
- GET /payment/success and GET /payment/cancel (Checkout return pages)

## Deployment
The Render blueprint uses a persistent disk mounted at /var/data for SQLite order storage. This requires a Render plan that supports persistent disks and may incur hosting costs. Configure GEMINI_API_KEY, TAVILY_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, APP_BASE_URL, and DATABASE_PATH in the host's private environment settings.

Create a new Stripe webhook endpoint pointing to https://YOUR_HOST/webhook/stripe and subscribe to checkout.session.completed, checkout.session.async_payment_succeeded, and checkout.session.async_payment_failed.

## Lead Finder limitations\nLead Finder returns research candidates based on public company-level snippets. It does not verify buying intent, guarantee contactability, or collect personal email addresses or phone numbers. Validate each company and use its official public contact route before outreach.\n\n## Before public launch
- Add automated tests for payment, webhook idempotency, search failures, and malformed model output.
- Add customer authentication and rate limiting to order/report retrieval.
- Add PDF export and email delivery.
- Add monitoring, privacy notices, retention controls, and source verification workflow.
