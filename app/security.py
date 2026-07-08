"""רכיבי אבטחה ל-SUT: הנפקת JWT לאימות והצפנה סימטרית עם Fernet.

הסודות מגיעים ממשתני סביבה כדי שמספר אינסטנסים מאחורי load balancer יחלקו
את אותו מפתח. ערכי ברירת המחדל כאן מיועדים לפיתוח בלבד ואין להשתמש בהם בייצור.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-please-change-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 30

# מפתח Fernet תקין (urlsafe base64 של 32 בתים). לפיתוח בלבד.
FERNET_KEY = os.environ.get("FERNET_KEY", "-8UT8zApukRqSldTedZZlFN6J1SpCkuyYobXz_qwvtM=")

# מזהה האינסטנס, נחשף דרך /api/whoami כדי לראות איזה שרת ענה מאחורי ה-load balancer.
INSTANCE_ID = os.environ.get("INSTANCE_ID", "local")

# פרטי התחברות לדוגמה. במערכת אמת המשתמשים נשמרים ב-DB עם סיסמאות מגובבות.
DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "demo123")

_fernet = Fernet(FERNET_KEY.encode())


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()