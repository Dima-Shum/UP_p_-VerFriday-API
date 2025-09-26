import sys
import os
from typing import Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QSpinBox, QComboBox, QDialogButtonBox, QMessageBox,
                             QApplication, QMainWindow)
from PyQt5 import QtWidgets

from API_client import APIClient
from App import Ui_MonitoringSystem

os.environ[
    'QT_QPA_PLATFORM_PLUGIN_PATH'] = r'C:\Users\Студент.44-9\AppData\Local\Programs\Python\Python312\Lib\site-packages\PyQt5\Qt5\plugins'


class StudentMonitoringApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MonitoringSystem()
        self.ui.setupUi(self)

        self.api_client = APIClient("http://localhost:8000")

        self.load_students()
        self.load_statistics()

        self.ui.DelStudentBtn.clicked.connect(self.delete_student)
        self.ui.AddStudentBtn.clicked.connect(self.show_add_student_dialog)
        self.ui.FindStudentBtn.clicked.connect(self.search_student)
        self.ui.FiltrByGroup.currentIndexChanged.connect(self.filter_by_group)
        self.ui.FiltrByScience.currentIndexChanged.connect(self.filter_by_science)

        self.load_groups_into_combo(self.ui.FiltrByGroup)
        self.load_sciences_into_combo(self.ui.FiltrByScience)

    def load_students(self, group_id: Optional[int] = None, science_id: Optional[int] = None):
        try:
            students = self.api_client.get_students(group_id, science_id)

            self.ui.TableStudent.setRowCount(0)
            self.ui.TableStudent.setRowCount(len(students))

            for row_idx, student in enumerate(students):
                self.ui.TableStudent.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(student.get('id', ''))))
                self.ui.TableStudent.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(student.get('fio', '')))
                self.ui.TableStudent.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(student.get('group_name', '')))
                self.ui.TableStudent.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(
                    str(student.get('curs_name', ''))))
                self.ui.TableStudent.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(student.get('science_name', '')))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def load_statistics(self):
        try:
            stats = self.api_client.get_statistics()
            self.ui.TotalStudentStat.setStyleSheet("color: white;")
            self.ui.TotalStudentStat.setText(f"Всего студентов: {stats['total_students']}")
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")

    def show_add_student_dialog(self):
        dialog = QDialog(self)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #2d3844;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: white;
                color: #2d3844;
                border: 2px solid #6a5acd;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #6a5acd;
            }
            QComboBox::down-arrow {
                color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #6a5acd;
                border: none;
                border-radius: 2px;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                color: white;
            }
            QPushButton {
                background-color: #6a5acd;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a4abc;
            }
            QPushButton:pressed {
                background-color: #4a3aac;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        dialog.setWindowTitle("Добавить нового студента")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        FIO_edit = QLineEdit()
        Group_edit = QComboBox()
        Curs_edit = QSpinBox()
        Curs_edit.setRange(1, 4)
        Science_edit = QComboBox()

        form_layout.addRow("ФИО студента:", FIO_edit)
        form_layout.addRow("Группа:", Group_edit)
        form_layout.addRow("Курс:", Curs_edit)
        form_layout.addRow("Научное направление:", Science_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        button_box.accepted.connect(lambda: self.add_student(
            dialog, FIO_edit.text(), Group_edit.currentData(),
            Curs_edit.value(), Science_edit.currentData()
        ))
        button_box.rejected.connect(dialog.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        self.load_groups_into_combo(Group_edit)
        self.load_sciences_into_combo(Science_edit)

        dialog.exec_()

    def add_student(self, dialog, FIO, group_id, curs_id, science_id):
        if not FIO:
            QMessageBox.warning(dialog, "Ошибка", "Введите ФИО студента.")
            return

        try:
            student_data = {
                "FIO": FIO,
                "Group_id": group_id,
                "Curs_id": curs_id,
                "Science_id": science_id
            }

            result = self.api_client.create_student(student_data)
            QMessageBox.information(dialog, "Успех", "Студент успешно добавлен")
            dialog.accept()
            self.load_students()
            self.load_statistics()

        except Exception as e:
            QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить студента: {str(e)}")

    def delete_student(self):
        selected_row = self.ui.TableStudent.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для удаления")
            return

        student_id = int(self.ui.TableStudent.item(selected_row, 0).text())

        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить профиль этого студента?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.api_client.delete_student(student_id)
                self.load_students()
                self.load_statistics()
                QMessageBox.information(self, "Успех", "Студент успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить профиль студента: {str(e)}")

    def load_groups_into_combo(self, combo_box):
        try:
            groups = self.api_client.get_groups()
            combo_box.clear()

            if combo_box == self.ui.FiltrByGroup:
                combo_box.addItem("-- Все группы --", None)

            for group in groups:
                combo_box.addItem(group.get('group_name', ''), group.get('id'))

        except Exception as e:
            print(f"Ошибка загрузки групп: {e}")

    def load_sciences_into_combo(self, combo_box):
        try:
            sciences = self.api_client.get_sciences()
            combo_box.clear()

            if combo_box == self.ui.FiltrByScience:
                combo_box.addItem("-- Все направления --", None)

            for science in sciences:
                # Используем правильные ключи
                combo_box.addItem(science.get('science_name', ''), science.get('id'))

        except Exception as e:
            print(f"Ошибка загрузки направлений: {e}")

    def search_student(self):
        search_text = self.ui.FindStudentLine.text().strip()

        if not search_text:
            self.load_students()
            return

        try:
            students = self.api_client.get_students()
            filtered_students = [s for s in students if search_text.lower() in s.get('fio', '').lower()]

            self.ui.TableStudent.setRowCount(0)
            self.ui.TableStudent.setRowCount(len(filtered_students))

            for row_idx, student in enumerate(filtered_students):
                self.ui.TableStudent.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(student.get('id', ''))))
                self.ui.TableStudent.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(student.get('fio', '')))
                self.ui.TableStudent.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(student.get('group_name', '')))
                self.ui.TableStudent.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(student.get('curs_name', ''))))
                self.ui.TableStudent.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(student.get('science_name', '')))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске: {str(e)}")

    def filter_by_group(self):
        group_id = self.ui.FiltrByGroup.currentData()
        science_id = self.ui.FiltrByScience.currentData()
        self.load_students(group_id, science_id)

    def filter_by_science(self):
        group_id = self.ui.FiltrByGroup.currentData()
        science_id = self.ui.FiltrByScience.currentData()
        self.load_students(group_id, science_id)


def run_gui():
    app = QApplication(sys.argv)
    window = StudentMonitoringApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
