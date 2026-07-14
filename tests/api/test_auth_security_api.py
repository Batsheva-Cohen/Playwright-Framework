from playwright.sync_api import APIRequestContext

from utils.config import settings


def test_login_returns_token(api_request_context: APIRequestContext) -> None:
    response = api_request_context.post(
        "/auth/login",
        data={"username": settings.username, "password": settings.password},
    )
    assert response.status == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_me_requires_valid_token(
    api_request_context: APIRequestContext, auth_headers: dict[str, str]
) -> None:
    # ללא token, מצופה 401
    assert api_request_context.get("/api/me").status == 401

    # עם token תקין, מצופה 200 והמשתמש הנכון
    response = api_request_context.get("/api/me", headers=auth_headers)
    assert response.status == 200
    assert response.json()["username"] == settings.username

#בדיקה שהתחברות עם פרטים שגויים מוחזרת עם קוד 401.
def test_invalid_credentials(api_request_context: APIRequestContext) -> None:
    response = api_request_context.post(
        "/auth/login",
        data={"username": "valid_username", "password": "valid_password"},        
    )
    assert response.status == 401

# test with valid token return status code 401
def test_invalid_token(api_request_context: APIRequestContext) -> None:
    auth_token = "garbage"
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    response = api_request_context.get("/api/me", headers=auth_headers)
    assert response.status == 401

# uv run pytest