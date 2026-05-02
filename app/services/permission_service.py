"""
Сервис прав доступа.

Модуль определяет, какие разделы системы доступны пользователю
в зависимости от его роли.
"""

from app.services.auth_service import AuthenticatedUser


ROLE_ADMIN = "Администратор"
ROLE_MANAGER = "Руководитель"
ROLE_EMPLOYEE = "Сотрудник"


AVAILABLE_SECTIONS_BY_ROLE = {
    ROLE_ADMIN: [
        "Главная панель",
        "Сотрудники",
        "Отделы",
        "Должности",
        "KPI-показатели",
        "KPI-записи",
        "Аналитика KPI",
        "ML-анализ",
        "Отчеты",
        "Пользователи",
        "Настройки",
        "Журнал действий",
        "Справка",
    ],
    ROLE_MANAGER: [
        "Главная панель",
        "Сотрудники отдела",
        "KPI-записи",
        "Аналитика отдела",
        "ML-прогнозы",
        "Отчеты",
        "Личный кабинет",
        "Справка",
    ],
    ROLE_EMPLOYEE: [
        "Главная панель",
        "Личный кабинет",
        "Мои KPI",
        "Мой ML-прогноз",
        "Мои отчеты",
        "Справка",
    ],
}


def get_available_sections(user: AuthenticatedUser) -> list[str]:
    """
    Возвращает список разделов, доступных пользователю.

    Параметры:
        user: авторизованный пользователь.

    Возвращает:
        список названий разделов приложения.
    """
    return AVAILABLE_SECTIONS_BY_ROLE.get(user.role_name, [])


def can_manage_users(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь управлять учетными записями.
    """
    return user.role_name == ROLE_ADMIN


def can_manage_kpi(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь управлять KPI-записями.
    """
    return user.role_name in [ROLE_ADMIN, ROLE_MANAGER]


def can_train_ml_model(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь запускать обучение ML-модели.
    """
    return user.role_name == ROLE_ADMIN


def can_export_reports(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь формировать отчеты.
    """
    return user.role_name in [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]


def can_open_admin_panel(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь открыть административную панель.
    """
    return user.role_name == ROLE_ADMIN


def can_open_personal_account(user: AuthenticatedUser) -> bool:
    """
    Проверяет, может ли пользователь открыть личный кабинет.
    """
    return user.role_name in [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]