import os
from collections.abc import Iterator

import pytest
import requests
from playwright.sync_api import APIRequestContext, Playwright

LB_URL = os.environ.get("LB_URL", "http://localhost:8080")


def _lb_is_up() -> bool:
    try:
        return requests.get(f"{LB_URL}/api/health", timeout=1).status_code == 200
    except requests.RequestException:
        return False


# כל הבדיקות בקובץ מסומנות distributed, ומדלגות אם ה-load balancer אינו רץ
pytestmark = [
    pytest.mark.distributed,
    pytest.mark.skipif(
        not _lb_is_up(), reason="ה-load balancer אינו רץ, יש להריץ docker compose up"
    ),
]


@pytest.fixture(scope="module")
def lb_context(playwright: Playwright) -> Iterator[APIRequestContext]:
    context = playwright.request.new_context(base_url=LB_URL)
    yield context
    context.dispose()


def test_requests_distributed_across_instances(lb_context: APIRequestContext) -> None:
    seen = set()
    for _ in range(10):
        seen.add(lb_context.get("/api/whoami").json()["instance"])
    # שני אינסטנסים לפחות ענו, כלומר הבקשות מתפזרות
    assert len(seen) >= 2


def test_data_consistent_across_instances(lb_context: APIRequestContext) -> None:
    created = lb_context.post("/api/tasks", data={"title": "lb-task", "priority": "high"})
    assert created.status == 201
    task_id = created.json()["id"]

    # הקריאה עשויה להגיע לאינסטנס אחר, אך הנתון משותף דרך ה-DB
    fetched = lb_context.get(f"/api/tasks/{task_id}")
    assert fetched.status == 200
    assert fetched.json()["title"] == "lb-task"


def test_token_valid_across_instances(lb_context: APIRequestContext) -> None:
    login = lb_context.post(
        "/auth/login", data={"username": "demo", "password": "demo123"}
    )
    token = login.json()["access_token"]

    # ה-token הונפק על ידי אינסטנס כלשהו, ונבדק אולי על ידי אחר, אך הסוד משותף
    me = lb_context.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status == 200

def test_multiple_tasks_consistent_across_instances(lb_context: APIRequestContext,) -> None:
    list_ids_tasks = []
    for i in range(5):
        created = lb_context.post("/api/tasks", data={"title": f'lb-task{i}', "priority": "high"})
        assert created.status == 201
        list_ids_tasks.append(created.json()["id"])

    list_all_ids = []

    get_all = lb_context.get("/api/tasks").json()
    for task in get_all:
        list_all_ids.append(task["id"])

    for id in list_ids_tasks:
        assert id in list_all_ids, f"Task {id} missing from task list"
        




