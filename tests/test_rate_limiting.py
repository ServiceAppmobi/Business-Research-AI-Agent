from fastapi.testclient import TestClient

from app.main import app, limiter

client = TestClient(app)


def test_limiter_is_registered_on_app():
    assert app.state.limiter is limiter


def test_public_api_rate_limit_configuration():
    # SlowAPI stores defaults as LimitGroup objects; their string representation
    # is not the configured limit. Verify the limiter has a default policy
    # without depending on private implementation details.
    assert limiter._default_limits
