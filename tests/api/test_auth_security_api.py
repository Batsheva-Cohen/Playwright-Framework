import pytest
from playwright.sync_api import APIRequestContext

from app.main import NoteCreate, create_note
from app.security import create_access_token, decrypt, encrypt
from utils.config import settings


@pytest.mark.api
@pytest.mark.auth
@pytest.mark.smoke
def test_login_returns_token(api_request_context: APIRequestContext) -> None:
    response = api_request_context.post(
        "/auth/login",
        data={"username": settings.username, "password": settings.password},
    )
    assert response.status == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

@pytest.mark.api
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
@pytest.mark.api
def test_invalid_credentials(api_request_context: APIRequestContext) -> None:
    response = api_request_context.post(
        "/auth/login",
        data={"username": "valid_username", "password": "valid_password"},        
    )
    assert response.status == 401

# test with valid token return status code 401
@pytest.mark.api
@pytest.mark.auth
def test_invalid_token(api_request_context: APIRequestContext) -> None:
    auth_token = "garbage"
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    response = api_request_context.get("/api/me", headers=auth_headers)
    assert response.status == 401

# יצירת טקסט להצפנה ובדיקה שהוא אכן מצליח להצפין ולפענח בחזרה
@pytest.mark.api
@pytest.mark.auth
def test_secure_notes_API(api_request_context: APIRequestContext):
    my_token = create_access_token(settings.username)
    payload = NoteCreate(content="the secret password is 1234")
    create_my_note = create_note(payload, settings.username)
    response = api_request_context.post(
        "/api/secure-notes",
        headers={
            "Authorization": f"Bearer {my_token}",
        },
        data={"content": create_my_note["content"]}

    )
    assert response.status == 201

    encrypted_message = encrypt(create_my_note["content"])
    decrypted_message = decrypt(encrypted_message)

    assert encrypted_message != create_my_note["content"]  
    assert decrypted_message == create_my_note["content"] 

# בדיקה שליחת בקשת הצפנה ללא טוקן מחזירה 401
@pytest.mark.api
@pytest.mark.auth
def test_create_note_unauthorized(api_request_context: APIRequestContext):
    payload = NoteCreate(content="the secret password is 1234")
    my_token = ""
    create_my_note = create_note(payload, settings.username)
    response = api_request_context.post(
        "/api/secure-notes",
        headers={
            "Authorization": f"Bearer {my_token}",
        },
        data={"content": create_my_note["content"]}
        )
    assert response.status == 401
