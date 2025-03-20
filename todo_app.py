import sys
import os
import sqlite3
from datetime import datetime, timedelta
from functools import partial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QDateTimeEdit, QMessageBox, QAbstractItemView)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon, QFont

# Database setup
def create_database():
    """Create SQLite database and tasks table if they don't exist"""
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_datetime TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        completed_datetime TEXT,
        created_date TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

class TodoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle('待办事项管理工具')
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header_layout = QHBoxLayout()
        header_label = QLabel('今日待办事项')
        header_label.setFont(QFont('Arial', 16, QFont.Bold))
        header_layout.addWidget(header_label)
        main_layout.addLayout(header_layout)
        
        # Create task input area
        input_layout = QHBoxLayout()
        
        # Task title input
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText('输入新的待办事项...')
        input_layout.addWidget(self.task_input, 3)
        
        # Due datetime picker
        self.due_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.due_datetime.setDisplayFormat('yyyy-MM-dd HH:mm')
        self.due_datetime.setCalendarPopup(True)
        input_layout.addWidget(QLabel('添加时间:'), 1)
        input_layout.addWidget(self.due_datetime, 2)
        
        # Add task button
        add_button = QPushButton('添加任务')
        add_button.clicked.connect(self.add_task)
        input_layout.addWidget(add_button, 1)
        
        main_layout.addLayout(input_layout)
        
        # Create tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(['任务', '添加时间', '状态', '完成时间', '操作'])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        main_layout.addWidget(self.tasks_table)
        
        # Create bottom buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton('刷新任务列表')
        refresh_button.clicked.connect(self.load_tasks)
        button_layout.addWidget(refresh_button)
        
        clear_completed_button = QPushButton('清除已完成任务')
        clear_completed_button.clicked.connect(self.clear_completed_tasks)
        button_layout.addWidget(clear_completed_button)
        
        main_layout.addLayout(button_layout)
        
        # Load tasks from database
        self.load_tasks()
    
    def add_task(self):
        """Add a new task to the database"""
        task_title = self.task_input.text().strip()
        if not task_title:
            QMessageBox.warning(self, '警告', '任务内容不能为空！')
            return
        
        due_datetime = self.due_datetime.dateTime().toString('yyyy-MM-dd HH:mm')
        created_date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect('todo.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tasks (title, due_datetime, created_date) VALUES (?, ?, ?)',
                (task_title, due_datetime, created_date)
            )
            conn.commit()
        
        self.task_input.clear()
        self.due_datetime.setDateTime(QDateTime.currentDateTime())
        self.load_tasks()
        
    def load_tasks(self):
        """Load tasks from database and display in table"""
        # First check if any tasks need to be moved to today
        self.move_incomplete_tasks()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect('todo.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, title, due_datetime, completed, completed_datetime FROM tasks WHERE created_date = ?',
                (today,)
            )
            tasks = cursor.fetchall()
        
        # Clear and set up table
        self.tasks_table.setRowCount(0)
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            task_id, title, due_datetime, completed, completed_datetime = task
            
            # Task title
            self.tasks_table.setItem(row, 0, QTableWidgetItem(title))
            
            # Due datetime
            self.tasks_table.setItem(row, 1, QTableWidgetItem(due_datetime))
            
            # Status
            status = '已完成' if completed else '未完成'
            status_item = QTableWidgetItem(status)
            if completed:
                status_item.setBackground(Qt.green)
            else:
                # Check if task is overdue
                due_dt = datetime.strptime(due_datetime, '%Y-%m-%d %H:%M')
                if due_dt < datetime.now():
                    status_item.setBackground(Qt.red)
            self.tasks_table.setItem(row, 2, status_item)
            
            # Completed datetime
            completed_text = completed_datetime if completed_datetime else ''
            self.tasks_table.setItem(row, 3, QTableWidgetItem(completed_text))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            if not completed:
                complete_button = QPushButton('完成')
                complete_button.clicked.connect(partial(self.mark_completed, task_id))
                action_layout.addWidget(complete_button)
            
            delete_button = QPushButton('删除')
            delete_button.clicked.connect(partial(self.delete_task, task_id))
            action_layout.addWidget(delete_button)
            
            action_widget.setLayout(action_layout)
            self.tasks_table.setCellWidget(row, 4, action_widget)
    
    def mark_completed(self, task_id):
        """Mark a task as completed"""
        completed_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        with sqlite3.connect('todo.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tasks SET completed = 1, completed_datetime = ? WHERE id = ?',
                (completed_datetime, task_id)
            )
            conn.commit()
        
        self.load_tasks()
    
    def delete_task(self, task_id):
        """Delete a task from the database"""
        confirm = QMessageBox.question(
            self, '确认删除', '确定要删除这个任务吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            with sqlite3.connect('todo.db') as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.commit()
            
            self.load_tasks()
    
    def clear_completed_tasks(self):
        """Clear all completed tasks"""
        confirm = QMessageBox.question(
            self, '确认清除', '确定要清除所有已完成的任务吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            with sqlite3.connect('todo.db') as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE completed = 1')
                conn.commit()
            
            self.load_tasks()
    
    def move_incomplete_tasks(self):
        """Move incomplete tasks from previous days to today"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        with sqlite3.connect('todo.db') as conn:
            cursor = conn.cursor()
            
            # Find incomplete tasks from previous days
            cursor.execute(
                'SELECT id FROM tasks WHERE created_date < ? AND completed = 0',
                (today,)
            )
            tasks = cursor.fetchall()
            
            # Update their created_date to today
            for task_id in tasks:
                cursor.execute(
                    'UPDATE tasks SET created_date = ? WHERE id = ?',
                    (today, task_id[0])
                )
            
            conn.commit()

def main():
    # Create database if it doesn't exist
    create_database()
    
    # Start application
    app = QApplication(sys.argv)
    window = TodoApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()