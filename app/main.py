"""TaskBoard API - מערכת ניהול משימות לצורכי תרגול אוטומציה.

המערכת חושפת REST API מלא עם תיעוד Swagger, ממשק Web פשוט, אימות מבוסס JWT,
שמירת נתונים מוצפנים, ו-endpoint לזיהוי האינסטנס מאחורי load balancer.
מיועדת לשמש כ-System Under Test (SUT) במשימת אוטומציה לתפקיד QA Automation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from app.db import get_connection, init_db, now_iso
from app.security import (
    DEMO_PASSWORD,
    DEMO_USERNAME,
    INSTANCE_ID,
    TOKEN_TTL_MINUTES,
    create_access_token,
    decode_access_token,
    decrypt,
    encrypt,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token") from None
    return str(payload["sub"])


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    status: Status = Status.todo
    priority: Priority = Priority.medium

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value.strip()


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    status: Status | None = None
    priority: Priority | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    created_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="TaskBoard API", version="2.0.0", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/whoami")
def whoami() -> dict[str, str]:
    return {"instance": INSTANCE_ID}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> dict:
    if payload.username != DEMO_USERNAME or payload.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(payload.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_MINUTES * 60,
    }


@app.get("/api/me")
def me(user: str = Depends(current_user)) -> dict[str, str]:
    return {"username": user}


@app.post("/api/secure-notes", response_model=NoteResponse, status_code=201)
def create_note(payload: NoteCreate, user: str = Depends(current_user)) -> dict:
    created_at = now_iso()
    encrypted = encrypt(payload.content)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO notes (content_encrypted, created_at) VALUES (?, ?)",
            (encrypted, created_at),
        )
        conn.commit()
        note_id = cursor.lastrowid
    return {"id": note_id, "content": payload.content, "created_at": created_at}


@app.get("/api/secure-notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, user: str = Depends(current_user)) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, content_encrypted, created_at FROM notes WHERE id = ?",
            (note_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return {
        "id": row["id"],
        "content": decrypt(row["content_encrypted"]),
        "created_at": row["created_at"],
    }


@app.get("/api/tasks", response_model=list[Task])
def list_tasks(
    status: Status | None = Query(default=None),
    priority: Priority | None = Query(default=None),
) -> list[dict]:
    query = "SELECT * FROM tasks"
    clauses: list[str] = []
    params: list[str] = []
    if status is not None:
        clauses.append("status = ?")
        params.append(status.value)
    if priority is not None:
        clauses.append("priority = ?")
        params.append(priority.value)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id ASC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="task not found")
    return dict(row)


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate) -> dict:
    created_at = now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, status, priority, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                payload.title,
                payload.description,
                payload.status.value,
                payload.priority.value,
                created_at,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    return dict(row)


@app.patch("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> dict:
    fields = payload.model_dump(exclude_none=True)
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="task not found")
        if fields:
            normalized = {
                key: (value.value if isinstance(value, Enum) else value)
                for key, value in fields.items()
            }
            assignments = ", ".join(f"{key} = ?" for key in normalized)
            values = list(normalized.values()) + [task_id]
            conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
            conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="task not found")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()