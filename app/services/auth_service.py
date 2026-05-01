"""
Сервис авторизации пользователей.

Этот модуль отвечает за:
- поиск пользователя по логину;
- проверку пароля;
- проверку активности учетной записи;
- возврат информации о вошедшем пользователе.
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import User
from app.utils.security import verify_password


@dataclass
class AuthenticatedUser:
    """
    Данные авторизованного пользователя.

    Этот класс используется после успешного входа в систему.
    В нем хранятся только те данные, которые нужны приложению для работы:
    id пользователя, логин, ФИО, роль и связь с сотрудником.
    """

    id: int
    username: str
    full_name: str
    role_name: str
    employee_id: Optional[int]

    def is_admin(self) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        """
        return self.role_name == "Администратор"

    def is_manager(self) -> bool:
        """
        Проверяет, является ли пользователь руководителем.
        """
        return self.role_name == "Руководитель"

    def is_employee(self) -> bool:
        """
        Проверяет, является ли пользователь сотрудником.
        """
        return self.role_name == "Сотрудник"


class AuthService:
    """
    Сервис для работы с авторизацией.

    Сервис получает сессию базы данных и через нее ищет пользователя.
    """

    def __init__(self, session: Session):
        """
        Создает объект сервиса авторизации.

        Параметры:
            session: активная сессия SQLAlchemy для работы с базой данных.
        """
        self.session = session

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Ищет пользователя по логину.

        Параметры:
            username: логин пользователя.

        Возвращает:
            объект User, если пользователь найден;
            None, если пользователь не найден.
        """
        if not username:
            return None

        normalized_username = username.strip()

        return (
            self.session.query(User)
            .filter(User.username == normalized_username)
            .first()
        )

    def authenticate(self, username: str, password: str) -> Optional[AuthenticatedUser]:
        """
        Выполняет авторизацию пользователя.

        Параметры:
            username: логин пользователя.
            password: пароль пользователя.

        Возвращает:
            AuthenticatedUser при успешной авторизации;
            None при ошибке логина, пароля или если пользователь отключен.
        """
        user = self.get_user_by_username(username)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        role_name = user.role.name if user.role else "Без роли"

        return AuthenticatedUser(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role_name=role_name,
            employee_id=user.employee_id,
        )