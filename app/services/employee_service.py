"""
Сервис работы с сотрудниками.

Модуль содержит бизнес-логику получения сотрудников из базы данных.
Сервис используется графическим интерфейсом, чтобы не писать SQL-запросы
прямо в окнах приложения.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.database.models import Employee, KpiRecord
from app.services.auth_service import AuthenticatedUser


@dataclass
class EmployeeListItem:
    """
    Краткая информация о сотруднике для отображения в таблице.
    """

    id: int
    personnel_number: str
    full_name: str
    department_name: str
    position_name: str
    email: str
    is_active: bool


@dataclass
class EmployeeDetails:
    """
    Полная информация о сотруднике для карточки сотрудника.
    """

    id: int
    personnel_number: str
    full_name: str
    email: str
    phone: str
    hire_date: Optional[date]
    department_name: str
    position_name: str
    is_active: bool


@dataclass
class EmployeeKpiRecordItem:
    """
    KPI-запись сотрудника для отображения в карточке.
    """

    indicator_name: str
    period_start: date
    period_end: date
    actual_value: float
    target_value: float
    score: float


class EmployeeService:
    """
    Сервис получения данных о сотрудниках.
    """

    def __init__(self, session: Session):
        """
        Создает сервис сотрудников.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def get_employees_for_user(
        self,
        current_user: AuthenticatedUser,
    ) -> list[EmployeeListItem]:
        """
        Возвращает список сотрудников с учетом роли пользователя.

        Логика:
        - администратор видит всех сотрудников;
        - руководитель видит сотрудников своего отдела;
        - сотрудник видит только себя.
        """
        query = (
            self.session.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position),
            )
            .order_by(Employee.full_name)
        )

        if current_user.role_name == "Сотрудник":
            if current_user.employee_id is None:
                return []

            query = query.filter(Employee.id == current_user.employee_id)

        elif current_user.role_name == "Руководитель":
            if current_user.employee_id is None:
                return []

            manager_employee = self.session.query(Employee).filter(
                Employee.id == current_user.employee_id
            ).first()

            if manager_employee is None:
                return []

            query = query.filter(Employee.department_id == manager_employee.department_id)

        employees = query.all()

        return [
            EmployeeListItem(
                id=employee.id,
                personnel_number=employee.personnel_number,
                full_name=employee.full_name,
                department_name=employee.department.name if employee.department else "",
                position_name=employee.position.name if employee.position else "",
                email=employee.email or "",
                is_active=employee.is_active,
            )
            for employee in employees
        ]

    def get_employee_details(self, employee_id: int) -> Optional[EmployeeDetails]:
        """
        Возвращает подробную информацию о сотруднике.
        """
        employee = (
            self.session.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position),
            )
            .filter(Employee.id == employee_id)
            .first()
        )

        if employee is None:
            return None

        return EmployeeDetails(
            id=employee.id,
            personnel_number=employee.personnel_number,
            full_name=employee.full_name,
            email=employee.email or "",
            phone=employee.phone or "",
            hire_date=employee.hire_date,
            department_name=employee.department.name if employee.department else "",
            position_name=employee.position.name if employee.position else "",
            is_active=employee.is_active,
        )

    def get_employee_kpi_records(
        self,
        employee_id: int,
    ) -> list[EmployeeKpiRecordItem]:
        """
        Возвращает KPI-записи сотрудника.
        """
        records = (
            self.session.query(KpiRecord)
            .options(joinedload(KpiRecord.indicator))
            .filter(KpiRecord.employee_id == employee_id)
            .order_by(KpiRecord.period_start.desc())
            .all()
        )

        return [
            EmployeeKpiRecordItem(
                indicator_name=record.indicator.name if record.indicator else "",
                period_start=record.period_start,
                period_end=record.period_end,
                actual_value=record.actual_value,
                target_value=record.target_value,
                score=record.score,
            )
            for record in records
        ]