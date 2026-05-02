"""
Окно списка KPI-записей.

Окно показывает KPI-записи из базы данных с учетом роли пользователя:
- администратор видит все записи;
- руководитель видит записи сотрудников своего отдела;
- сотрудник видит только собственные KPI.
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
from app.services.kpi_service import KpiRecordListItem, KpiService
from app.services.permission_service import can_manage_kpi
from app.ui.kpi_form_window import KpiFormWindow


class KpiListWindow(QDialog):
    """
    Окно списка KPI-записей.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно списка KPI.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.kpi_records = []

        self.setWindowTitle("KPI Monitor ML — KPI-записи")
        self.resize(1100, 650)

        self._create_interface()
        self._load_kpi_records()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("KPI-записи сотрудников")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            f"Текущая роль: {self.current_user.role_name}. "
            "Данные отображаются с учетом прав доступа."
        )
        description_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Сотрудник",
                "Отдел",
                "Показатель",
                "Период с",
                "Период по",
                "Факт",
                "План",
                "Оценка",
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._load_kpi_records)

        self.add_button = QPushButton("Добавить KPI")
        self.add_button.clicked.connect(self._open_add_kpi_stub)
        self.add_button.setEnabled(can_manage_kpi(self.current_user))

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        button_layout.addWidget(refresh_button)
        button_layout.addWidget(self.add_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _load_kpi_records(self) -> None:
        """
        Загружает KPI-записи из базы данных.
        """
        session = SessionLocal()

        try:
            service = KpiService(session)
            self.kpi_records = service.get_kpi_records_for_user(self.current_user)

        finally:
            session.close()

        self.table.setRowCount(len(self.kpi_records))

        for row_index, record in enumerate(self.kpi_records):
            self._set_table_item(row_index, 0, str(record.id))
            self._set_table_item(row_index, 1, record.employee_name)
            self._set_table_item(row_index, 2, record.department_name)
            self._set_table_item(row_index, 3, record.indicator_name)
            self._set_table_item(row_index, 4, record.period_start.strftime("%d.%m.%Y"))
            self._set_table_item(row_index, 5, record.period_end.strftime("%d.%m.%Y"))
            self._set_table_item(row_index, 6, f"{record.actual_value:.2f}")
            self._set_table_item(row_index, 7, f"{record.target_value:.2f}")
            self._set_table_item(row_index, 8, f"{record.score:.2f}")

        self.table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение в ячейку таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)

    def _open_add_kpi_stub(self) -> None:
        """
        Открывает форму добавления KPI-записи.

        После успешного сохранения список KPI автоматически обновляется.
        """
        form_window = KpiFormWindow(self.current_user)
        result = form_window.exec()

        if result == QDialog.Accepted:
            self._load_kpi_records()