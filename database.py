import sqlite3
from datetime import datetime, date

class Database:
    def __init__(self):
        self.con = sqlite3.connect('todo.db')
        self.cursor = self.con.cursor()
        self.create_task_table()

    def create_task_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                task TEXT NOT NULL, 
                due_date TEXT, 
                completed INTEGER NOT NULL CHECK (completed IN (0, 1))
            )
        """)
        self.con.commit()

    def create_task(self, task, due_date=None):
        if due_date:
            due_date = datetime.strptime(due_date, '%A %d %B %Y').strftime('%Y-%m-%d')
        self.cursor.execute("INSERT INTO tasks(task, due_date, completed) VALUES(?, ?, ?)", (task, due_date, 0))
        self.con.commit()
        created_task = self.cursor.lastrowid, task, due_date
        print(f"Created task: {created_task}")  # Debug print
        return created_task

    def get_tasks(self):
        today = date.today().strftime('%Y-%m-%d')
        print(f"Today's date: {today}")  # Debug print
        today_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0 AND date(due_date) = date(?)", (today,)).fetchall()
        delayed_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0 AND date(due_date) < date(?)", (today,)).fetchall()
        upcoming_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0 AND date(due_date) > date(?)", (today,)).fetchall()
        completed_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 1").fetchall()
        print(f"Today's tasks: {today_tasks}")  # Debug print
        print(f"Delayed tasks: {delayed_tasks}")  # Debug print
        print(f"Upcoming tasks: {upcoming_tasks}")  # Debug print
        print(f"Completed tasks: {completed_tasks}")  # Debug print
        return today_tasks, delayed_tasks, upcoming_tasks, completed_tasks

    def mark_task_as_complete(self, taskid):
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=?", (taskid,))
        self.con.commit()

    def mark_task_as_incomplete(self, taskid):
        self.cursor.execute("UPDATE tasks SET completed=0 WHERE id=?", (taskid,))
        self.con.commit()
        task_text = self.cursor.execute("SELECT task FROM tasks WHERE id=?", (taskid,)).fetchone()
        return task_text[0] if task_text else None

    def delete_task(self, taskid):
        self.cursor.execute("DELETE FROM tasks WHERE id=?", (taskid,))
        self.con.commit()

    def close_db_connection(self):
        self.con.close()

    def get_task(self, taskid):
        return self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE id=?", (taskid,)).fetchone()

    def search_tasks(self, search_text):
        search_pattern = f"%{search_text}%"
        return self.cursor.execute("""
            SELECT id, task, due_date, completed
            FROM tasks
            WHERE task LIKE ?
        """, (search_pattern,)).fetchall()