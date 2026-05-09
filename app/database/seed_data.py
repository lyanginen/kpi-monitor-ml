"""
Скрипт заполнения базы данных тестовыми данными.

Назначение:
- создать роли пользователей;
- создать отделы и должности;
- создать сотрудников;
- создать KPI-показатели;
- создать историю KPI;
- создать тестовых пользователей для входа в систему;
- создать базовые настройки приложения.

Этот файл нужен для демонстрации работы приложения проверяющему.
"""

from datetime import date

from app.database.connection import SessionLocal
from app.database.init_db import init_database
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
from app.utils.security import hash_password


def get_or_create_by_name(session, model, name: str, **kwargs):
    """
    Получает объект по полю name или создает его, если он еще не существует.

    Параметры:
        session: текущая сессия SQLAlchemy.
        model: ORM-класс таблицы.
        name: значение поля name.
        kwargs: дополнительные поля для создания объекта.

    Возвращает:
        найденный или созданный объект.
    """
    existing_object = session.query(model).filter(model.name == name).first()

    if existing_object:
        return existing_object

    new_object = model(name=name, **kwargs)
    session.add(new_object)
    session.flush()

    return new_object


def create_roles(session):
    """
    Создает роли пользователей.

    В системе используется 3 уровня доступа:
    - администратор;
    - руководитель;
    - сотрудник.
    """
    admin_role = get_or_create_by_name(
        session,
        Role,
        "Администратор",
        description="Полный доступ к системе, пользователям, справочникам и ML-модулю.",
    )

    manager_role = get_or_create_by_name(
        session,
        Role,
        "Руководитель",
        description="Доступ к сотрудникам подразделения, KPI и аналитическим отчетам.",
    )

    employee_role = get_or_create_by_name(
        session,
        Role,
        "Сотрудник",
        description="Доступ к личному кабинету, собственным KPI и персональному прогнозу.",
    )

    return admin_role, manager_role, employee_role


def create_departments(session):
    """
    Создает подразделения организации.
    """
    departments = [
        ("Отдел продаж", "Подразделение, отвечающее за продажи и работу с клиентами."),
        ("ИТ-отдел", "Подразделение, отвечающее за разработку и сопровождение ИТ-систем."),
        ("Отдел поддержки", "Подразделение, отвечающее за обработку обращений пользователей."),
        ("HR-отдел", "Подразделение, отвечающее за подбор, адаптацию и развитие персонала."),
    ]

    result = []

    for name, description in departments:
        department = get_or_create_by_name(
            session,
            Department,
            name,
            description=description,
        )
        result.append(department)

    return result


def create_positions(session):
    """
    Создает должности сотрудников.
    """
    positions = [
        ("Специалист по продажам", "Сотрудник, выполняющий план продаж."),
        ("Backend-разработчик", "Сотрудник, разрабатывающий серверную часть информационных систем."),
        ("Специалист поддержки", "Сотрудник, обрабатывающий обращения пользователей."),
        ("HR-специалист", "Сотрудник, отвечающий за HR-процессы."),
        ("Руководитель отдела", "Сотрудник, управляющий подразделением."),
    ]

    result = []

    for name, description in positions:
        position = get_or_create_by_name(
            session,
            Position,
            name,
            description=description,
        )
        result.append(position)

    return result


def create_kpi_indicators(session):
    """
    Создает справочник KPI-показателей.

    Каждый показатель имеет:
    - название;
    - единицу измерения;
    - целевое значение;
    - вес в общей оценке.
    """
    indicators = [
        {
            "name": "Выполнение плана",
            "description": "Процент выполнения индивидуального или отделенческого плана.",
            "unit": "%",
            "target_value": 100.0,
            "weight": 0.30,
        },
        {
            "name": "Качество работы",
            "description": "Оценка качества выполненных задач по внутренней шкале.",
            "unit": "%",
            "target_value": 90.0,
            "weight": 0.25,
        },
        {
            "name": "Соблюдение сроков",
            "description": "Доля задач, выполненных без нарушения сроков.",
            "unit": "%",
            "target_value": 95.0,
            "weight": 0.20,
        },
        {
            "name": "Производительность",
            "description": "Количество выполненных задач относительно установленной нормы.",
            "unit": "%",
            "target_value": 100.0,
            "weight": 0.15,
        },
        {
            "name": "Командное взаимодействие",
            "description": "Оценка участия сотрудника в командной работе.",
            "unit": "%",
            "target_value": 85.0,
            "weight": 0.10,
        },
    ]

    result = []

    for item in indicators:
        existing_indicator = session.query(KpiIndicator).filter(
            KpiIndicator.name == item["name"]
        ).first()

        if existing_indicator:
            result.append(existing_indicator)
            continue

        indicator = KpiIndicator(
            name=item["name"],
            description=item["description"],
            unit=item["unit"],
            target_value=item["target_value"],
            weight=item["weight"],
        )

        session.add(indicator)
        session.flush()
        result.append(indicator)

    return result


