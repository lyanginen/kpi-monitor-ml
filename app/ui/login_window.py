"""
Окно авторизации приложения.

Пользователь вводит логин и пароль.
После успешной проверки приложение передает данные пользователя
в главное окно.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthService, AuthenticatedUser
from app.services.audit_service import AuditService


class LoginWindow(QDialog):
    """
    Окно входа в систему.
    """

    def __init__(self):
        """
        Создает окно авторизации.
        """
        super().__init__()

        self.authenticated_user: Optional[AuthenticatedUser] = None

        self.setWindowTitle("KPI Monitor ML — вход в систему")
        self.resize(420, 260)
        self._create_interface()

    def _create_interface(self) -> None:
        """
        Создает элементы интерфейса окна авторизации.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("KPI Monitor ML")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        subtitle_label = QLabel("Вход в систему мониторинга KPI")
        subtitle_label.setAlignment(Qt.AlignCenter)

        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Например: admin")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Например: admin123")
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Логин:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self._handle_login)

        hint_label = QLabel(
            "Тестовые учетные записи:\n"
            "admin / admin123\n"
            "manager / manager123\n"
            "employee / employee123"
        )
        hint_label.setStyleSheet("color: gray;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(login_button)
        main_layout.addSpacing(10)
        main_layout.addWidget(hint_label)

        self.setLayout(main_layout)

        self.username_input.returnPressed.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)

    def _handle_login(self) -> None:
        """
        Обрабатывает нажатие кнопки входа.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Ошибка входа",
                "Введите логин и пароль.",
            )
            return

        session = SessionLocal()

        try:
            auth_service = AuthService(session)
            user = auth_service.authenticate(username, password)

            if user is None:
                QMessageBox.warning(
                    self,
                    "Ошибка входа",
                    "Неверный логин, пароль или учетная запись отключена.",
                )
                return

            audit_service = AuditService(session)
            audit_service.log_action(
                user_id=user.id,
                action="Успешная авторизация",
                entity_name="User",
                entity_id=user.id,
                details=f"Пользователь {user.username} выполнил вход в систему.",
            )

            self.authenticated_user = user
            self.accept()

        finally:
            session.close()