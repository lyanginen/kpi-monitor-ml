"""
Скрипт инициализации базы данных.

При запуске создает файл SQLite-базы данных и все таблицы,
описанные в ORM-моделях SQLAlchemy.
"""

from app.database.connection import Base, engine, get_database_path
from app.database import models  


def init_database() -> None:
    """
    Создает таблицы базы данных.

    SQLAlchemy берет все классы моделей, унаследованные от Base,
    и создает соответствующие таблицы в SQLite.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_database()
    print("База данных успешно создана.")
    print(f"Путь к базе данных: {get_database_path()}")