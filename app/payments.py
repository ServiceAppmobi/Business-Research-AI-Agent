import stripe
from app.config import settings

REPORT_PLANS = {
    "basic": {"name": "Basic Business Research Report", "price_minor": 4900, "description": "Essential market overview, customer segments, opportunities, risks and key competitors."},
    "professional": {"name": "Professional Business Research Report", "price_minor": 9900, "description": "Detailed market analysis, 5–10 competitor comparison, positioning, SWOT and strategic recommendations."},
    "premium": {"name": "Premium Business Intelligence Report", "price_minor": 19900, "description": "Extended market and competitor intelligence, market-entry opportunities, pricing strategy and 90-day action plan."},
}

def create_checkout_session(order_id: str, customer_email: str, plan: str = "professional"):
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    client = stripe.StripeClient(settings.stripe_secret_key)
    params = {
        "mode": "payment",
        "customer_email": customer_email,
        "client_reference_id": order_id,
        "line_items": [{
            "price_data": {
                "currency": settings.product_currency,
                "unit_amount": REPORT_PLANS[plan]["price_minor"],
                "product_data": {
                    "name": REPORT_PLANS[plan]["name"],
                    "description": REPORT_PLANS[plan]["description"],
                },
            },
            "quantity": 1,
        }],
        "metadata": {"order_id": order_id, "report_plan": plan},
        "success_url": f"{settings.app_base_url}/payment/success?order_id={order_id}",
        "cancel_url": f"{settings.app_base_url}/payment/cancel",
    }
    # Do not set payment_method_types: Stripe Dashboard controls eligible dynamic methods.
    session = client.v1.checkout.sessions.create(params)
    return session

def construct_webhook_event(payload: bytes, signature: str):
    if not settings.stripe_webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")
    return stripe.Webhook.construct_event(
        payload, signature, settings.stripe_webhook_secret
    )
