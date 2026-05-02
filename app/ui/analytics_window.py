"""
Окно аналитики KPI.

Окно показывает:
- общую статистику KPI;
- средние показатели по отделам;
- средние показатели по сотрудникам.

Данные отображаются с учетом роли пользователя.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticatedUser


class AnalyticsWindow(QDialog):
    """
    Окно аналитики KPI.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно аналитики.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.dashboard_stats = None
        self.department_summary = []
        self.employee_summary = []

        self.setWindowTitle("KPI Monitor ML — аналитика KPI")
        self.resize(1050, 700)

        self._create_interface()
        self._load_analytics()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Аналитика KPI")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            f"Текущая роль: {self.current_user.role_name}. "
            "Аналитика построена на основе доступных пользователю данных."
        )
        description_label.setWordWrap(True)

        self.tabs = QTabWidget()

        self.summary_tab = QWidget()
        self.departments_tab = QWidget()
        self.employees_tab = QWidget()

        self.tabs.addTab(self.summary_tab, "Сводка")
        self.tabs.addTab(self.departments_tab, "По отделам")
        self.tabs.addTab(self.employees_tab, "По сотрудникам")

        self._create_summary_tab()
        self._create_departments_tab()
        self._create_employees_tab()

        refresh_button = QPushButton("Обновить аналитику")
        refresh_button.clicked.connect(self._load_analytics)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(refresh_button)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _create_summary_tab(self) -> None:
        """
        Создает вкладку сводной аналитики.
        """
        layout = QGridLayout()

        self.employees_count_label = self._create_metric_card("Сотрудников", "0")
        self.records_count_label = self._create_metric_card("KPI-записей", "0")
        self.average_score_label = self._create_metric_card("Средняя оценка", "0")
        self.min_score_label = self._create_metric_card("Минимальная оценка", "0")
        self.max_score_label = self._create_metric_card("Максимальная оценка", "0")

        layout.addWidget(self.employees_count_label, 0, 0)
        layout.addWidget(self.records_count_label, 0, 1)
        layout.addWidget(self.average_score_label, 0, 2)
        layout.addWidget(self.min_score_label, 1, 0)
        layout.addWidget(self.max_score_label, 1, 1)

        self.summary_tab.setLayout(layout)

    def _create_metric_card(self, title: str, value: str) -> QFrame:
        """
        Создает карточку метрики.
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setMinimumHeight(120)

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px;")

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 26px; font-weight: bold;")

        frame.value_label = value_label

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        frame.setLayout(layout)

        return frame

    def _create_departments_tab(self) -> None:
        """
        Создает вкладку аналитики по отделам.
        """
        layout = QVBoxLayout()

        self.departments_table = QTableWidget()
        self.departments_table.setColumnCount(4)
        self.departments_table.setHorizontalHeaderLabels(
            [
                "Отдел",
                "Сотрудников",
                "KPI-записей",
                "Средняя оценка",
            ]
        )
        self.departments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.departments_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.departments_table)
        self.departments_tab.setLayout(layout)

    def _create_employees_tab(self) -> None:
        """
        Создает вкладку аналитики по сотрудникам.
        """
        layout = QVBoxLayout()

        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(5)
        self.employees_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Сотрудник",
                "Отдел",
                "KPI-записей",
                "Средняя оценка",
            ]
        )
        self.employees_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.employees_table)
        self.employees_tab.setLayout(layout)

    def _load_analytics(self) -> None:
        """
        Загружает аналитику из базы данных.
        """
        session = SessionLocal()

        try:
            service = AnalyticsService(session)
            self.dashboard_stats = service.get_dashboard_stats(self.current_user)
            self.department_summary = service.get_department_summary(self.current_user)
            self.employee_summary = service.get_employee_summary(self.current_user)

        finally:
            session.close()

        self._fill_summary_tab()
        self._fill_departments_table()
        self._fill_employees_table()

    def _fill_summary_tab(self) -> None:
        """
        Заполняет сводную вкладку.
        """
        stats = self.dashboard_stats

        self.employees_count_label.value_label.setText(str(stats.employees_count))
        self.records_count_label.value_label.setText(str(stats.kpi_records_count))
        self.average_score_label.value_label.setText(f"{stats.average_score:.2f}")
        self.min_score_label.value_label.setText(f"{stats.min_score:.2f}")
        self.max_score_label.value_label.setText(f"{stats.max_score:.2f}")

    def _fill_departments_table(self) -> None:
        """
        Заполняет таблицу аналитики по отделам.
        """
        self.departments_table.setRowCount(len(self.department_summary))

        for row_index, item in enumerate(self.department_summary):
            self._set_table_item(
                self.departments_table,
                row_index,
                0,
                item.department_name,
            )
            self._set_table_item(
                self.departments_table,
                row_index,
                1,
                str(item.employees_count),
            )
            self._set_table_item(
                self.departments_table,
                row_index,
                2,
                str(item.records_count),
            )
            self._set_table_item(
                self.departments_table,
                row_index,
                3,
                f"{item.average_score:.2f}",
            )

        self.departments_table.resizeColumnsToContents()

    def _fill_employees_table(self) -> None:
        """
        Заполняет таблицу аналитики по сотрудникам.
        """
        self.employees_table.setRowCount(len(self.employee_summary))

        for row_index, item in enumerate(self.employee_summary):
            self._set_table_item(
                self.employees_table,
                row_index,
                0,
                str(item.employee_id),
            )
            self._set_table_item(
                self.employees_table,
                row_index,
                1,
                item.employee_name,
            )
            self._set_table_item(
                self.employees_table,
                row_index,
                2,
                item.department_name,
            )
            self._set_table_item(
                self.employees_table,
                row_index,
                3,
                str(item.records_count),
            )
            self._set_table_item(
                self.employees_table,
                row_index,
                4,
                f"{item.average_score:.2f}",
            )

        self.employees_table.resizeColumnsToContents()

    def _set_table_item(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        value: str,
    ) -> None:
        """
        Устанавливает значение в ячейку таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.setItem(row, column, item)