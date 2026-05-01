"""
Окно карточки сотрудника.

Окно показывает подробную информацию о сотруднике и его KPI-записи.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.employee_service import EmployeeDetails, EmployeeKpiRecordItem, EmployeeService


class EmployeeDetailWindow(QDialog):
    """
    Карточка сотрудника.
    """

    def __init__(self, employee_id: int):
        """
        Создает карточку сотрудника.

        Параметры:
            employee_id: идентификатор сотрудника в базе данных.
        """
        super().__init__()

        self.employee_id = employee_id
        self.employee_details: Optional[EmployeeDetails] = None
        self.kpi_records: list[EmployeeKpiRecordItem] = []

        self.setWindowTitle("KPI Monitor ML — карточка сотрудника")
        self.resize(900, 650)

        self._create_interface()
        self._load_employee_data()

    def _create_interface(self) -> None:
        """
        Создает интерфейс карточки сотрудника.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Карточка сотрудника")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.form_layout = QFormLayout()

        self.personnel_number_label = QLabel("-")
        self.full_name_label = QLabel("-")
        self.email_label = QLabel("-")
        self.phone_label = QLabel("-")
        self.hire_date_label = QLabel("-")
        self.department_label = QLabel("-")
        self.position_label = QLabel("-")
        self.status_label = QLabel("-")

        self.form_layout.addRow("Табельный номер:", self.personnel_number_label)
        self.form_layout.addRow("ФИО:", self.full_name_label)
        self.form_layout.addRow("Email:", self.email_label)
        self.form_layout.addRow("Телефон:", self.phone_label)
        self.form_layout.addRow("Дата приема:", self.hire_date_label)
        self.form_layout.addRow("Отдел:", self.department_label)
        self.form_layout.addRow("Должность:", self.position_label)
        self.form_layout.addRow("Статус:", self.status_label)

        kpi_title_label = QLabel("История KPI")
        kpi_title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.kpi_table = QTableWidget()
        self.kpi_table.setColumnCount(6)
        self.kpi_table.setHorizontalHeaderLabels(
            [
                "Показатель",
                "Период с",
                "Период по",
                "Факт",
                "План",
                "Оценка",
            ]
        )
        self.kpi_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.kpi_table.setSelectionBehavior(QTableWidget.SelectRows)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addLayout(self.form_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(kpi_title_label)
        main_layout.addWidget(self.kpi_table)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _load_employee_data(self) -> None:
        """
        Загружает данные сотрудника и KPI из базы данных.
        """
        session = SessionLocal()

        try:
            service = EmployeeService(session)
            self.employee_details = service.get_employee_details(self.employee_id)
            self.kpi_records = service.get_employee_kpi_records(self.employee_id)

        finally:
            session.close()

        if self.employee_details is None:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Сотрудник не найден.",
            )
            self.close()
            return

        self._fill_employee_form(self.employee_details)
        self._fill_kpi_table(self.kpi_records)

    def _fill_employee_form(self, employee: EmployeeDetails) -> None:
        """
        Заполняет поля карточки сотрудника.
        """
        self.personnel_number_label.setText(employee.personnel_number)
        self.full_name_label.setText(employee.full_name)
        self.email_label.setText(employee.email)
        self.phone_label.setText(employee.phone)
        self.hire_date_label.setText(
            employee.hire_date.strftime("%d.%m.%Y") if employee.hire_date else "-"
        )
        self.department_label.setText(employee.department_name)
        self.position_label.setText(employee.position_name)
        self.status_label.setText("Активен" if employee.is_active else "Неактивен")

    def _fill_kpi_table(self, records: list[EmployeeKpiRecordItem]) -> None:
        """
        Заполняет таблицу KPI-записей.
        """
        self.kpi_table.setRowCount(len(records))

        for row_index, record in enumerate(records):
            self._set_table_item(row_index, 0, record.indicator_name)
            self._set_table_item(row_index, 1, record.period_start.strftime("%d.%m.%Y"))
            self._set_table_item(row_index, 2, record.period_end.strftime("%d.%m.%Y"))
            self._set_table_item(row_index, 3, f"{record.actual_value:.2f}")
            self._set_table_item(row_index, 4, f"{record.target_value:.2f}")
            self._set_table_item(row_index, 5, f"{record.score:.2f}")

        self.kpi_table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.kpi_table.setItem(row, column, item)