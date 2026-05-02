"""
Окно настроек приложения.

Окно позволяет:
- просматривать настройки из базы данных;
- редактировать выбранную настройку;
- создавать резервную копию базы данных;
- открывать рабочие папки приложения;
- отображать техническую информацию о проекте.
"""

import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthenticatedUser
from app.services.settings_service import SettingsService


class SettingsWindow(QDialog):
    """
    Окно настроек приложения.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно настроек.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.settings = []

        self.setWindowTitle("KPI Monitor ML — настройки")
        self.resize(1000, 650)

        self._create_interface()
        self._load_settings()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна настроек.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Панель настроек")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            "В этом разделе отображаются основные настройки приложения, "
            "рабочие каталоги и служебные действия."
        )
        description_label.setWordWrap(True)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setText(
            "Панель настроек содержит не менее 5 пунктов управления:\n"
            "1. редактирование настройки;\n"
            "2. обновление списка настроек;\n"
            "3. резервное копирование базы данных;\n"
            "4. открытие папки data;\n"
            "5. открытие папки exports;\n"
            "6. открытие папки models."
        )

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Ключ",
                "Значение",
                "Описание",
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        button_layout = QHBoxLayout()

        edit_button = QPushButton("Изменить настройку")
        edit_button.clicked.connect(self._edit_selected_setting)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._load_settings)

        backup_button = QPushButton("Создать резервную копию БД")
        backup_button.clicked.connect(self._create_database_backup)

        open_data_button = QPushButton("Открыть data")
        open_data_button.clicked.connect(self._open_data_directory)

        open_exports_button = QPushButton("Открыть exports")
        open_exports_button.clicked.connect(self._open_exports_directory)

        open_models_button = QPushButton("Открыть models")
        open_models_button.clicked.connect(self._open_models_directory)

        button_layout.addWidget(edit_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(backup_button)
        button_layout.addWidget(open_data_button)
        button_layout.addWidget(open_exports_button)
        button_layout.addWidget(open_models_button)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.info_text)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _load_settings(self) -> None:
        """
        Загружает настройки из базы данных.
        """
        session = SessionLocal()

        try:
            service = SettingsService(session)
            self.settings = service.get_settings()

        finally:
            session.close()

        self.table.setRowCount(len(self.settings))

        for row_index, setting in enumerate(self.settings):
            self._set_table_item(row_index, 0, str(setting.id))
            self._set_table_item(row_index, 1, setting.setting_key)
            self._set_table_item(row_index, 2, setting.setting_value)
            self._set_table_item(row_index, 3, setting.description)

        self.table.resizeColumnsToContents()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)

    def _get_selected_setting_key(self):
        """
        Возвращает ключ выбранной настройки.
        """
        selected_items = self.table.selectedItems()

        if not selected_items:
            return None

        selected_row = selected_items[0].row()
        key_item = self.table.item(selected_row, 1)

        if key_item is None:
            return None

        return key_item.text()

    def _get_selected_setting_value(self):
        """
        Возвращает значение выбранной настройки.
        """
        selected_items = self.table.selectedItems()

        if not selected_items:
            return None

        selected_row = selected_items[0].row()
        value_item = self.table.item(selected_row, 2)

        if value_item is None:
            return None

        return value_item.text()

    def _edit_selected_setting(self) -> None:
        """
        Открывает диалог изменения выбранной настройки.
        """
        setting_key = self._get_selected_setting_key()
        current_value = self._get_selected_setting_value()

        if setting_key is None:
            QMessageBox.warning(
                self,
                "Настройка не выбрана",
                "Выберите настройку в таблице.",
            )
            return

        new_value, ok = QInputDialog.getText(
            self,
            "Изменение настройки",
            f"Введите новое значение для настройки:\n{setting_key}",
            text=current_value or "",
        )

        if not ok:
            return

        session = SessionLocal()

        try:
            service = SettingsService(session)
            service.update_setting(setting_key, new_value)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось изменить настройку.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Готово",
            "Настройка успешно изменена.",
        )

        self._load_settings()

    def _create_database_backup(self) -> None:
        """
        Создает резервную копию базы данных.
        """
        session = SessionLocal()

        try:
            service = SettingsService(session)
            backup_path = service.create_database_backup()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка резервного копирования",
                f"Не удалось создать резервную копию базы данных.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Резервная копия создана",
            f"Файл резервной копии:\n{backup_path}",
        )

    def _open_data_directory(self) -> None:
        """
        Открывает папку data.
        """
        session = SessionLocal()

        try:
            service = SettingsService(session)
            directory = service.get_data_directory()

        finally:
            session.close()

        self._open_directory(directory)

    def _open_exports_directory(self) -> None:
        """
        Открывает папку exports.
        """
        session = SessionLocal()

        try:
            service = SettingsService(session)
            directory = service.get_exports_directory()

        finally:
            session.close()

        self._open_directory(directory)

    def _open_models_directory(self) -> None:
        """
        Открывает папку models.
        """
        session = SessionLocal()

        try:
            service = SettingsService(session)
            directory = service.get_models_directory()

        finally:
            session.close()

        self._open_directory(directory)

    def _open_directory(self, directory: Path) -> None:
        """
        Открывает папку в файловой системе.

        Поддерживаются macOS, Windows и Linux.
        """
        directory.mkdir(exist_ok=True)

        system_name = platform.system()

        try:
            if system_name == "Windows":
                os.startfile(directory)
            elif system_name == "Darwin":
                subprocess.run(["open", str(directory)], check=False)
            else:
                subprocess.run(["xdg-open", str(directory)], check=False)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка открытия папки",
                f"Не удалось открыть папку.\n\n{error}",
            )