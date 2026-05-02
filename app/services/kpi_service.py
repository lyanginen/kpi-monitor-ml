"""
Сервис работы с KPI-записями.

Модуль отвечает за:
- получение KPI-записей из базы данных;
- фильтрацию KPI с учетом роли пользователя;
- получение сотрудников и KPI-показателей для форм;
- создание новых KPI-записей.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.database.models import Employee, KpiIndicator, KpiRecord
from app.services.auth_service import AuthenticatedUser


@dataclass
class KpiRecordListItem:
    """
    KPI-запись для отображения в таблице интерфейса.
    """

    id: int
    employee_name: str
    department_name: str
    indicator_name: str
    period_start: date
    period_end: date
    actual_value: float
    target_value: float
    score: float


@dataclass
class EmployeeComboItem:
    """
    Сотрудник для выпадающего списка.
    """

    id: int
    full_name: str


@dataclass
class IndicatorComboItem:
    """
    KPI-показатель для выпадающего списка.
    """

    id: int
    name: str
    target_value: float


class KpiService:
    """
    Сервис для работы с KPI.
    """

    def __init__(self, session: Session):
        """
        Создает сервис KPI.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def get_kpi_records_for_user(
        self,
        current_user: AuthenticatedUser,
    ) -> List[KpiRecordListItem]:
        """
        Возвращает список KPI-записей с учетом роли пользователя.

        Логика:
        - администратор видит все KPI-записи;
        - руководитель видит KPI сотрудников своего отдела;
        - сотрудник видит только свои KPI.
        """
        query = (
            self.session.query(KpiRecord)
            .options(
                joinedload(KpiRecord.employee).joinedload(Employee.department),
                joinedload(KpiRecord.indicator),
            )
            .order_by(KpiRecord.period_start.desc())
        )

        if current_user.role_name == "Сотрудник":
            if current_user.employee_id is None:
                return []

            query = query.filter(KpiRecord.employee_id == current_user.employee_id)

        elif current_user.role_name == "Руководитель":
            if current_user.employee_id is None:
                return []

            manager_employee = (
                self.session.query(Employee)
                .filter(Employee.id == current_user.employee_id)
                .first()
            )

            if manager_employee is None:
                return []

            query = query.join(Employee).filter(
                Employee.department_id == manager_employee.department_id
            )

        records = query.all()

        result = []

        for record in records:
            employee = record.employee
            indicator = record.indicator
            department_name = ""

            if employee and employee.department:
                department_name = employee.department.name

            result.append(
                KpiRecordListItem(
                    id=record.id,
                    employee_name=employee.full_name if employee else "",
                    department_name=department_name,
                    indicator_name=indicator.name if indicator else "",
                    period_start=record.period_start,
                    period_end=record.period_end,
                    actual_value=record.actual_value,
                    target_value=record.target_value,
                    score=record.score,
                )
            )

        return result

    def get_available_employees_for_user(
        self,
        current_user: AuthenticatedUser,
    ) -> List[EmployeeComboItem]:
        """
        Возвращает сотрудников, для которых пользователь может добавлять KPI.

        Администратор может выбрать любого сотрудника.
        Руководитель может выбрать сотрудника своего отдела.
        Сотрудник не должен добавлять KPI вручную, поэтому получает пустой список.
        """
        if current_user.role_name == "Сотрудник":
            return []

        query = self.session.query(Employee).order_by(Employee.full_name)

        if current_user.role_name == "Руководитель":
            if current_user.employee_id is None:
                return []

            manager_employee = (
                self.session.query(Employee)
                .filter(Employee.id == current_user.employee_id)
                .first()
            )

            if manager_employee is None:
                return []

            query = query.filter(Employee.department_id == manager_employee.department_id)

        employees = query.all()

        return [
            EmployeeComboItem(
                id=employee.id,
                full_name=employee.full_name,
            )
            for employee in employees
        ]

    def get_indicators(self) -> List[IndicatorComboItem]:
        """
        Возвращает список KPI-показателей.
        """
        indicators = (
            self.session.query(KpiIndicator)
            .order_by(KpiIndicator.name)
            .all()
        )

        return [
            IndicatorComboItem(
                id=indicator.id,
                name=indicator.name,
                target_value=indicator.target_value or 0.0,
            )
            for indicator in indicators
        ]

    def get_indicator_target_value(self, indicator_id: int) -> float:
        """
        Возвращает целевое значение KPI-показателя.
        """
        indicator = (
            self.session.query(KpiIndicator)
            .filter(KpiIndicator.id == indicator_id)
            .first()
        )

        if indicator is None:
            return 0.0

        return indicator.target_value or 0.0

    def calculate_score(self, actual_value: float, target_value: float) -> float:
        """
        Рассчитывает оценку KPI.

        Если фактическое значение равно плановому, score будет равен 100.
        Если фактическое значение выше плана, score может быть выше 100,
        но ограничивается значением 120.
        """
        if target_value <= 0:
            return 0.0

        score = actual_value / target_value * 100

        return min(round(score, 2), 120.0)

    def create_kpi_record(
        self,
        employee_id: int,
        indicator_id: int,
        period_start: date,
        period_end: date,
        actual_value: float,
        target_value: float,
        comment: str,
    ) -> KpiRecord:
        """
        Создает новую KPI-запись.

        Параметры:
            employee_id: ID сотрудника.
            indicator_id: ID KPI-показателя.
            period_start: начало периода.
            period_end: конец периода.
            actual_value: фактическое значение.
            target_value: плановое значение.
            comment: комментарий к записи.

        Возвращает:
            созданную KPI-запись.
        """
        if period_end < period_start:
            raise ValueError("Дата окончания периода не может быть раньше даты начала.")

        score = self.calculate_score(actual_value, target_value)

        record = KpiRecord(
            employee_id=employee_id,
            indicator_id=indicator_id,
            period_start=period_start,
            period_end=period_end,
            actual_value=actual_value,
            target_value=target_value,
            score=score,
            comment=comment,
        )

        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)

        return record