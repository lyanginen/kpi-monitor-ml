"""
Модуль подключения к базе данных.

"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Корневая папка проекта.
# parents[2] означает: от файла app/database/connection.py подняться на два уровня вверх.
BASE_DIR = Path(__file__).resolve().parents[2]

# Папка для хранения данных приложения.
DATA_DIR = BASE_DIR / "data"

# Создаем папку data, если она еще не существует.
DATA_DIR.mkdir(exist_ok=True)

# Путь к файлу базы данных.
DATABASE_PATH = DATA_DIR / "kpi_monitor.db"

# Строка подключения к SQLite.
DATABASE_URL = "sqlite:///" + str(DATABASE_PATH)

# Объект engine отвечает за соединение приложения с базой данных.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# SessionLocal используется для создания сессий работы с базой данных.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base — базовый класс для всех ORM-моделей.
Base = declarative_base()


def get_database_path() -> Path:
    """
    Возвращает путь к файлу базы данных.

    Функция нужна, чтобы другие модули приложения могли получить путь к БД,
    например для отображения в справке или для резервного копирования.
    """
    return DATABASE_PATH