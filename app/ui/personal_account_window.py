"""
Окно личного кабинета пользователя.

Окно показывает:
- данные текущего пользователя;
- роль пользователя;
- связанного сотрудника;
- краткую сводку KPI;
- доступные пользователю разделы системы.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticatedUser
from app.services.employee_service import EmployeeService
from app.services.permission_service import get_available_sections


class PersonalAccountWindow(QDialog):
    """
    Окно личного кабинета.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает личный кабинет.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user

        self.setWindowTitle("KPI Monitor ML — личный кабинет")
        self.resize(850, 620)

        self._create_interface()
        self._load_user_data()

    def _create_interface(self) -> None:
        """
        Создает интерфейс личного кабинета.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Личный кабинет")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.form_layout = QFormLayout()

        self.full_name_label = QLabel("-")
        self.username_label = QLabel("-")
        self.role_label = QLabel("-")
        self.employee_label = QLabel("-")
        self.department_label = QLabel("-")
        self.position_label = QLabel("-")
        self.average_kpi_label = QLabel("-")
        self.kpi_records_count_label = QLabel("-")

        self.form_layout.addRow("ФИО пользователя:", self.full_name_label)
        self.form_layout.addRow("Логин:", self.username_label)
        self.form_layout.addRow("Роль:", self.role_label)
        self.form_layout.addRow("Связанный сотрудник:", self.employee_label)
        self.form_layout.addRow("Отдел:", self.department_label)
        self.form_layout.addRow("Должность:", self.position_label)
        self.form_layout.addRow("Средняя оценка KPI:", self.average_kpi_label)
        self.form_layout.addRow("Количество KPI-записей:", self.kpi_records_count_label)

        sections_label = QLabel("Доступные разделы")
        sections_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.sections_text = QTextEdit()
        self.sections_text.setReadOnly(True)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(sections_label)
        main_layout.addWidget(self.sections_text)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _load_user_data(self) -> None:
        """
        Загружает данные пользователя, сотрудника и KPI-сводку.
        """
        self.full_name_label.setText(self.current_user.full_name)
        self.username_label.setText(self.current_user.username)
        self.role_label.setText(self.current_user.role_name)

        sections = get_available_sections(self.current_user)
        sections_text = "\n".join(f"- {section}" for section in sections)
        self.sections_text.setText(sections_text)

        if self.current_user.employee_id is None:
            self.employee_label.setText("Не связан с сотрудником")
            self.department_label.setText("-")
            self.position_label.setText("-")
            self.average_kpi_label.setText("-")
            self.kpi_records_count_label.setText("-")
            return

        session = SessionLocal()

        try:
            employee_service = EmployeeService(session)
            employee = employee_service.get_employee_details(self.current_user.employee_id)

            analytics_service = AnalyticsService(session)
            employee_summary = analytics_service.get_employee_summary(self.current_user)

        finally:
            session.close()

        if employee is None:
            self.employee_label.setText("Сотрудник не найден")
            self.department_label.setText("-")
            self.position_label.setText("-")
            self.average_kpi_label.setText("-")
            self.kpi_records_count_label.setText("-")
            return

        self.employee_label.setText(employee.full_name)
        self.department_label.setText(employee.department_name)
        self.position_label.setText(employee.position_name)

        if employee_summary:
            summary = employee_summary[0]
            self.average_kpi_label.setText(f"{summary.average_score:.2f}")
            self.kpi_records_count_label.setText(str(summary.records_count))
        else:
            self.average_kpi_label.setText("0.00")
            self.kpi_records_count_label.setText("0")