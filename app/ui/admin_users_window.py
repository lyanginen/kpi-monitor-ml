"""
Окно административной панели пользователей.

Окно доступно администратору и позволяет:
- просматривать учетные записи пользователей;
- видеть роли пользователей;
- видеть связь пользователя с сотрудником;
- включать и отключать учетные записи.
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
from app.services.admin_service import AdminService
from app.services.auth_service import AuthenticatedUser


class AdminUsersWindow(QDialog):
    """
    Окно управления пользователями.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно административной панели.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.users = []

        self.setWindowTitle("KPI Monitor ML — админ-панель пользователей")
        self.resize(1050, 620)

        self._create_interface()
        self._load_users()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Админ-панель пользователей")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            "Раздел предназначен для просмотра учетных записей, ролей "
            "и управления активностью пользователей."
        )
        description_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Логин",
                "ФИО",
                "Роль",
                "Связанный сотрудник",
                "Активен",
                "Дата создания",
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._load_users)

        activate_button = QPushButton("Активировать")
        activate_button.clicked.connect(lambda: self._set_selected_user_active(True))

        deactivate_button = QPushButton("Отключить")
        deactivate_button.clicked.connect(lambda: self._set_selected_user_active(False))

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        button_layout.addWidget(refresh_button)
        button_layout.addWidget(activate_button)
        button_layout.addWidget(deactivate_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _load_users(self) -> None:
        """
        Загружает пользователей из базы данных.
        """
        session = SessionLocal()

        try:
            service = AdminService(session)
            self.users = service.get_users()

        finally:
            session.close()

        self.table.setRowCount(len(self.users))

        for row_index, user in enumerate(self.users):
            created_at = "-"

            if user.created_at:
                created_at = user.created_at.strftime("%d.%m.%Y %H:%M")

            self._set_table_item(row_index, 0, str(user.id))
            self._set_table_item(row_index, 1, user.username)
            self._set_table_item(row_index, 2, user.full_name)
            self._set_table_item(row_index, 3, user.role_name)
            self._set_table_item(row_index, 4, user.employee_name)
            self._set_table_item(row_index, 5, "Да" if user.is_active else "Нет")
            self._set_table_item(row_index, 6, created_at)

        self.table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)

    def _get_selected_user_id(self) -> Optional[int]:
        """
        Возвращает ID выбранного пользователя.
        """
        selected_items = self.table.selectedItems()

        if not selected_items:
            return None

        selected_row = selected_items[0].row()
        user_id_item = self.table.item(selected_row, 0)

        if user_id_item is None:
            return None

        return int(user_id_item.text())

    def _set_selected_user_active(self, is_active: bool) -> None:
        """
        Изменяет активность выбранной учетной записи.
        """
        user_id = self._get_selected_user_id()

        if user_id is None:
            QMessageBox.warning(
                self,
                "Пользователь не выбран",
                "Выберите пользователя в таблице.",
            )
            return

        if user_id == self.current_user.id and not is_active:
            QMessageBox.warning(
                self,
                "Операция запрещена",
                "Нельзя отключить собственную учетную запись.",
            )
            return

        session = SessionLocal()

        try:
            service = AdminService(session)
            service.set_user_active(user_id, is_active)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка изменения пользователя",
                f"Не удалось изменить учетную запись.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Готово",
            "Статус учетной записи успешно изменен.",
        )

        self._load_users()