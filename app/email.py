import logging
from html import escape
from urllib.parse import urljoin

import requests

from app.config import settings

logger = logging.getLogger(__name__)
RESEND_API_URL = "https://api.resend.com/emails"


def _send_email(to: str, subject: str, html: str) -> bool:
    if not settings.resend_api_key or not settings.email_from:
        logger.info("Email delivery skipped: Resend is not configured")
        return False
    try:
        response = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": html},
            timeout=12,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Email delivery failed")
        return False


def send_order_access_email(to: str, order_id: str, access_token: str) -> bool:
    portal_url = urljoin(settings.app_base_url.rstrip("/") + "/", "portal")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#10243d">
      <h2>Your Business Research order access</h2>
      <p>Keep these private access details safe. They let you view your order and report.</p>
      <p><strong>Order reference</strong><br>{escape(order_id)}</p>
      <p><strong>Secure access token</strong><br><code>{escape(access_token)}</code></p>
      <p><a href="{escape(portal_url, quote=True)}">Open your secure customer portal</a></p>
      <p style="color:#64748b;font-size:12px">Do not forward this email. Anyone with the access token can view your order and report.</p>
    </div>"""
    return _send_email(to, "Your Business Research order access", html)


def send_report_ready_email(to: str, order_id: str) -> bool:
    portal_url = urljoin(settings.app_base_url.rstrip("/") + "/", "portal")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#10243d">
      <h2>Your business research report is ready</h2>
      <p>Your report for order <strong>{escape(order_id)}</strong> has been generated.</p>
      <p>Open the secure customer portal and enter your order reference and access token to review or download the PDF.</p>
      <p><a href="{escape(portal_url, quote=True)}">Open customer portal</a></p>
    </div>"""
    return _send_email(to, "Your Business Research report is ready", html)
