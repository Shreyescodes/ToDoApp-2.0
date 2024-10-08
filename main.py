import platform
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker
from datetime import datetime, date
from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import ListProperty
from kivymd.uix.button import MDFlatButton
import logging
from kivymd.uix.menu import MDDropdownMenu

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import permissions for Android
if platform.system() == "Android":
    from android.permissions import request_permissions, Permission  # type: ignore
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

from database import Database

# Initialize db instance
db = Database()

class ListItemWithCheckbox(TwoLineAvatarIconListItem):
    bg_color = ListProperty([0, 0, 0, 0])  # Transparent by default

    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        self.pk = pk

    def mark(self, check, the_list_item):
        if check.active:
            the_list_item.text = '[s]' + the_list_item.text + '[/s]'
            db.mark_task_as_complete(the_list_item.pk)
            self.parent.remove_widget(the_list_item)
            app.root.ids.completed_container.add_widget(the_list_item)
        else:
            the_list_item.text = db.mark_task_as_incomplete(the_list_item.pk)
            self.parent.remove_widget(the_list_item)
            app.add_task_to_list(db.get_task(the_list_item.pk))

    def delete_item(self, the_list_item):
        self.parent.remove_widget(the_list_item)
        db.delete_task(the_list_item.pk)

class LeftCheckbox(ILeftBodyTouch, MDCheckbox):
    pass

class DialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.date_text.text = str(datetime.now().strftime('%A %d %B %Y'))

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()

    def on_save(self, instance, value, date_range):
        date = value.strftime('%A %d %B %Y')
        self.ids.date_text.text = str(date)

class SearchDialog(MDBoxLayout):
    pass

