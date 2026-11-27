# AI Business Research Agent

Multilingual business research report API powered by Google Gemini, with paid orders through Stripe Checkout.

## Current features
- FastAPI API and health endpoint
- 11 output languages
- Structured research report schema
- Gemini API integration
- Stripe Checkout one-time payment endpoint
- Signed Stripe webhook handling
- SQLite order persistence and report status endpoint

## Research limitation
The report generator currently uses information supplied in the request and model knowledge. It does not yet perform live web research, verify facts, or attach source citations. Do not market reports as independently verified market intelligence until retrieval, source tracking, and human validation are implemented.

## Stripe configuration
The project follows the environment-variable convention in the existing working-ebook-agent project: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, PRODUCT_CURRENCY (defaults to pln), and APP_BASE_URL.

The report price is separately configurable as RESEARCH_REPORT_PRICE_MINOR (default 4900, i.e. PLN 49.00, matching the amount in the existing e-book deployment blueprint). The same Stripe account API key can be used if it has the required permissions. The webhook signing secret is unique to each webhook endpoint: create a new endpoint for this service and set its new whsec_ value as STRIPE_WEBHOOK_SECRET. Stripe Connect Express destination transfers and platform fees are intentionally not copied because this product sells its own reports.

Never commit API keys. Configure secrets only in the hosting provider's private environment settings. Use separate test and live keys; before production, prefer a restricted API key with only the permissions required by Checkout.

## Local setup
Python 3.11+, Gemini API access, and a Stripe account with Checkout enabled.

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs.

## API
- GET /health
- GET /api/v1/languages
- POST /api/v1/research (direct development endpoint)
- POST /api/v1/checkout (creates a paid order and returns the Stripe Checkout URL)
- POST /webhook/stripe (Stripe webhook receiver)
- GET /api/v1/orders/{order_id} (checks order status and returns the report when complete)
- GET /payment/success and GET /payment/cancel (Checkout return pages)

## Deployment notes
The included Render blueprint uses a persistent disk mounted at /var/data for SQLite order storage. This requires a Render plan that supports persistent disks and may incur hosting costs. Set APP_BASE_URL to the deployed HTTPS origin and configure DATABASE_PATH=/var/data/research_orders.sqlite3.

Create a new Stripe webhook endpoint pointing to https://YOUR_HOST/webhook/stripe and subscribe to checkout.session.completed, checkout.session.async_payment_succeeded, and checkout.session.async_payment_failed.

The handler verifies the Stripe signature, processes paid completion events, and ignores other event types. Report generation runs after confirmed payment. The order status endpoint currently uses a random UUID as a bearer-style lookup; add customer authentication and rate limiting before public launch.

## Roadmap
1. Live web retrieval and source citations
2. Evidence grading and fact-check workflow
3. Customer authentication and secure report access
4. PDF export and email delivery
5. Production monitoring, privacy and retention controls
