"""
Сервис журнала действий пользователей.

Модуль отвечает за:
- запись событий в журнал действий;
- получение списка действий пользователей;
- подготовку данных для административного окна журнала.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload

from app.database.models import AuditLog, User


@dataclass
class AuditLogItem:
    """
    Запись журнала действий для отображения в интерфейсе.
    """

    id: int
    user_name: str
    action: str
    entity_name: str
    entity_id: Optional[int]
    created_at: datetime
    details: str


class AuditService:
    """
    Сервис работы с журналом действий.
    """

    def __init__(self, session):
        """
        Создает сервис журнала действий.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        entity_name: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        Добавляет запись в журнал действий.

        Параметры:
            user_id: ID пользователя, который выполнил действие.
            action: краткое название действия.
            entity_name: название сущности, с которой связано действие.
            entity_id: ID сущности.
            details: подробное описание события.
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            details=details,
        )

        self.session.add(log)
        self.session.commit()

    def get_logs(self, limit: int = 200) -> List[AuditLogItem]:
        """
        Возвращает последние записи журнала действий.

        Параметры:
            limit: максимальное количество записей.
        """
        logs = (
            self.session.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []

        for log in logs:
            user_name = "Система"

            if log.user:
                user_name = log.user.full_name

            result.append(
                AuditLogItem(
                    id=log.id,
                    user_name=user_name,
                    action=log.action,
                    entity_name=log.entity_name or "-",
                    entity_id=log.entity_id,
                    created_at=log.created_at,
                    details=log.details or "",
                )
            )

        return result