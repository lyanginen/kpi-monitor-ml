"""
Форма добавления KPI-записи.

Форма позволяет администратору или руководителю выбрать сотрудника,
выбрать KPI-показатель, указать период, фактическое значение и комментарий.
"""

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthenticatedUser
from app.services.kpi_service import KpiService


class KpiFormWindow(QDialog):
    """
    Окно добавления KPI-записи.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает форму добавления KPI.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.employees = []
        self.indicators = []

        self.setWindowTitle("KPI Monitor ML — добавление KPI")
        self.resize(520, 500)

        self._create_interface()
        self._load_form_data()

    def _create_interface(self) -> None:
        """
        Создает интерфейс формы.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Добавление KPI-записи")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        form_layout = QFormLayout()

        self.employee_combo = QComboBox()
        self.indicator_combo = QComboBox()
        self.indicator_combo.currentIndexChanged.connect(self._update_target_value)

        self.period_start_input = QDateEdit()
        self.period_start_input.setCalendarPopup(True)
        self.period_start_input.setDate(QDate.currentDate())

        self.period_end_input = QDateEdit()
        self.period_end_input.setCalendarPopup(True)
        self.period_end_input.setDate(QDate.currentDate())

        self.actual_value_input = QDoubleSpinBox()
        self.actual_value_input.setRange(0, 100000)
        self.actual_value_input.setDecimals(2)
        self.actual_value_input.setValue(80.00)

        self.target_value_input = QDoubleSpinBox()
        self.target_value_input.setRange(0, 100000)
        self.target_value_input.setDecimals(2)
        self.target_value_input.setValue(100.00)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Комментарий к KPI-записи")

        form_layout.addRow("Сотрудник:", self.employee_combo)
        form_layout.addRow("KPI-показатель:", self.indicator_combo)
        form_layout.addRow("Период с:", self.period_start_input)
        form_layout.addRow("Период по:", self.period_end_input)
        form_layout.addRow("Фактическое значение:", self.actual_value_input)
        form_layout.addRow("Плановое значение:", self.target_value_input)
        form_layout.addRow("Комментарий:", self.comment_input)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self._save_kpi_record)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)

        main_layout.addWidget(title_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(save_button)
        main_layout.addWidget(cancel_button)

        self.setLayout(main_layout)

    def _load_form_data(self) -> None:
        """
        Загружает сотрудников и KPI-показатели для выпадающих списков.
        """
        session = SessionLocal()

        try:
            service = KpiService(session)
            self.employees = service.get_available_employees_for_user(self.current_user)
            self.indicators = service.get_indicators()

        finally:
            session.close()

        self.employee_combo.clear()

        for employee in self.employees:
            self.employee_combo.addItem(employee.full_name, employee.id)

        self.indicator_combo.clear()

        for indicator in self.indicators:
            self.indicator_combo.addItem(indicator.name, indicator.id)

        self._update_target_value()

    def _update_target_value(self) -> None:
        """
        Подставляет плановое значение выбранного KPI-показателя.
        """
        indicator_index = self.indicator_combo.currentIndex()

        if indicator_index < 0:
            return

        if indicator_index >= len(self.indicators):
            return

        indicator = self.indicators[indicator_index]
        self.target_value_input.setValue(indicator.target_value)

    def _qdate_to_python_date(self, value: QDate) -> date:
        """
        Преобразует дату из формата Qt в стандартный Python date.
        """
        return date(value.year(), value.month(), value.day())

    def _save_kpi_record(self) -> None:
        """
        Сохраняет KPI-запись в базу данных.
        """
        employee_id = self.employee_combo.currentData()
        indicator_id = self.indicator_combo.currentData()

        if employee_id is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите сотрудника.",
            )
            return

        if indicator_id is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите KPI-показатель.",
            )
            return

        period_start = self._qdate_to_python_date(self.period_start_input.date())
        period_end = self._qdate_to_python_date(self.period_end_input.date())
        actual_value = self.actual_value_input.value()
        target_value = self.target_value_input.value()
        comment = self.comment_input.toPlainText().strip()

        session = SessionLocal()

        try:
            service = KpiService(session)
            service.create_kpi_record(
                employee_id=employee_id,
                indicator_id=indicator_id,
                period_start=period_start,
                period_end=period_end,
                actual_value=actual_value,
                target_value=target_value,
                comment=comment,
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                str(error),
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить KPI-запись.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Готово",
            "KPI-запись успешно сохранена.",
        )
        self.accept()