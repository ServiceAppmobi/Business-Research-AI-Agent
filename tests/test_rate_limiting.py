from fastapi.testclient import TestClient

from app.main import app, limiter

client = TestClient(app)


def test_limiter_is_registered_on_app():
    assert app.state.limiter is limiter


def test_public_api_rate_limit_configuration():
    assert limiter._default_limits
    assert any(
        limit.amount == 120 and limit.granularity.name == "minute"
        for limit in limiter._default_limits
    )
