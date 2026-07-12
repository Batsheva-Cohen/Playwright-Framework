from playwright.sync_api import Page, expect

from pages.task_board_page import TaskBoardPage

# web-first assertion,
    # מונע בדיקות שבירות כי הוא חוסך לי את הניהול של כל מה שקרה כשהדף נטען וכל הכפתורים נטענים ועולים 
    # וכל הבדיקות על הכפתורים שלי לא מתחילות עד שכל המסך עולה מה שחוסך לי את כל הנפילות האלה כששוכחים לשים 
    # sleep 
    # או שזמן ההמתנה לא היה מספיק כדי שהוא יעלה לרקע והבדיקה התחילה על כפתור שלא נמצא 

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






    
