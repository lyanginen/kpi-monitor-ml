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
        help_menu = menu_bar.addMenu("Справка")

        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)

        employees_action = data_menu.addAction("Сотрудники")
        employees_action.triggered.connect(self._open_employees_window)

        kpi_action = data_menu.addAction("KPI-записи")
        kpi_action.triggered.connect(
            lambda: self._show_section_stub("KPI-записи")
        )

        train_model_action = ml_menu.addAction("Обучение модели")
        train_model_action.triggered.connect(
            lambda: self._show_section_stub("Обучение ML-модели")
        )

        prediction_action = ml_menu.addAction("Прогноз KPI")
        prediction_action.triggered.connect(
            lambda: self._show_section_stub("ML-прогноз KPI")
        )

        docx_report_action = reports_menu.addAction("Сформировать DOCX")
        docx_report_action.triggered.connect(
            lambda: self._show_section_stub("Формирование DOCX-отчета")
        )

        xlsx_report_action = reports_menu.addAction("Сформировать XLSX")
        xlsx_report_action.triggered.connect(
            lambda: self._show_section_stub("Формирование XLSX-отчета")
        )

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

        self._show_section_stub(section_name)

    def _open_employees_window(self) -> None:
        """
        Открывает окно списка сотрудников.

        Список сотрудников будет показан с учетом роли текущего пользователя.
        """
        employees_window = EmployeeListWindow(self.current_user)
        employees_window.exec()

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