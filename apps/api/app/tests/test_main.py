import uuid
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_claims, get_db
from app.core.security import SupabaseClaims
from app.main import app


def test_unhandled_exception_response_still_has_cors_headers() -> None:
    """A bare `@app.exception_handler(Exception)` looks like it fixes this but
    doesn't — FastAPI wires it to Starlette's ServerErrorMiddleware, which
    sits *outside* CORSMiddleware and sends its response without ever
    passing back through it. Reproduces the real-world symptom: the backend
    logs show a clean 500 (e.g. a transient DB connection failure), but the
    browser reports it as a CORS policy violation, masking the real cause.
    """

    def fake_claims() -> SupabaseClaims:
        return SupabaseClaims(
            supabase_auth_id=uuid.uuid4(), email="teacher@example.com", phone=None
        )

    async def broken_get_db() -> AsyncGenerator[None]:
        raise RuntimeError("simulated unhandled failure (e.g. DB connection drop)")
        yield  # pragma: no cover - unreachable, makes this an async generator

    app.dependency_overrides[get_current_claims] = fake_claims
    app.dependency_overrides[get_db] = broken_get_db
    try:
        response = TestClient(app, raise_server_exceptions=False).get(
            "/api/v1/me",
            headers={"Origin": "http://localhost:3000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.parametrize("origin", ["http://localhost:3000"])
def test_normal_error_response_still_has_cors_headers(origin: str) -> None:
    """Sanity check the fix didn't disturb the ordinary (non-crashing) path."""
    response = TestClient(app).get("/api/v1/me", headers={"Origin": origin})
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == origin
