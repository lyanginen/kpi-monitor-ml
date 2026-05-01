"""
Скрипт проверки содержимого базы данных.

Используется для быстрой проверки:
- количества записей в основных таблицах;
- наличия тестовых пользователей;
- наличия KPI-истории.
"""

from app.database.connection import SessionLocal, get_database_path
from app.database.models import (
    AppSetting,
    AuditLog,
    Department,
    Employee,
    KpiIndicator,
    KpiRecord,
    Position,
    Role,
    User,
)


def print_table_count(session, model, title: str) -> None:
    """
    Выводит количество записей в указанной таблице.

    Параметры:
        session: сессия SQLAlchemy.
        model: ORM-модель таблицы.
        title: человекочитаемое название таблицы.
    """
    count = session.query(model).count()
    print(f"{title}: {count}")


def check_database() -> None:
    """
    Проверяет основные данные в базе.
    """
    session = SessionLocal()

    try:
        print("Проверка базы данных KPI Monitor ML")
        print(f"Файл базы данных: {get_database_path()}")
        print("-" * 60)

        print_table_count(session, Role, "Роли")
        print_table_count(session, User, "Пользователи")
        print_table_count(session, Department, "Отделы")
        print_table_count(session, Position, "Должности")
        print_table_count(session, Employee, "Сотрудники")
        print_table_count(session, KpiIndicator, "KPI-показатели")
        print_table_count(session, KpiRecord, "KPI-записи")
        print_table_count(session, AppSetting, "Настройки")
        print_table_count(session, AuditLog, "Журнал действий")

        print("-" * 60)
        print("Тестовые пользователи:")

        users = session.query(User).order_by(User.id).all()

        for user in users:
            role_name = user.role.name if user.role else "Без роли"
            print(f"{user.username} | {user.full_name} | {role_name}")

        print("-" * 60)
        print("Проверка завершена успешно.")

    finally:
        session.close()


if __name__ == "__main__":
    check_database()