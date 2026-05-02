"""
Сервис административного управления пользователями.

Модуль отвечает за:
- получение списка пользователей;
- изменение активности учетной записи;
- получение ролей пользователей;
- подготовку данных для административной панели.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload

from app.database.models import Role, User


@dataclass
class UserListItem:
    """
    Пользователь для отображения в административной панели.
    """

    id: int
    username: str
    full_name: str
    role_name: str
    employee_name: str
    is_active: bool
    created_at: Optional[datetime]


@dataclass
class RoleListItem:
    """
    Роль пользователя для отображения в интерфейсе.
    """

    id: int
    name: str
    description: str


class AdminService:
    """
    Сервис административных функций.
    """

    def __init__(self, session):
        """
        Создает сервис администрирования.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def get_users(self) -> List[UserListItem]:
        """
        Возвращает список пользователей системы.
        """
        users = (
            self.session.query(User)
            .options(
                joinedload(User.role),
                joinedload(User.employee),
            )
            .order_by(User.id)
            .all()
        )

        result = []

        for user in users:
            role_name = user.role.name if user.role else "Без роли"
            employee_name = user.employee.full_name if user.employee else "-"

            result.append(
                UserListItem(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    role_name=role_name,
                    employee_name=employee_name,
                    is_active=user.is_active,
                    created_at=user.created_at,
                )
            )

        return result

    def get_roles(self) -> List[RoleListItem]:
        """
        Возвращает список ролей пользователей.
        """
        roles = self.session.query(Role).order_by(Role.name).all()

        return [
            RoleListItem(
                id=role.id,
                name=role.name,
                description=role.description or "",
            )
            for role in roles
        ]

    def set_user_active(self, user_id: int, is_active: bool) -> None:
        """
        Включает или отключает учетную запись пользователя.
        """
        user = (
            self.session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if user is None:
            raise ValueError("Пользователь не найден.")

        user.is_active = is_active
        self.session.commit()