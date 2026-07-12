from playwright.sync_api import Page


class BasePage:
    """בסיס לכל מסך. מחזיק את הפניה ל-page ופעולות משותפות."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self, path: str = "/") -> None:
        self.page.goto(path)