"""
Главное окно приложения KPI Monitor ML.

Это окно открывается после успешной авторизации пользователя.
В нем отображаются:
- ФИО пользователя;
- роль пользователя;
- доступные разделы системы;
- верхнее меню приложения.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.auth_service import AuthenticatedUser
from app.services.permission_service import get_available_sections
from app.ui.employee_list_window import EmployeeListWindow
from app.ui.kpi_list_window import KpiListWindow
from app.ui.analytics_window import AnalyticsWindow
from app.ui.ml_window import MlWindow
from app.ui.reports_window import ReportsWindow
from app.ui.help_window import HelpWindow
from app.ui.settings_window import SettingsWindow
from app.ui.admin_users_window import AdminUsersWindow
from app.ui.personal_account_window import PersonalAccountWindow
from app.ui.audit_log_window import AuditLogWindow


class MainWindow(QMainWindow):
    """
    Главное окно приложения.

    Окно получает данные авторизованного пользователя и строит интерфейс
    с учетом его роли.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает главное окно.

        Параметры:
            current_user: пользователь, который успешно вошел в систему.
        """
        super().__init__()

        self.current_user = current_user

        self.setWindowTitle("KPI Monitor ML — главная панель")
        self.resize(1100, 700)

        self._create_menu_bar()
        self._create_central_widget()

    def _create_menu_bar(self) -> None:
        """
        Создает верхнее меню приложения.

        Меню содержит не менее 5 смысловых пунктов:
        - Файл;
        - Данные;
        - ML-анализ;
        - Отчеты;
        - Справка.
        """
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("Файл")
        data_menu = menu_bar.addMenu("Данные")
        ml_menu = menu_bar.addMenu("ML-анализ")
        reports_menu = menu_bar.addMenu("Отчеты")
        settings_menu = menu_bar.addMenu("Настройки")
        help_menu = menu_bar.addMenu("Справка")

        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)

        employees_action = data_menu.addAction("Сотрудники")
        employees_action.triggered.connect(self._open_employees_window)

        kpi_action = data_menu.addAction("KPI-записи")
        kpi_action.triggered.connect(self._open_kpi_window)

        analytics_action = data_menu.addAction("Аналитика KPI")
        analytics_action.triggered.connect(self._open_analytics_window)

        users_action = data_menu.addAction("Пользователи")
        users_action.triggered.connect(self._open_admin_users_window)

        audit_log_action = data_menu.addAction("Журнал действий")
        audit_log_action.triggered.connect(self._open_audit_log_window)

        personal_account_action = data_menu.addAction("Личный кабинет")
        personal_account_action.triggered.connect(self._open_personal_account_window)

        train_model_action = ml_menu.addAction("Обучение модели")
        train_model_action.triggered.connect(self._open_ml_window)

        prediction_action = ml_menu.addAction("Прогноз KPI")
        prediction_action.triggered.connect(self._open_ml_window)

        docx_report_action = reports_menu.addAction("Сформировать DOCX")
        docx_report_action.triggered.connect(self._open_reports_window)

        xlsx_report_action = reports_menu.addAction("Сформировать XLSX")
        xlsx_report_action.triggered.connect(self._open_reports_window)

        settings_action = settings_menu.addAction("Панель настроек")
        settings_action.triggered.connect(self._open_settings_window)

        backup_action = settings_menu.addAction("Резервное копирование БД")
        backup_action.triggered.connect(self._open_settings_window)

        data_folder_action = settings_menu.addAction("Рабочие папки")
        data_folder_action.triggered.connect(self._open_settings_window)

        app_parameters_action = settings_menu.addAction("Параметры приложения")
        app_parameters_action.triggered.connect(self._open_settings_window)

        model_parameters_action = settings_menu.addAction("Параметры ML-модели")
        model_parameters_action.triggered.connect(self._open_settings_window)

        help_action = help_menu.addAction("Справка по системе")
        help_action.triggered.connect(self._open_help_window)

        about_action = help_menu.addAction("О системе")
        about_action.triggered.connect(self._show_about_dialog)

    def _create_central_widget(self) -> None:
        """
        Создает основную область главного окна.
        """
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        sidebar = self._create_sidebar()
        content = self._create_content_area()

        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(content, 3)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _create_sidebar(self) -> QFrame:
        """
        Создает левую панель с информацией о пользователе и разделами.
        """
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar_layout = QVBoxLayout()

        title_label = QLabel("KPI Monitor ML")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        user_label = QLabel(f"Пользователь:\n{self.current_user.full_name}")
        user_label.setWordWrap(True)

        role_label = QLabel(f"Роль:\n{self.current_user.role_name}")
        role_label.setWordWrap(True)

        sections_label = QLabel("Доступные разделы:")
        sections_label.setStyleSheet("font-weight: bold;")

        self.sections_list = QListWidget()
        available_sections = get_available_sections(self.current_user)

        for section_name in available_sections:
            self.sections_list.addItem(section_name)

        self.sections_list.itemClicked.connect(self._handle_section_click)

        logout_button = QPushButton("Выйти")
        logout_button.clicked.connect(self.close)

        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(user_label)
        sidebar_layout.addWidget(role_label)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(sections_label)
        sidebar_layout.addWidget(self.sections_list)
        sidebar_layout.addWidget(logout_button)

        sidebar.setLayout(sidebar_layout)

        return sidebar

    def _create_content_area(self) -> QFrame:
        """
        Создает правую рабочую область окна.
        """
        content = QFrame()
        content.setFrameShape(QFrame.StyledPanel)

        content_layout = QVBoxLayout()

        welcome_label = QLabel("Главная панель")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setText(
            "Добро пожаловать в систему мониторинга и анализа KPI сотрудников.\n\n"
            "На текущем этапе реализована авторизация, роли пользователей "
            "и главное окно приложения.\n\n"
            "Дальше в эти разделы будут добавлены полноценные формы: сотрудники, "
            "KPI-записи, аналитика, ML-прогнозы, отчеты, настройки и справка."
        )

        content_layout.addWidget(welcome_label)
        content_layout.addWidget(self.content_text)

        content.setLayout(content_layout)

        return content
    
    def _handle_section_click(self, item) -> None:
        """
        Обрабатывает нажатие на раздел в левом меню.
        """
        section_name = item.text()

        if section_name in ["Сотрудники", "Сотрудники отдела"]:
            self._open_employees_window()
            return

        if section_name in ["KPI-записи", "Мои KPI"]:
            self._open_kpi_window()
            return
        
        if section_name in ["Аналитика KPI", "Аналитика отдела"]:
            self._open_analytics_window()
            return
        
        if section_name in ["ML-анализ", "ML-прогнозы", "Мой ML-прогноз"]:
            self._open_ml_window()
            return
        
        if section_name in ["Отчеты", "Мои отчеты"]:
            self._open_reports_window()
            return
        
        if section_name == "Настройки":
            self._open_settings_window()
            return

        if section_name == "Справка":
            self._open_help_window()
            return
        
        if section_name == "Пользователи":
            self._open_admin_users_window()
            return

        if section_name == "Личный кабинет":
            self._open_personal_account_window()
            return
        
        if section_name == "Журнал действий":
            self._open_audit_log_window()
            return

        self._show_section_stub(section_name)

    def _open_employees_window(self) -> None:
        """
        Открывает окно списка сотрудников.

        Список сотрудников будет показан с учетом роли текущего пользователя.
        """
        employees_window = EmployeeListWindow(self.current_user)
        employees_window.exec()

    def _open_kpi_window(self) -> None:
        """
        Открывает окно KPI-записей.

        Данные будут показаны с учетом роли текущего пользователя.
        """
        kpi_window = KpiListWindow(self.current_user)
        kpi_window.exec()

    def _open_analytics_window(self) -> None:
        """
        Открывает окно аналитики KPI.

        Аналитика строится с учетом роли текущего пользователя.
        """
        analytics_window = AnalyticsWindow(self.current_user)
        analytics_window.exec()

    def _open_ml_window(self) -> None:
        """
        Открывает окно ML-анализа и прогноза KPI.
        """
        ml_window = MlWindow(self.current_user)
        ml_window.exec()

    def _open_reports_window(self) -> None:
        """
        Открывает окно формирования отчетов.
        """
        reports_window = ReportsWindow(self.current_user)
        reports_window.exec()
    
    def _open_admin_users_window(self) -> None:
        """
        Открывает админ-панель пользователей.

        Если пользователь не является администратором, раздел не открывается.
        """
        if not self.current_user.is_admin():
            QMessageBox.warning(
                self,
                "Доступ запрещен",
                "Админ-панель доступна только пользователю с ролью Администратор.",
            )
            return

        admin_window = AdminUsersWindow(self.current_user)
        admin_window.exec()

    def _open_audit_log_window(self) -> None:
        """
        Открывает журнал действий пользователей.

        Если пользователь не является администратором, раздел не открывается.
        """
        if not self.current_user.is_admin():
            QMessageBox.warning(
                self,
                "Доступ запрещен",
                "Журнал действий доступен только пользователю с ролью Администратор.",
            )
            return

        audit_log_window = AuditLogWindow(self.current_user)
        audit_log_window.exec()

    def _open_personal_account_window(self) -> None:
        """
        Открывает личный кабинет текущего пользователя.
        """
        personal_account_window = PersonalAccountWindow(self.current_user)
        personal_account_window.exec()

    def _open_settings_window(self) -> None:
        """
        Открывает окно настроек приложения.
        """
        settings_window = SettingsWindow(self.current_user)
        settings_window.exec()

    def _open_help_window(self) -> None:
        """
        Открывает окно справки по системе.
        """
        help_window = HelpWindow(self.current_user)
        help_window.exec()

    def _show_section_stub(self, section_name: str) -> None:
        """
        Временно отображает заглушку выбранного раздела.

        Позже вместо заглушек будут открываться полноценные оконные формы.
        """
        self.content_text.setText(
            f"Раздел: {section_name}\n\n"
            "Функциональность раздела будет реализована на следующих этапах разработки.\n\n"
            "Этот экран уже используется как часть навигации приложения."
        )

    def _show_about_dialog(self) -> None:
        """
        Показывает информацию о системе.
        """
        QMessageBox.information(
            self,
            "О системе",
            "KPI Monitor ML\n\n"
            "Система мониторинга и анализа KPI сотрудников организации "
            "с использованием методов машинного обучения.\n\n"
            "Автор: [указать ФИО автора]\n"
            "Тема ВКР: Разработка системы мониторинга и анализа KPI сотрудников "
            "организации с использованием методов машинного обучения.",
        )