def create_employees(session, departments, positions):
    """
    Создает тестовых сотрудников организации.

    Данные не являются случайными: они заданы вручную и нужны для демонстрации
    структуры предметной области.
    """
    employees_data = [
        {
            "personnel_number": "EMP-001",
            "full_name": "Иванов Сергей Петрович",
            "email": "ivanov@example.local",
            "phone": "+7 900 000-00-01",
            "hire_date": date(2021, 3, 15),
            "department": "Отдел продаж",
            "position": "Специалист по продажам",
        },
        {
            "personnel_number": "EMP-002",
            "full_name": "Петрова Анна Викторовна",
            "email": "petrova@example.local",
            "phone": "+7 900 000-00-02",
            "hire_date": date(2020, 7, 10),
            "department": "ИТ-отдел",
            "position": "Backend-разработчик",
        },
        {
            "personnel_number": "EMP-003",
            "full_name": "Сидоров Максим Андреевич",
            "email": "sidorov@example.local",
            "phone": "+7 900 000-00-03",
            "hire_date": date(2022, 1, 20),
            "department": "Отдел поддержки",
            "position": "Специалист поддержки",
        },
        {
            "personnel_number": "EMP-004",
            "full_name": "Кузнецова Мария Олеговна",
            "email": "kuznetsova@example.local",
            "phone": "+7 900 000-00-04",
            "hire_date": date(2019, 11, 5),
            "department": "HR-отдел",
            "position": "HR-специалист",
        },
        {
            "personnel_number": "EMP-005",
            "full_name": "Смирнов Алексей Игоревич",
            "email": "smirnov@example.local",
            "phone": "+7 900 000-00-05",
            "hire_date": date(2018, 6, 1),
            "department": "ИТ-отдел",
            "position": "Руководитель отдела",
        },
    ]

    department_by_name = {department.name: department for department in departments}
    position_by_name = {position.name: position for position in positions}

    result = []

    for item in employees_data:
        existing_employee = session.query(Employee).filter(
            Employee.personnel_number == item["personnel_number"]
        ).first()

        if existing_employee:
            result.append(existing_employee)
            continue

        employee = Employee(
            personnel_number=item["personnel_number"],
            full_name=item["full_name"],
            email=item["email"],
            phone=item["phone"],
            hire_date=item["hire_date"],
            department_id=department_by_name[item["department"]].id,
            position_id=position_by_name[item["position"]].id,
            is_active=True,
        )

        session.add(employee)
        session.flush()
        result.append(employee)

    return result


def calculate_kpi_score(actual_value: float, target_value: float) -> float:
    """
    Рассчитывает нормированную оценку KPI.

    Если фактическое значение равно целевому, сотрудник получает 100 баллов.
    Если больше целевого — оценка может быть выше 100, но ограничивается 120.
    """
    if target_value <= 0:
        return 0.0

    score = actual_value / target_value * 100

    return min(round(score, 2), 120.0)


