"""
Модели базы данных системы мониторинга KPI.

Каждый класс в этом файле соответствует отдельной таблице в базе данных.
База данных описывает пользователей, сотрудников, отделы, KPI-показатели,
результаты машинного обучения, отчеты, настройки и журнал действий.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Role(Base):
    """
    Роль пользователя в системе.

    Примеры ролей:
    - администратор;
    - руководитель;
    - сотрудник.
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    """
    Учетная запись пользователя.

    Через эту таблицу реализуется вход в приложение и разграничение прав доступа.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")


class Department(Base):
    """
    Подразделение организации.

    Используется для группировки сотрудников и анализа KPI по отделам.
    """

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    employees = relationship("Employee", back_populates="department")


class Position(Base):
    """
    Должность сотрудника.

    Позволяет учитывать роль сотрудника внутри организации.
    """

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    employees = relationship("Employee", back_populates="position")


class Employee(Base):
    """
    Сотрудник организации.

    Основная сущность предметной области.
    Для сотрудника хранятся личные данные, отдел, должность и KPI-записи.
    """

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    personnel_number = Column(String(50), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    hire_date = Column(Date, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    kpi_records = relationship("KpiRecord", back_populates="employee")
    predictions = relationship("MlPrediction", back_populates="employee")
    user = relationship("User", back_populates="employee", uselist=False)


class KpiIndicator(Base):
    """
    Справочник KPI-показателей.

    Примеры показателей:
    - выполнение плана;
    - качество работы;
    - соблюдение сроков;
    - количество выполненных задач.
    """

    __tablename__ = "kpi_indicators"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)
    target_value = Column(Float, nullable=True)
    weight = Column(Float, default=1.0)

    records = relationship("KpiRecord", back_populates="indicator")


class KpiRecord(Base):
    """
    Значение KPI сотрудника за определенный период.

    Эта таблица хранит исторические данные, на основе которых строится аналитика
    и обучается модель машинного обучения.
    """

    __tablename__ = "kpi_records"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("kpi_indicators.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    actual_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="kpi_records")
    indicator = relationship("KpiIndicator", back_populates="records")


class MlModelInfo(Base):
    """
    Информация об обученной ML-модели.

    Таблица нужна, чтобы фиксировать версию модели, путь к файлу модели
    и краткое описание алгоритма.
    """

    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    algorithm = Column(String(150), nullable=False)
    model_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)

    metrics = relationship("ModelMetric", back_populates="model")
    predictions = relationship("MlPrediction", back_populates="model")


class ModelMetric(Base):
    """
    Метрики качества ML-модели.

    Например:
    - accuracy;
    - precision;
    - recall;
    - f1-score.
    """

    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    measured_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("MlModelInfo", back_populates="metrics")


class MlPrediction(Base):
    """
    Результат прогноза ML-модели для сотрудника.

    Например, модель может прогнозировать риск снижения KPI:
    низкий, средний или высокий.
    """

    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    prediction_label = Column(String(100), nullable=False)
    prediction_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="predictions")
    model = relationship("MlModelInfo", back_populates="predictions")


class Report(Base):
    """
    Сформированный отчет.

    Таблица хранит сведения о документах, созданных приложением:
    например DOCX или XLSX-отчетах.
    """

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    """
    Настройки приложения.

    Например:
    - путь к папке отчетов;
    - тема интерфейса;
    - параметры отображения;
    - настройки модели.
    """

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(150), nullable=False, unique=True)
    setting_value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)


class AuditLog(Base):
    """
    Журнал действий пользователей.

    Нужен для фиксации важных событий:
    вход в систему, изменение KPI, запуск обучения модели, экспорт отчетов.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    entity_name = Column(String(150), nullable=True)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    user = relationship("User", back_populates="audit_logs")