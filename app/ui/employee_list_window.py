"""
Окно списка сотрудников.

Окно отображает сотрудников из базы данных с учетом роли пользователя.
Администратор видит всех, руководитель — сотрудников своего отдела,
сотрудник — только собственную карточку.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthenticatedUser
from app.services.employee_service import EmployeeListItem, EmployeeService
from app.ui.employee_detail_window import EmployeeDetailWindow



class EmployeeListWindow(QDialog):
    """
    Окно со списком сотрудников.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно списка сотрудников.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.employees: list[EmployeeListItem] = []

        self.setWindowTitle("KPI Monitor ML — сотрудники")
        self.resize(1000, 600)

        self._create_interface()
        self._load_employees()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Список сотрудников")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            f"Текущая роль: {self.current_user.role_name}. "
            "Список отображается с учетом прав доступа."
        )
        description_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Табельный номер",
                "ФИО",
                "Отдел",
                "Должность",
                "Email",
                "Активен",
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._open_selected_employee)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._load_employees)

        open_button = QPushButton("Открыть карточку")
        open_button.clicked.connect(self._open_selected_employee)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        button_layout.addWidget(refresh_button)
        button_layout.addWidget(open_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _load_employees(self) -> None:
        """
        Загружает сотрудников из базы данных и выводит их в таблицу.
        """
        session = SessionLocal()

        try:
            service = EmployeeService(session)
            self.employees = service.get_employees_for_user(self.current_user)

        finally:
            session.close()

        self.table.setRowCount(len(self.employees))

        for row_index, employee in enumerate(self.employees):
            self._set_table_item(row_index, 0, str(employee.id))
            self._set_table_item(row_index, 1, employee.personnel_number)
            self._set_table_item(row_index, 2, employee.full_name)
            self._set_table_item(row_index, 3, employee.department_name)
            self._set_table_item(row_index, 4, employee.position_name)
            self._set_table_item(row_index, 5, employee.email)
            self._set_table_item(row_index, 6, "Да" if employee.is_active else "Нет")

        self.table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.

        Параметры:
            row: номер строки.
            column: номер колонки.
            value: текстовое значение.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)

    def _get_selected_employee_id(self) -> Optional[int]:
        """
        Возвращает ID выбранного сотрудника.
        """
        selected_items = self.table.selectedItems()

        if not selected_items:
            return None

        selected_row = selected_items[0].row()
        employee_id_item = self.table.item(selected_row, 0)

        if employee_id_item is None:
            return None

        return int(employee_id_item.text())

    def _open_selected_employee(self) -> None:
        """
        Открывает карточку выбранного сотрудника.
        """
        employee_id = self._get_selected_employee_id()

        if employee_id is None:
            QMessageBox.warning(
                self,
                "Сотрудник не выбран",
                "Выберите сотрудника в таблице.",
            )
            return

        detail_window = EmployeeDetailWindow(employee_id)
        detail_window.exec()