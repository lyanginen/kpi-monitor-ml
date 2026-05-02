"""
Окно справки по системе.

Окно содержит:
- назначение системы;
- описание ролей пользователей;
- описание основных разделов;
- сведения об авторе и теме ВКР.
"""

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.services.auth_service import AuthenticatedUser


class HelpWindow(QDialog):
    """
    Окно справки по системе.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно справки.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user

        self.setWindowTitle("KPI Monitor ML — справка по системе")
        self.resize(850, 650)

        self._create_interface()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна справки.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Справка по системе")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setText(self._build_help_text())

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.help_text)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _build_help_text(self) -> str:
        """
        Формирует текст справки.
        """
        return (
            "KPI Monitor ML\n"
            "============================================================\n\n"
            "Тема ВКР:\n"
            "Разработка системы мониторинга и анализа KPI сотрудников организации "
            "с использованием методов машинного обучения.\n\n"
            "Автор работы:\n"
            "Лянгинен Илья Борисович\n\n"
            "Назначение системы:\n"
            "Приложение предназначено для хранения, мониторинга и анализа KPI "
            "сотрудников организации. Система позволяет учитывать сотрудников, "
            "подразделения, должности, KPI-показатели, исторические KPI-записи, "
            "формировать отчеты и выполнять прогнозирование риска снижения KPI "
            "с использованием модели машинного обучения.\n\n"
            "Роли пользователей:\n"
            "1. Администратор — имеет доступ ко всем разделам системы, может "
            "работать с пользователями, настройками, отчетами и ML-модулем.\n"
            "2. Руководитель — работает с сотрудниками своего отдела, KPI-записями, "
            "аналитикой отдела и отчетами.\n"
            "3. Сотрудник — просматривает личный кабинет, собственные KPI и "
            "персональный ML-прогноз.\n\n"
            "Основные разделы системы:\n"
            "- Сотрудники — просмотр сотрудников и карточек сотрудников.\n"
            "- KPI-записи — просмотр и добавление KPI-показателей.\n"
            "- Аналитика KPI — сводные показатели, аналитика по отделам и сотрудникам.\n"
            "- ML-анализ — обучение модели RandomForestClassifier и прогноз риска KPI.\n"
            "- Отчеты — формирование DOCX и XLSX документов.\n"
            "- Настройки — управление параметрами приложения и резервное копирование БД.\n"
            "- Справка — описание назначения системы и порядка работы.\n\n"
            "Машинное обучение:\n"
            "В системе используется модель RandomForestClassifier. "
            "Модель решает задачу классификации риска снижения KPI сотрудника. "
            "В качестве признаков используются исторические KPI-оценки, "
            "а результатом является один из классов: низкий риск, средний риск "
            "или высокий риск.\n\n"
            "Файловая структура:\n"
            "- main.py — точка входа в приложение.\n"
            "- requirements.txt — список зависимостей.\n"
            "- data/kpi_monitor.db — база данных SQLite.\n"
            "- models/model.pkl — сохраненная ML-модель.\n"
            "- exports/ — папка сформированных отчетов.\n\n"
            "Текущий пользователь:\n"
            f"{self.current_user.full_name}\n"
            f"Роль: {self.current_user.role_name}\n\n"
            "Тестовые учетные записи:\n"
            "admin / admin123\n"
            "manager / manager123\n"
            "employee / employee123\n"
        )