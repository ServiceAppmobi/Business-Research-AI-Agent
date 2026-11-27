import asyncio
import json
import uuid
from fastapi import FastAPI, Header, HTTPException, Request
from app.agent import generate_report
from app.languages import SUPPORTED_LANGUAGES
from app.payments import create_checkout_session, construct_webhook_event
from app.schemas import CheckoutRequest, CheckoutResponse, ResearchRequest, ResearchReport
from app.storage import init_db, create_order, attach_checkout, get_order, mark_paid, claim_generation, save_report, mark_failed

app = FastAPI(title="AI Business Research Agent", description="Multilingual AI-assisted business research reports with Stripe Checkout.", version="0.2.0")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-business-research-agent"}

@app.get("/api/v1/languages")
def languages():
    return SUPPORTED_LANGUAGES

@app.post("/api/v1/research", response_model=ResearchReport)
def research(request: ResearchRequest):
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language code")
    try:
        return generate_report(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=502, detail="Report generation failed")

@app.post("/api/v1/checkout", response_model=CheckoutResponse)
def checkout(payload: CheckoutRequest):
    if payload.research.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language code")
    order_id = str(uuid.uuid4())
    create_order(order_id, str(payload.customer_email), payload.research.model_dump())
    try:
        session = create_checkout_session(order_id, str(payload.customer_email))
        attach_checkout(order_id, session.id)
        return CheckoutResponse(order_id=order_id, checkout_url=session.url)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=502, detail="Could not create Stripe Checkout session")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="")):
    payload = await request.body()
    try:
        event = construct_webhook_event(payload, stripe_signature)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature or payload")

    if event["type"] not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        return {"status": "ignored"}

    session = event["data"]["object"]
    if session.get("payment_status") != "paid":
        return {"status": "awaiting_payment"}

    order_id = (session.get("metadata") or {}).get("order_id") or session.get("client_reference_id")
    if not order_id:
        return {"status": "ignored", "reason": "missing_order_id"}
    order = get_order(order_id)
    if not order:
        return {"status": "ignored", "reason": "order_not_found"}

    mark_paid(order_id)
    if not claim_generation(order_id):
        return {"status": "already_processed"}

    try:
        research_request = ResearchRequest.model_validate(json.loads(order["request_json"]))
        report = await asyncio.to_thread(generate_report, research_request)
        save_report(order_id, report.model_dump())
    except Exception:
        mark_failed(order_id)
        raise HTTPException(status_code=500, detail="Paid order report generation failed; retry webhook")
    return {"status": "completed", "order_id": order_id}

@app.get("/api/v1/orders/{order_id}")
def order_status(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    result = {"order_id": order_id, "status": order["status"], "created_at": order["created_at"]}
    if order["status"] == "completed" and order["report_json"]:
        result["report"] = json.loads(order["report_json"])
    return result
