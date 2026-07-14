import json

from playwright.sync_api import APIRequestContext

from utils.data_factory import task_payload


def test_task_lifecycle_via_api(api_request_context: APIRequestContext) -> None:
    payload = task_payload(priority="high")

    # יצירה, ומצופה 201 עם גוף JSON שמכיל את השדות שנשלחו
    created = api_request_context.post("/api/tasks", data=payload)
    assert created.status == 201
    body = created.json()
    assert body["title"] == payload["title"]
    assert body["priority"] == "high"
    assert body["status"] == "todo"
    task_id = body["id"]

    # קריאה, ומצופה 200 עם אותו מזהה
    fetched = api_request_context.get(f"/api/tasks/{task_id}")
    assert fetched.status == 200
    assert fetched.json()["id"] == task_id

    # עדכון חלקי דרך PATCH, ומצופה ש-status ישתנה
    updated = api_request_context.patch(f"/api/tasks/{task_id}", data={"status": "done"})
    assert updated.status == 200
    assert updated.json()["status"] == "done"

    # מחיקה, ומצופה 204, ולאחריה הקריאה מחזירה 404
    deleted = api_request_context.delete(f"/api/tasks/{task_id}")
    assert deleted.status == 204
    assert api_request_context.get(f"/api/tasks/{task_id}").status == 404

#Check that creating a task with an empty title returns with code 422
def test_create_task_with_empty_title_returns_422(api_request_context: APIRequestContext) -> None:
    payload = task_payload(title="        ")

    created = api_request_context.post("/api/tasks", data=payload)
    assert created.status == 422

#Incorrect priority test
def test_incorrect_priority_return_422(api_request_context: APIRequestContext) -> None:
        payload = task_payload(title="Incorrect priority", priority="urgen")
        created = api_request_context.post("/api/tasks", data=payload)
        assert created.status == 422

#Checking the JSON content after receiving a response
def test_JSON_structure(api_request_context) -> None:
    payload = task_payload(title="new task", priority="low")
    created = api_request_context.post("/api/tasks", data=payload)
    assert created.status == 201
    body = created.json()
    list_of_fields = ["id", "title", "priority", "status", "created_at"]
    for i in list_of_fields:
         assert i in body.keys()
#בדיקת בקשה למשימה שלא קיימת ןמחזירה סטטוס קוד 404
def test_for_non_existent_task_returns_404(api_request_context) -> None:
    payload = task_payload(title="new task", priority="low")
    created = api_request_context.post("/api/tasks",data=payload)
    body = created.json()
    task_id = body["id"]
    get = api_request_context.get(f"/api/tasks/{task_id*3}")    
    assert get.status == 404
  
#uv run pytest