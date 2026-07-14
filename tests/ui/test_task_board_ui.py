import pytest
from playwright.sync_api import Page, expect

from pages.task_board_page import TaskBoardPage
from utils.data_factory import unique_title


@pytest.mark.ui
@pytest.mark.smoke
def test_homepage_loads(page: Page) -> None:
    page.goto("/")

    # expect ממתין אוטומטית עד שהאלמנט גלוי, ואינו נכשל מיד אם הדף עדיין נטען.
    expect(page.get_by_role("heading", name="TaskBoard")).to_be_visible()
    expect(page.get_by_test_id("title-input")).to_be_visible()
    expect(page.get_by_test_id("priority-select")).to_be_visible()
    expect(page.get_by_test_id("add-button")).to_be_visible()
    # בדיקה שמוודאת שטבלת המשימות גלויה במסך לפי ה data-testid שלה
    expect(page.get_by_test_id("tasks-table")).to_be_visible()
    expect(page.get_by_test_id("priority-select")).to_have_value("medium")   
     #בדיקה שהרשימה מכילה אופציית בחירה של ALL
    expect(page.get_by_test_id("status-filter")).to_contain_text("all")
    
@pytest.mark.ui
def test_homepage_with_pom(page: Page) -> None:
    board = TaskBoardPage(page)
    board.open()

    expect(board.title_input).to_be_visible()
    expect(board.add_button).to_be_visible()
    expect(board.tasks_table).to_be_visible()
    #בדיקה שיש ערך ברירת באפשרויות בחירה מדיום
    expect(board.priority_select).to_have_value("medium")
    #בדיקה שהטבלה מופיע בדף
    expect(board.tasks_table).to_be_visible()
    #בדיקה שאופציית בחירה "כל" נמצאת ברשימה
    expect(board.status_filter).to_contain_text("all")

"""
הפרמטר 
board 
בבדיקה הוא התוצאה של הרצת הפיקסטור 
board 
מ-conftest.py.
 התפקיד של הפיקסטור הוא להכין את האובייקט ולפתוח את הדף
 , כדי שהבדיקה שלי תקבל אותו מוכן ותריץ את הטסטים
"""
@pytest.mark.ui
def test_homepage_with_use_fixture (board:TaskBoardPage):
    
    expect(board.title_input).to_be_visible()
    expect(board.add_button).to_be_visible()
    expect(board.tasks_table).to_be_visible()
    #בדיקה שיש ערך ברירת באפשרויות בחירה מדיום
    expect(board.priority_select).to_have_value("medium")
    #בדיקה שהטבלה מופיע בדף
    expect(board.tasks_table).to_be_visible()
    #בדיקה שאופציית בחירה "כל" נמצאת ברשימה
    expect(board.status_filter).to_contain_text("all")

@pytest.mark.ui
def test_add_task_appears_in_list(board: TaskBoardPage) -> None:
    title = unique_title("add")
    board.add_task(title, priority="high")

    expect(board.row_by_title(title)).to_be_visible()
    expect(board.priority_cell(title)).to_have_text("high")
    expect(board.status_cell(title)).to_have_text("todo")

#וידוא שסימון משימה כבוצעה מעדכן את הסטטוס שלה במערכת.
#וידוא שמשימה שסומנה כבוצעה מקבלת את העיצוב הוויזואלי המתאים (קו חוצה).
@pytest.mark.ui
def test_test_mark_task_as_done(board: TaskBoardPage) -> None:
    title = unique_title("complete")
    board.add_task(title, priority="high")
    board.mark_done(title)
    expect(board.status_cell(title)).to_have_text("done")
    expect(board.title_cell(title)).to_have_class("status-done")

#בדיקה לוידוי שמשימה שנמחקה אכן לא נמצאת 
@pytest.mark.ui
def test_delete_task_shows_empty_state(board: TaskBoardPage) -> None:
    title = unique_title("dell")
    board.add_task(title, priority="high")
    board.delete(title)
    expect(board.row_by_title(title)).to_be_hidden()
    expect(board.empty_state).to_be_visible()

#וידוא שמסנן הסטטוסים מציג אך ורק משימות שעונות על תנאי הסינון.
@pytest.mark.ui

def test_filter_by_status_done_shows_only_completed_tasks(board: TaskBoardPage) -> None:
    title1 = unique_title("complete and done")
    title2 = unique_title("complete")

    board.add_task(title1, priority="high")
    board.add_task(title2, priority="low")

    board.mark_done(title1)
    board.filter_by_status("done")
    expect(board.row_by_title(title1)).to_be_visible()
    expect(board.row_by_title(title2)).to_be_hidden()


#בדיקה שלילית לווידוא שהמערכת מונעת יצירת משימות לא תקינות ללא שם.
@pytest.mark.parametrize("invalid_title", [
    "",                
    "   ",           
    " ",    
])
@pytest.mark.ui
def test_add_task_with_empty_title_does_not_create_row(board: TaskBoardPage,invalid_title) -> None:
        #title = unique_title()
        board.add_task(invalid_title, priority="high")
        expect(board.row_by_title(invalid_title)).to_be_hidden()





    
