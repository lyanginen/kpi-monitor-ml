"""
Сервис аналитики KPI.

Модуль выполняет расчет аналитических показателей:
- количество сотрудников;
- количество KPI-записей;
- средняя оценка KPI;
- средняя оценка KPI по отделам;
- средняя оценка KPI по сотрудникам.

Сервис используется окном аналитики и отделяет бизнес-логику
от графического интерфейса.
"""

from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from app.database.models import Department, Employee, KpiRecord
from app.services.auth_service import AuthenticatedUser


@dataclass
class DashboardStats:
    """
    Сводные показатели для аналитической панели.
    """

    employees_count: int
    kpi_records_count: int
    average_score: float
    min_score: float
    max_score: float


@dataclass
class DepartmentKpiSummary:
    """
    Средние KPI по отделу.
    """

    department_name: str
    employees_count: int
    records_count: int
    average_score: float


@dataclass
class EmployeeKpiSummary:
    """
    Средние KPI по сотруднику.
    """

    employee_id: int
    employee_name: str
    department_name: str
    records_count: int
    average_score: float


class AnalyticsService:
    """
    Сервис расчета аналитики KPI.
    """

    def __init__(self, session: Session):
        """
        Создает сервис аналитики.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def _get_allowed_employee_ids(self, current_user: AuthenticatedUser) -> List[int]:
        """
        Возвращает список ID сотрудников, доступных текущему пользователю.

        Логика:
        - администратор видит всех сотрудников;
        - руководитель видит сотрудников своего отдела;
        - сотрудник видит только себя.
        """
        if current_user.role_name == "Администратор":
            employees = self.session.query(Employee).all()
            return [employee.id for employee in employees]

        if current_user.role_name == "Сотрудник":
            if current_user.employee_id is None:
                return []

            return [current_user.employee_id]

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

            employees = (
                self.session.query(Employee)
                .filter(Employee.department_id == manager_employee.department_id)
                .all()
            )

            return [employee.id for employee in employees]

        return []

    def get_dashboard_stats(self, current_user: AuthenticatedUser) -> DashboardStats:
        """
        Рассчитывает общие показатели KPI.
        """
        allowed_employee_ids = self._get_allowed_employee_ids(current_user)

        if not allowed_employee_ids:
            return DashboardStats(
                employees_count=0,
                kpi_records_count=0,
                average_score=0.0,
                min_score=0.0,
                max_score=0.0,
            )

        records = (
            self.session.query(KpiRecord)
            .filter(KpiRecord.employee_id.in_(allowed_employee_ids))
            .all()
        )

        employees_count = len(allowed_employee_ids)
        kpi_records_count = len(records)

        if not records:
            return DashboardStats(
                employees_count=employees_count,
                kpi_records_count=0,
                average_score=0.0,
                min_score=0.0,
                max_score=0.0,
            )

        scores = [record.score for record in records]

        return DashboardStats(
            employees_count=employees_count,
            kpi_records_count=kpi_records_count,
            average_score=round(sum(scores) / len(scores), 2),
            min_score=round(min(scores), 2),
            max_score=round(max(scores), 2),
        )

    def get_department_summary(
        self,
        current_user: AuthenticatedUser,
    ) -> List[DepartmentKpiSummary]:
        """
        Рассчитывает средние KPI по отделам.
        """
        allowed_employee_ids = self._get_allowed_employee_ids(current_user)

        if not allowed_employee_ids:
            return []

        departments = self.session.query(Department).order_by(Department.name).all()
        result = []

        for department in departments:
            employees = (
                self.session.query(Employee)
                .filter(Employee.department_id == department.id)
                .filter(Employee.id.in_(allowed_employee_ids))
                .all()
            )

            if not employees:
                continue

            employee_ids = [employee.id for employee in employees]

            records = (
                self.session.query(KpiRecord)
                .filter(KpiRecord.employee_id.in_(employee_ids))
                .all()
            )

            if records:
                average_score = round(
                    sum(record.score for record in records) / len(records),
                    2,
                )
            else:
                average_score = 0.0

            result.append(
                DepartmentKpiSummary(
                    department_name=department.name,
                    employees_count=len(employees),
                    records_count=len(records),
                    average_score=average_score,
                )
            )

        return result

    def get_employee_summary(
        self,
        current_user: AuthenticatedUser,
    ) -> List[EmployeeKpiSummary]:
        """
        Рассчитывает средние KPI по сотрудникам.
        """
        allowed_employee_ids = self._get_allowed_employee_ids(current_user)

        if not allowed_employee_ids:
            return []

        employees = (
            self.session.query(Employee)
            .filter(Employee.id.in_(allowed_employee_ids))
            .order_by(Employee.full_name)
            .all()
        )

        result = []

        for employee in employees:
            records = (
                self.session.query(KpiRecord)
                .filter(KpiRecord.employee_id == employee.id)
                .all()
            )

            if records:
                average_score = round(
                    sum(record.score for record in records) / len(records),
                    2,
                )
            else:
                average_score = 0.0

            department_name = employee.department.name if employee.department else ""

            result.append(
                EmployeeKpiSummary(
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    department_name=department_name,
                    records_count=len(records),
                    average_score=average_score,
                )
            )

        return result