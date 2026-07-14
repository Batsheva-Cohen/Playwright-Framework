import os
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests
from playwright.sync_api import APIRequestContext, Page, Playwright

from pages.task_board_page import TaskBoardPage
from utils.config import settings

_DB_FILE = Path(__file__).parent / "test_tasks.db"


def _server_is_up() -> bool:
    try:
        return requests.get(f"{settings.base_url}/api/health", timeout=1).status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def base_url() -> str:
    return settings.base_url


@pytest.fixture(scope="session", autouse=True)
def sut_server() -> Iterator[str]:
    # אם כבר רץ שרת חיצוני על אותה כתובת, משתמשים בו ולא מפעילים חדש.
    if _server_is_up():
        yield settings.base_url
        return

    env = os.environ.copy()
    env["TASKBOARD_DB"] = str(_DB_FILE)  # DB נפרד לבדיקות, כדי לא לגעת בנתוני אמת
    if _DB_FILE.exists():
        _DB_FILE.unlink()

    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", settings.host, "--port", str(settings.port),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 30
        while time.time() < deadline and not _server_is_up():
            time.sleep(0.5)
        if not _server_is_up():
            raise RuntimeError("ה-SUT לא עלה בזמן")
        yield settings.base_url
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(scope="session")
def api_request_context(
    playwright: Playwright, base_url: str
) -> Iterator[APIRequestContext]:
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture(autouse=True)
def clean_tasks(api_request_context: APIRequestContext) -> None:
    # בידוד: מחיקת כל המשימות לפני כל בדיקה, כדי שכל בדיקה תתחיל ממצב נקי.
    for task in api_request_context.get("/api/tasks").json():
        api_request_context.delete(f"/api/tasks/{task['id']}")


@pytest.fixture
def board(page: Page) -> TaskBoardPage:
    board = TaskBoardPage(page)
    board.open()
    return board

@pytest.fixture(scope="session")
def auth_token(api_request_context: APIRequestContext) -> str:
    response = api_request_context.post(
        "/auth/login",
        data={"username": settings.username, "password": settings.password},
    )
    assert response.status == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}

