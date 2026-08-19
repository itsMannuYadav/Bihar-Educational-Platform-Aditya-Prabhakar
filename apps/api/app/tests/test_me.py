from fastapi.testclient import TestClient

from app.main import app


def test_me_requires_auth() -> None:
    response = TestClient(app).get("/api/v1/me")
    assert response.status_code == 401


def test_get_me_before_onboarding_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 404
    assert response.json()["detail"] == "profile_not_found"


def test_create_then_read_me(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/me", json={"name": "Anita Kumari", "preferredLanguage": "hinglish"}
    )
    assert create_res.status_code == 201
    body = create_res.json()
    assert body["name"] == "Anita Kumari"
    assert body["preferredLanguage"] == "hinglish"
    assert body["email"] == "teacher@example.com"
    assert body["role"] == "teacher"

    read_res = client.get("/api/v1/me")
    assert read_res.status_code == 200
    assert read_res.json()["id"] == body["id"]


def test_create_me_accepts_snake_case_body_too(client: TestClient) -> None:
    """Request bodies accept either the field name or the camelCase alias —
    only responses are strictly camelCase. See app/schemas/base.py."""
    create_res = client.post(
        "/api/v1/me", json={"name": "Anita Kumari", "preferred_language": "hi"}
    )
    assert create_res.status_code == 201
    assert create_res.json()["preferredLanguage"] == "hi"


def test_create_me_twice_conflicts(client: TestClient) -> None:
    payload = {"name": "Anita Kumari", "preferredLanguage": "hi"}
    first = client.post("/api/v1/me", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/me", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"] == "profile_already_exists"
