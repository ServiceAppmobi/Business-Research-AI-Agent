import asyncio
import json
import uuid
from io import BytesIO
from xml.sax.saxutils import escape
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from app.agent import generate_report
from app.languages import SUPPORTED_LANGUAGES
from app.payments import create_checkout_session, construct_webhook_event
from app.schemas import CheckoutRequest, CheckoutResponse, ResearchRequest, ResearchReport
from app.storage import init_db, create_order, attach_checkout, get_order, mark_paid, mark_payment_failed, claim_generation, save_report, mark_failed

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

    session = event["data"]["object"]
    if event["type"] == "checkout.session.async_payment_failed":
        failed_order_id = (session.get("metadata") or {}).get("order_id") or session.get("client_reference_id")
        if failed_order_id:
            mark_payment_failed(failed_order_id)
        return {"status": "payment_failed"}
    if event["type"] not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        return {"status": "ignored"}

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

@app.get("/payment/success", response_class=HTMLResponse)
def payment_success(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    status = order["status"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Payment received</title></head>
    <body style="font-family:system-ui;max-width:680px;margin:60px auto;padding:24px">
    <h1>Payment received</h1><p>Your research report is being prepared.</p>
    <p>Order status: <strong>{status}</strong></p>
    <p>Check your report status at <code>/api/v1/orders/{order_id}</code>.</p>
    </body></html>"""

@app.get("/payment/cancel", response_class=HTMLResponse)
def payment_cancel():
    return """<!doctype html><html><head><meta charset="utf-8"><title>Payment cancelled</title></head>
    <body style="font-family:system-ui;max-width:680px;margin:60px auto;padding:24px">
    <h1>Payment cancelled</h1><p>No payment was taken. You can return and try again.</p>
    </body></html>"""

@app.get("/api/v1/orders/{order_id}/report.pdf")
def download_report_pdf(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] != "completed" or not order["report_json"]:
        raise HTTPException(status_code=409, detail="Report is not ready yet")

    report = json.loads(order["report_json"])
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm, title="AI Business Research Report"
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6))
    story = [Paragraph("AI Business Research Report", styles["Title"]), Spacer(1, 8)]
    sections = [
        ("Executive Summary", "executive_summary"),
        ("Market Overview", "market_overview"),
        ("Target Customers", "target_customers"),
        ("Opportunities", "opportunities"),
        ("Risks", "risks"),
        ("Competitor Landscape", "competitor_landscape"),
        ("Recommended Next Steps", "recommended_next_steps"),
        ("Assumptions and Limitations", "assumptions_and_limitations"),
    ]
    for heading, key in sections:
        value = report.get(key, "")
        if not value:
            continue
        story.append(Paragraph(escape(heading), styles["SectionHeading"]))
        if isinstance(value, list):
            for item in value:
                story.append(Paragraph("• " + escape(str(item)), styles["BodyText"]))
                story.append(Spacer(1, 3))
        else:
            story.append(Paragraph(escape(str(value)).replace("\\n", "<br/>"), styles["BodyText"]))
    citations = report.get("citations", [])
    if citations:
        story.append(Paragraph("Sources", styles["SectionHeading"]))
        for index, source in enumerate(citations, start=1):
            title = escape(str(source.get("title", "Source")))
            url = escape(str(source.get("url", "")))
            snippet = escape(str(source.get("snippet", "")))
            story.append(Paragraph(f"[S{index}] <link href=\"{url}\" color=\"blue\">{title}</link>", styles["BodyText"]))
            if snippet:
                story.append(Paragraph(snippet, styles["Italic"]))
            story.append(Spacer(1, 5))
    story.append(Spacer(1, 12))
    story.append(Paragraph(escape(str(report.get("research_method", ""))), styles["Italic"]))
    story.append(Paragraph(escape(str(report.get("disclaimer", ""))), styles["Italic"]))
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="business-research-{order_id}.pdf"'}
    )
