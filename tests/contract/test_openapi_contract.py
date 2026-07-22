from playwright.sync_api import APIRequestContext

EXPECTED_PATHS = {
    "/api/health",
    "/api/whoami",
    "/auth/login",
    "/api/me",
    "/api/tasks",
    "/api/tasks/{task_id}",
    "/api/secure-notes",
    "/api/secure-notes/{note_id}",
}


def test_openapi_declares_expected_paths(api_request_context: APIRequestContext) -> None:
    spec = api_request_context.get("/openapi.json").json()
    declared = set(spec["paths"].keys())
    missing = EXPECTED_PATHS - declared
    assert not missing, f"endpoints חסרים בחוזה: {missing}"


def test_task_schema_declares_expected_fields(api_request_context: APIRequestContext) -> None:
    spec = api_request_context.get("/openapi.json").json()
    task_schema = spec["components"]["schemas"]["Task"]
    expected = {"id", "title", "description", "status", "priority", "created_at"}
    assert set(task_schema["required"]) == expected


def test_protected_endpoints_declare_security(api_request_context: APIRequestContext) -> None:
    spec = api_request_context.get("/openapi.json").json()
    # שיטת האימות מוצהרת ברמת המסמך
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
    # ו-endpoint מוגן מצהיר עליה במפורש
    assert spec["paths"]["/api/me"]["get"]["security"] == [{"HTTPBearer": []}]

#בדיקה שמוודאת שהתשובות בפועל תואמות לחוזה
def test_get_tasks_response_contains_all_required_fields(api_request_context: APIRequestContext) -> None:
        spec = api_request_context.get("/openapi.json").json()
        required_fields = set(spec["components"]["schemas"]["Task"]["required"])

        response = api_request_context.get("/api/tasks")
        assert response.status_code == 200
        tasks = response.json()

        for task in tasks:
            missing = required_fields - set(task.keys())
            assert not missing, f"Task {task.get('id')} is missing required fields: {missing}"





