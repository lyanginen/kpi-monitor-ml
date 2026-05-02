"""
Сервис настроек приложения.

Модуль отвечает за:
- получение настроек из базы данных;
- изменение значений настроек;
- создание резервной копии базы данных;
- получение путей к рабочим папкам приложения.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.database.connection import BASE_DIR, DATA_DIR, DATABASE_PATH
from app.database.models import AppSetting


EXPORTS_DIR = BASE_DIR / "exports"
BACKUPS_DIR = EXPORTS_DIR / "backups"

EXPORTS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

HIDDEN_SETTING_KEYS = {
    "author_name",
    "application_theme",
}


@dataclass
class AppSettingItem:
    """
    Настройка приложения для отображения в интерфейсе.
    """

    id: int
    setting_key: str
    setting_value: str
    description: str


class SettingsService:
    """
    Сервис работы с настройками приложения.
    """

    def __init__(self, session):
        """
        Создает сервис настроек.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def get_settings(self) -> List[AppSettingItem]:
        """
        Возвращает список настроек приложения.
        """
        query = self.session.query(AppSetting)

        for hidden_key in HIDDEN_SETTING_KEYS:
            query = query.filter(AppSetting.setting_key != hidden_key)

        settings = query.order_by(AppSetting.setting_key).all()

        return [
            AppSettingItem(
                id=setting.id,
                setting_key=setting.setting_key,
                setting_value=setting.setting_value,
                description=setting.description or "",
            )
            for setting in settings
        ]

        return [
            AppSettingItem(
                id=setting.id,
                setting_key=setting.setting_key,
                setting_value=setting.setting_value,
                description=setting.description or "",
            )
            for setting in settings
        ]

    def get_setting_value(self, setting_key: str) -> Optional[str]:
        """
        Возвращает значение настройки по ключу.
        """
        setting = (
            self.session.query(AppSetting)
            .filter(AppSetting.setting_key == setting_key)
            .first()
        )

        if setting is None:
            return None

        return setting.setting_value

    def update_setting(self, setting_key: str, setting_value: str) -> None:
        """
        Обновляет значение настройки.

        Если настройки с таким ключом нет, она будет создана.
        """
        if setting_key in HIDDEN_SETTING_KEYS:
            raise ValueError("Эта настройка является служебной и не может изменяться из интерфейса.")

        setting = (
            self.session.query(AppSetting)
            .filter(AppSetting.setting_key == setting_key)
            .first()
        )

        if setting is None:
            setting = AppSetting(
                setting_key=setting_key,
                setting_value=setting_value,
                description="Пользовательская настройка приложения.",
            )
            self.session.add(setting)
        else:
            setting.setting_value = setting_value

        self.session.commit()

    def create_database_backup(self) -> str:
        """
        Создает резервную копию файла базы данных.

        Возвращает:
            путь к созданному файлу резервной копии.
        """
        if not DATABASE_PATH.exists():
            raise FileNotFoundError("Файл базы данных не найден.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUPS_DIR / f"kpi_monitor_backup_{timestamp}.db"

        shutil.copy2(DATABASE_PATH, backup_file)

        return str(backup_file)

    def get_data_directory(self) -> Path:
        """
        Возвращает путь к папке data.
        """
        DATA_DIR.mkdir(exist_ok=True)

        return DATA_DIR

    def get_exports_directory(self) -> Path:
        """
        Возвращает путь к папке exports.
        """
        EXPORTS_DIR.mkdir(exist_ok=True)

        return EXPORTS_DIR

    def get_models_directory(self) -> Path:
        """
        Возвращает путь к папке models.
        """
        models_dir = BASE_DIR / "models"
        models_dir.mkdir(exist_ok=True)

        return models_dir