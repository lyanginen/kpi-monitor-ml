"""
Окно журнала действий.

Окно доступно администратору и показывает события системы:
- авторизацию пользователей;
- добавление KPI-записей;
- обучение ML-модели;
- выполнение прогнозов;
- формирование отчетов;
- изменение статусов пользователей.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.audit_service import AuditService
from app.services.auth_service import AuthenticatedUser


class AuditLogWindow(QDialog):
    """
    Окно просмотра журнала действий.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно журнала действий.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.logs = []

        self.setWindowTitle("KPI Monitor ML — журнал действий")
        self.resize(1150, 650)

        self._create_interface()
        self._load_logs()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна журнала.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Журнал действий пользователей")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            "В этом разделе отображаются ключевые действия пользователей "
            "и системные события приложения."
        )
        description_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Пользователь",
                "Действие",
                "Сущность",
                "ID сущности",
                "Дата и время",
                "Подробности",
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._load_logs)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.table)
        main_layout.addWidget(refresh_button)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _load_logs(self) -> None:
        """
        Загружает записи журнала из базы данных.
        """
        session = SessionLocal()

        try:
            service = AuditService(session)
            self.logs = service.get_logs()

        finally:
            session.close()

        self.table.setRowCount(len(self.logs))

        for row_index, log in enumerate(self.logs):
            created_at = "-"

            if log.created_at:
                created_at = log.created_at.strftime("%d.%m.%Y %H:%M:%S")

            entity_id = "-" if log.entity_id is None else str(log.entity_id)

            self._set_table_item(row_index, 0, str(log.id))
            self._set_table_item(row_index, 1, log.user_name)
            self._set_table_item(row_index, 2, log.action)
            self._set_table_item(row_index, 3, log.entity_name)
            self._set_table_item(row_index, 4, entity_id)
            self._set_table_item(row_index, 5, created_at)
            self._set_table_item(row_index, 6, log.details)

        self.table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)