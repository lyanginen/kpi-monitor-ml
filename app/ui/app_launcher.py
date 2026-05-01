"""
Модуль запуска графического интерфейса приложения.

Здесь создается QApplication, открывается окно авторизации,
а после успешного входа открывается главное окно приложения.
"""

import sys

from PySide6.QtWidgets import QApplication, QDialog

from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow


def start_gui_application() -> None:
    """
    Запускает графическое приложение.
    """
    qt_application = QApplication(sys.argv)

    login_window = LoginWindow()
    login_result = login_window.exec()

    if login_result != QDialog.Accepted:
        sys.exit(0)

    if login_window.authenticated_user is None:
        sys.exit(0)

    main_window = MainWindow(login_window.authenticated_user)
    main_window.show()

    sys.exit(qt_application.exec())