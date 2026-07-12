import time


def unique_title(prefix: str = "task") -> str:
    """כותרת ייחודית, כדי ששתי בדיקות לא יתנגשו על אותו טקסט."""
    return f"{prefix}-{time.time_ns()}"


def task_payload(
    title: str | None = None,
    priority: str = "medium",
    status: str = "todo",
) -> dict:
    return {
        "title": title or unique_title(),
        "priority": priority,
        "status": status,
    }