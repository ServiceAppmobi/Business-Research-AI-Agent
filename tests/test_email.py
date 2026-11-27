from app import email
from app.config import settings


class FakeResponse:
    def raise_for_status(self):
        return None


def test_access_email_uses_resend_and_keeps_token_out_of_url(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "test-resend-key")
    monkeypatch.setattr(settings, "email_from", "Reports <reports@example.com>")
    monkeypatch.setattr(settings, "app_base_url", "https://research.example.com")
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(email.requests, "post", fake_post)
    assert email.send_order_access_email("buyer@example.com", "order-123", "secret-token")
    assert captured["url"] == email.RESEND_API_URL
    assert captured["json"]["to"] == ["buyer@example.com"]
    assert "secret-token" in captured["json"]["html"]
    assert "secret-token" not in captured["json"]["html"].split('href="')[1].split('"')[0]


def test_email_is_skipped_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr(settings, "email_from", "")
    assert email.send_report_ready_email("buyer@example.com", "order-123") is False
