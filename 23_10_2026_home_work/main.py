import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QCheckBox, QListWidget,
QMessageBox, QComboBox,
QDialog,
)


class TaskManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager 2.0")
        self.resize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Список
        self.task_list = QListWidget()

        # Название задачи
        self.title_label = QLabel("Task")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название задачи")
        self.title_count = QLabel("Название: 0 символов")
        self.title_input.textChanged.connect(self.update_title_count)

        # Описание
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Описание задачи")

        # Выбор одного приоритета
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Low', 'Medium', "High"])
        self.priority_combo.setCurrentText('Medium')

        # Независимые настройки.
        self.important_checkbox = QCheckBox("Важная задача")
        self.notification_checkbox = QCheckBox("Отправить уведомление")
        # Кнопка диалога
        self.about_button = QPushButton("О программе")
        self.about_button.clicked.connect(self.show_about)
        # Кнопка удаления
        self.delete_button = QPushButton("Удалить задачу")
        self.delete_button.clicked.connect(self.delete_selected_task)
        # Кнопка очистки
        self.clear_button = QPushButton('Очистить список')
        self.clear_button.clicked.connect(self.clear_tasks)
        # Кнопка
        self.add_button = QPushButton("Добавить задачу")
        self.add_button.clicked.connect(self.add_task)

        self.status_label = QLabel("Готов к созданию задачи")

        # Порядок элементов
        layout.addWidget(self.title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(self.title_count)
        layout.addWidget(self.description_input)
        layout.addWidget(self.priority_combo)
        layout.addWidget(self.important_checkbox)
        layout.addWidget(self.notification_checkbox)
        layout.addWidget(self.add_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.task_list)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.about_button)
        layout.addWidget(self.status_label)
        self.setStyleSheet("""
                    QMainWindow, QWidget {
                        background-color: #20242b;
                        color: #f1f3f5;
                        font-size: 14px;
                    }

                    QLineEdit, QTextEdit, QListWidget, QComboBox {
                        background-color: #2c323c;
                        border: 1px solid #566173;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #365f9e;
                    }

                    QPushButton {
                        background-color: #365f9e;
                        color: white;
                        border: 1px solid #507bbd;
                        border-radius: 6px;
                        padding: 10px;
                    }

                    QPushButton:hover {
                        background-color: #4474ba;
                    }

                    QPushButton:pressed {
                        background-color: #294b80;
                    }

                    QListWidget::item {
                        padding: 6px;
                    }
                    QRadioButton::indicator {
                        width: 16px;
                        height: 16px;
                        border: 2px solid #aab4c3;
                        border-radius: 10px;
                        background-color: #20242b;
                    }

                    QRadioButton::indicator:checked {
                        background-color: #64b5f6;
                        border-color: #64b5f6;
                    }
                    QListWidget::item:selected {
                        background-color: #365f9e;
                        color: white;
                    }
                """)

    def add_task(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, 'Нет названия', 'Введите название задачи')
            return
        description = self.description_input.toPlainText()

        priority = self.priority_combo.currentText()

        important = self.important_checkbox.isChecked()
        notification = self.notification_checkbox.isChecked()

        self.task_list.addItem(f'Приоритет: {priority} \n'
                               f'Задача:{title}, описание: {description}\n'
                               f'{"Важная задача, " if important else "Неважная задача, "}'
                               f'{"отправить уведомление" if notification else "не отправлять уведомление"}')


        self.title_input.clear()
        self.description_input.clear()

        self.status_label.setText(f"Задач: {self.task_list.count()}")

        print("Название:", title)
        print("Описание:", description)
        print("Приоритет:", priority)
        print("Важная задача:", 'Да' if important else 'Нет')
        print("Отправить уведомление:", 'Да' if notification else 'Нет')

    def clear_tasks(self):
        if self.task_list.count() == 0:
            QMessageBox.information(self, 'Очистка списка', "Список пуст")
            return

        choice = QMessageBox.question(self, 'очистка списка', "Удалить все задачи ?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No,)
        if choice == QMessageBox.StandardButton.Yes:
            self.task_list.clear()
            self.status_label.setText('Задач 0')
    def update_title_count(self, text):
        self.title_count.setText(f'Название: {len(text)} символов')
    def delete_selected_task(self):
        row = self.task_list.currentRow()

        if row == -1:
            QMessageBox.warning(self, "Задача не выбрана", "Выберите задачу в списке")
            return
        choice = QMessageBox.question(
            self,
            "Удаление задачи",
            "Удалить выбранную задачу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.task_list.takeItem(row)
            self.status_label.setText(
                f"Задач: {self.task_list.count()}"
            )
    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('О программе')
        dialog.resize(350, 180)

        layout = QVBoxLayout(dialog)

        description = QLabel("Task Manager 2.0\n"
            "Приложение для управления задачами.\n"
            "Приоритеты, создание и удаление задач.\n\n"
            "Дополнительные пункты: A, B, C.")
        description.setWordWrap(True)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)

        layout.addWidget(description)
        layout.addWidget(close_button)

        dialog.exec()
app = QApplication(sys.argv)
window = TaskManagerWindow()
window.show()
sys.exit(app.exec())