def create_kpi_records(session, employees, indicators):
    """
    Создает историю KPI для сотрудников за несколько месяцев.

    Данные заданы вручную по шаблону, чтобы можно было показать:
    - стабильных сотрудников;
    - сотрудников с ростом KPI;
    - сотрудников с риском снижения KPI.
    """
    periods = [
        (date(2025, 9, 1), date(2025, 9, 30)),
        (date(2025, 10, 1), date(2025, 10, 31)),
        (date(2025, 11, 1), date(2025, 11, 30)),
        (date(2025, 12, 1), date(2025, 12, 31)),
        (date(2026, 1, 1), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
    ]

    employee_base_values = {
        "EMP-001": [92, 95, 97, 96, 98, 101],
        "EMP-002": [88, 90, 93, 95, 97, 99],
        "EMP-003": [84, 82, 80, 78, 75, 73],
        "EMP-004": [91, 92, 91, 93, 94, 95],
        "EMP-005": [96, 97, 98, 97, 99, 100],
    }

    indicator_offsets = {
        "Выполнение плана": 0,
        "Качество работы": -3,
        "Соблюдение сроков": 2,
        "Производительность": -1,
        "Командное взаимодействие": 1,
    }

    created_count = 0

    for employee in employees:
        base_values = employee_base_values[employee.personnel_number]

        for period_index, period in enumerate(periods):
            period_start, period_end = period

            for indicator in indicators:
                existing_record = session.query(KpiRecord).filter(
                    KpiRecord.employee_id == employee.id,
                    KpiRecord.indicator_id == indicator.id,
                    KpiRecord.period_start == period_start,
                    KpiRecord.period_end == period_end,
                ).first()

                if existing_record:
                    continue

                offset = indicator_offsets.get(indicator.name, 0)
                actual_value = float(base_values[period_index] + offset)
                target_value = float(indicator.target_value)
                score = calculate_kpi_score(actual_value, target_value)

                record = KpiRecord(
                    employee_id=employee.id,
                    indicator_id=indicator.id,
                    period_start=period_start,
                    period_end=period_end,
                    actual_value=actual_value,
                    target_value=target_value,
                    score=score,
                    comment="Тестовая запись KPI для демонстрации работы системы.",
                )

                session.add(record)
                created_count += 1

    return created_count


def create_users(session, roles, employees):
    """
    Создает тестовые учетные записи.

    Учетные данные понадобятся для демонстрации ролей:
    - admin / admin123
    - manager / manager123
    - employee / employee123
    """
    admin_role, manager_role, employee_role = roles

    employee_by_number = {
        employee.personnel_number: employee
        for employee in employees
    }

    users = [
        {
            "username": "admin",
            "password": "admin123",
            "full_name": "Администратор системы",
            "role": admin_role,
            "employee": None,
        },
        {
            "username": "manager",
            "password": "manager123",
            "full_name": "Смирнов Алексей Игоревич",
            "role": manager_role,
            "employee": employee_by_number["EMP-005"],
        },
        {
            "username": "employee",
            "password": "employee123",
            "full_name": "Петрова Анна Викторовна",
            "role": employee_role,
            "employee": employee_by_number["EMP-002"],
        },
    ]

    for item in users:
        existing_user = session.query(User).filter(
            User.username == item["username"]
        ).first()

        if existing_user:
            continue

        user = User(
            username=item["username"],
            password_hash=hash_password(item["password"]),
            full_name=item["full_name"],
            role_id=item["role"].id,
            employee_id=item["employee"].id if item["employee"] else None,
            is_active=True,
        )

        session.add(user)


def create_settings(session):
    """
    Создает базовые настройки приложения.
    """
    settings = [
        {
            "setting_key": "reports_directory",
            "setting_value": "exports",
            "description": "Папка для сохранения отчетов.",
        },
        {
            "setting_key": "application_theme",
            "setting_value": "light",
            "description": "Тема интерфейса приложения.",
        },
        {
            "setting_key": "model_file_path",
            "setting_value": "models/model.pkl",
            "description": "Путь к файлу обученной ML-модели.",
        },
        {
            "setting_key": "default_accuracy_threshold",
            "setting_value": "0.70",
            "description": "Минимальный ожидаемый уровень точности модели.",
        },
        {
            "setting_key": "author_name",
            "setting_value": "Лянгинен Илья Борисович",
            "description": "ФИО автора выпускной квалификационной работы.",
        },
    ]

    for item in settings:
        existing_setting = session.query(AppSetting).filter(
            AppSetting.setting_key == item["setting_key"]
        ).first()

        if existing_setting:
            continue

        setting = AppSetting(
            setting_key=item["setting_key"],
            setting_value=item["setting_value"],
            description=item["description"],
        )

        session.add(setting)


def create_audit_log(session):
    """
    Создает первую запись в журнале действий.
    """
    existing_log = session.query(AuditLog).filter(
        AuditLog.action == "Первичное заполнение базы данных"
    ).first()

    if existing_log:
        return

    log = AuditLog(
        user_id=None,
        action="Первичное заполнение базы данных",
        entity_name="Database",
        entity_id=None,
        details="Созданы роли, пользователи, сотрудники, KPI-показатели и тестовые KPI-записи.",
    )

    session.add(log)


def seed_database() -> None:
    """
    Основная функция заполнения базы данных.
    """
    init_database()

    session = SessionLocal()

    try:
        roles = create_roles(session)
        departments = create_departments(session)
        positions = create_positions(session)
        indicators = create_kpi_indicators(session)
        employees = create_employees(session, departments, positions)

        created_kpi_records = create_kpi_records(session, employees, indicators)

        create_users(session, roles, employees)
        create_settings(session)
        create_audit_log(session)

        session.commit()

        print("База данных успешно заполнена тестовыми данными.")
        print(f"Создано или проверено ролей: {len(roles)}")
        print(f"Создано или проверено отделов: {len(departments)}")
        print(f"Создано или проверено должностей: {len(positions)}")
        print(f"Создано или проверено сотрудников: {len(employees)}")
        print(f"Создано или проверено KPI-показателей: {len(indicators)}")
        print(f"Создано новых KPI-записей: {created_kpi_records}")
        print("Тестовые пользователи:")
        print("  admin / admin123")
        print("  manager / manager123")
        print("  employee / employee123")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    seed_database()