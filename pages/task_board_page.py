from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class TaskBoardPage(BasePage):
    """מסך ניהול המשימות. מרכז את כל ה-locators והפעולות."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.title_input = page.get_by_test_id("title-input")
        self.priority_select = page.get_by_test_id("priority-select")
        self.add_button = page.get_by_test_id("add-button")
        self.status_filter = page.get_by_test_id("status-filter")
        self.tasks_table = page.get_by_test_id("tasks-table")
        self.tasks_body = page.get_by_test_id("tasks-body")
        self.empty_state = page.get_by_test_id("empty-state")

    def open(self) -> None:
        super().open("/")

    def add_task(self, title: str, priority: str = "medium") -> None:
        self.title_input.fill(title)
        self.priority_select.select_option(priority)
        self.add_button.click()

    def row_by_title(self, title: str) -> Locator:
        # השורה שתא הכותרת שלה תואם בדיוק לכותרת שניתנה
        return self.tasks_body.locator("tr").filter(
            has=self.page.get_by_text(title, exact=True)
        )

    def priority_cell(self, title: str) -> Locator:
        # סדר התאים: id, כותרת, priority, status, פעולות
        return self.row_by_title(title).locator("td").nth(2)

    def status_cell(self, title: str) -> Locator:
        return self.row_by_title(title).locator("td").nth(3)

    def mark_done(self, title: str) -> None:
        self.row_by_title(title).get_by_role("button", name="סיום").click()

    def delete(self, title: str) -> None:
        self.row_by_title(title).get_by_role("button", name="מחיקה").click()

    def filter_by_status(self, status: str) -> None:
        # ערך ריק מציג את כל המשימות
        self.status_filter.select_option(status)

    async def get_tasks_count(self) -> int:
        return await self.tasks_body.locator("tr").count()
    
    def get_header_cell(self, header_name: str):
        return self.tasks_table.get_by_role("columnheader", name=header_name)
    
    """
היתרון של מודל 
POM 
הוא בעיקר בתחזוקה.

אם השתנה משהו במבנה של ה 
HTML 
או שהשתנה מספר זהות או שם של לוקטור,
והטסטים שלי השתמשו והסתמכו ישירות על המבנה והמזהים שמצוינים ב 
HTML,
אז במצב של שינוי אני אצטרך לעבור בכל הטסטים שלי ולשנות כל מה שהשתמש
ישירות במבנה ובמזהים האלו.

פה ה 
POM 
חוסך לי את כל התחזוקה הזו. במקום אחד הכל מוגדר, והטסטים שולפים
את הכל מוכן משלב האתחול 
init. 
אם לוקטור משתנה, אני משנה את הקוד רק במקום
אחד באתחול וזה מה שהופך את התחזוקה ליעילה.

הבדיקות עצמן אינן צריכות להכיר לוקטורים מכיוון שהתפקיד שלהן הוא לבדוק
את הלוגיקה העסקית ואת התנהגות האפליקציה, ולא את המבנה הטכני של הדף.
הפרדה זו שומרת על קוד בדיקות קריא ונקי.
"""

    
