import stripe
from app.config import settings

def create_checkout_session(order_id: str, customer_email: str):
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
                "unit_amount": settings.research_report_price_minor,
                "product_data": {
                    "name": "AI Business Research Report",
                    "description": "Multilingual AI-assisted business research report",
                },
            },
            "quantity": 1,
        }],
        "metadata": {"order_id": order_id},
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
