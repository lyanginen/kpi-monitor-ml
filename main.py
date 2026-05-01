"""
Автор: Лянгинен Илья Борисович
Тема ВКР: Разработка системы мониторинга и анализа KPI сотрудников организации
с использованием методов машинного обучения.
"""

from getpass import getpass

from app.database.connection import SessionLocal
from app.services.auth_service import AuthService
from app.services.permission_service import get_available_sections


def print_application_header() -> None:
    """
    Выводит заголовок приложения в консоль.
    """
    print("=" * 70)
    print("KPI Monitor ML")
    print("Система мониторинга и анализа KPI сотрудников организации")
    print("=" * 70)


def print_test_accounts_hint() -> None:
    """
    Выводит подсказку с тестовыми учетными записями.

    В финальной версии эти данные будут указаны во введении к ВКР,
    так как проверяющему нужно иметь возможность войти под разными ролями.
    """
    print("Тестовые учетные записи:")
    print("  admin    / admin123")
    print("  manager  / manager123")
    print("  employee / employee123")
    print("-" * 70)


def run_console_login_demo() -> None:
    """
    Запускает консольную демонстрацию авторизации.

    Эта функция временная. Она нужна, чтобы проверить бизнес-логику входа
    до разработки графического интерфейса.
    """
    session = SessionLocal()

    try:
        auth_service = AuthService(session)

        username = input("Введите логин: ").strip()
        password = getpass("Введите пароль: ")

        authenticated_user = auth_service.authenticate(username, password)

        if authenticated_user is None:
            print("Ошибка авторизации: неверный логин, пароль или учетная запись отключена.")
            return

        print("-" * 70)
        print("Авторизация выполнена успешно.")
        print(f"Пользователь: {authenticated_user.full_name}")
        print(f"Логин: {authenticated_user.username}")
        print(f"Роль: {authenticated_user.role_name}")

        if authenticated_user.employee_id:
            print(f"ID связанного сотрудника: {authenticated_user.employee_id}")
        else:
            print("Связанный сотрудник: не указан")

        print("-" * 70)
        print("Доступные разделы:")

        available_sections = get_available_sections(authenticated_user)

        for index, section_name in enumerate(available_sections, start=1):
            print(f"{index}. {section_name}")

        print("-" * 70)
        print("Проверка авторизации завершена.")

    finally:
        session.close()


def main() -> None:
    """
    Главная функция приложения.
    """
    print_application_header()
    print_test_accounts_hint()
    run_console_login_demo()


if __name__ == "__main__":
    main()