class MainApp(MDApp):
    task_list_dialog = None
    search_dialog = None
    menu = None

    def build(self):
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.accent_palette = "Red"
        self.theme_cls.accent_hue = "500"
        
        # Create the dropdown menu
        menu_items = [
            {
                "text": f"{i}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=i: self.menu_callback(x),
            } for i in ["Today's Tasks", "Delayed Tasks", "Upcoming Tasks", "Completed Tasks"]
        ]
        self.menu = MDDropdownMenu(
            caller=self.root.ids.dropdown_button,
            items=menu_items,
            width_mult=4,
        )

    def menu_callback(self, text_item):
        self.root.ids.dropdown_button.text = text_item
        self.menu.dismiss()
        
        if text_item == "Today's Tasks":
            self.show_today_tasks()
        elif text_item == "Delayed Tasks":
            self.show_delayed_tasks()
        elif text_item == "Upcoming Tasks":
            self.show_upcoming_tasks()
        elif text_item == "Completed Tasks":
            self.show_completed_tasks()

    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Create New Task",
                type="custom",
                content_cls=DialogContent(),
                auto_dismiss=False
            )
        self.task_list_dialog.open()

    def close_dialog(self, *args):
        self.task_list_dialog.dismiss()

    def add_task(self, task, task_date):
        logger.debug(f"Adding task: {task.text}, Date: {task_date}")
        created_task = db.create_task(task.text, task_date)
        logger.debug(f"Created task: {created_task}")
        self.add_task_to_list(created_task)
        task.text = ''

    def add_task_to_list(self, task):
        logger.debug(f"Adding task to list: {task}")
        due_date = datetime.strptime(task[2], '%Y-%m-%d').date() if task[2] else None
        today = date.today()
        
        list_item = ListItemWithCheckbox(pk=task[0], text='[b]' + task[1] + '[/b]', secondary_text=str(task[2]))
        
        if due_date == today:
            logger.debug(f"Adding to today's tasks: {task}")
            self.root.ids.today_container.add_widget(list_item)
        elif due_date and due_date < today:
            logger.debug(f"Adding to delayed tasks: {task}")
            self.root.ids.delayed_container.add_widget(list_item)
        elif due_date and due_date > today:
            logger.debug(f"Adding to upcoming tasks: {task}")
            self.root.ids.upcoming_container.add_widget(list_item)
        else:
            logger.debug(f"Adding to today's tasks (no date): {task}")
            self.root.ids.today_container.add_widget(list_item)

    def show_today_tasks(self):
        logger.debug("Showing today's tasks")
        self.root.ids.today_tasks_view.height = 400
        self.root.ids.delayed_tasks_view.height = 0
        self.root.ids.upcoming_tasks_view.height = 0
        self.root.ids.completed_tasks_view.height = 0

    def show_delayed_tasks(self):
        logger.debug("Showing delayed tasks")
        self.root.ids.today_tasks_view.height = 0
        self.root.ids.delayed_tasks_view.height = 400
        self.root.ids.upcoming_tasks_view.height = 0
        self.root.ids.completed_tasks_view.height = 0

    def show_upcoming_tasks(self):
        logger.debug("Showing upcoming tasks")
        self.root.ids.today_tasks_view.height = 0
        self.root.ids.delayed_tasks_view.height = 0
        self.root.ids.upcoming_tasks_view.height = 400
        self.root.ids.completed_tasks_view.height = 0

    def show_completed_tasks(self):
        logger.debug("Showing completed tasks")
        self.root.ids.today_tasks_view.height = 0
        self.root.ids.delayed_tasks_view.height = 0
        self.root.ids.upcoming_tasks_view.height = 0
        self.root.ids.completed_tasks_view.height = 400

    def show_search_dialog(self):
        if not self.search_dialog:
            self.search_dialog = MDDialog(
                title="Search Tasks",
                type="custom",
                content_cls=SearchDialog(),
            )
        self.search_dialog.open()

    def close_search_dialog(self, *args):
        self.search_dialog.dismiss()

    def search_task(self, search_text):
        self.close_search_dialog()
        search_results = db.search_tasks(search_text)
        
        # Reset all task backgrounds
        for container in [self.root.ids.today_container, self.root.ids.delayed_container, 
                          self.root.ids.upcoming_container, self.root.ids.completed_container]:
            for task in container.children:
                task.bg_color = [0, 0, 0, 0]  # Transparent
        
        if search_results:
            for result in search_results:
                task_id, task_text, due_date, completed = result
                for container in [self.root.ids.today_container, self.root.ids.delayed_container, 
                                  self.root.ids.upcoming_container, self.root.ids.completed_container]:
                    for task in container.children:
                        if task.pk == task_id:
                            task.bg_color = self.theme_cls.primary_light
        else:
            self.show_search_not_found_dialog()

    def show_search_not_found_dialog(self):
        not_found_dialog = MDDialog(
            title="Search Result",
            text="No tasks found matching your search criteria.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: not_found_dialog.dismiss()
                )
            ]
        )
        not_found_dialog.open()

    def on_start(self):
        try:
            today_tasks, delayed_tasks, upcoming_tasks, completed_tasks = db.get_tasks()

            logger.debug(f"Today's tasks: {today_tasks}")
            logger.debug(f"Delayed tasks: {delayed_tasks}")
            logger.debug(f"Upcoming tasks: {upcoming_tasks}")
            logger.debug(f"Completed tasks: {completed_tasks}")

            for task in today_tasks:
                self.add_task_to_list(task)

            for task in delayed_tasks:
                self.add_task_to_list(task)

            for task in upcoming_tasks:
                self.add_task_to_list(task)

            for task in completed_tasks:
                add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + task[1] + '[/s]', secondary_text=str(task[2]))
                add_task.ids.check.active = True
                self.root.ids.completed_container.add_widget(add_task)

            # Initially, show the today's tasks
            self.show_today_tasks()
            self.root.ids.dropdown_button.text = "Today's Tasks"

        except Exception as e:
            logger.exception(f"Error in on_start: {e}")

if __name__ == '__main__':
    app = MainApp()
    app.run()
