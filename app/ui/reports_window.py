"""
Окно отчетов.

Окно позволяет:
- сформировать DOCX-отчет по KPI;
- сформировать XLSX-отчет с аналитикой;
- посмотреть список ранее сформированных отчетов;
- открыть папку exports в файловой системе.
"""

import os
import platform
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthenticatedUser
from app.services.report_service import EXPORTS_DIR, ReportService
from app.services.audit_service import AuditService


class ReportsWindow(QDialog):
    """
    Окно формирования отчетов.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно отчетов.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user
        self.reports = []

        self.setWindowTitle("KPI Monitor ML — отчеты")
        self.resize(1000, 620)

        self._create_interface()
        self._load_reports()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна отчетов.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("Отчеты")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            "В этом разделе можно сформировать отчеты по KPI сотрудников "
            "в форматах DOCX и XLSX."
        )
        description_label.setWordWrap(True)

        button_layout = QHBoxLayout()

        docx_button = QPushButton("Сформировать DOCX")
        docx_button.clicked.connect(self._generate_docx_report)

        xlsx_button = QPushButton("Сформировать XLSX")
        xlsx_button.clicked.connect(self._generate_xlsx_report)

        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self._load_reports)

        open_folder_button = QPushButton("Открыть папку exports")
        open_folder_button.clicked.connect(self._open_exports_folder)

        button_layout.addWidget(docx_button)
        button_layout.addWidget(xlsx_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(open_folder_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Название",
                "Тип",
                "Путь к файлу",
                "Дата создания",
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _generate_docx_report(self) -> None:
        """
        Формирует DOCX-отчет.
        """
        session = SessionLocal()

        try:
            service = ReportService(session)
            result = service.generate_kpi_docx_report(self.current_user)

            audit_service = AuditService(session)
            audit_service.log_action(
                user_id=self.current_user.id,
                action="Формирование DOCX-отчета",
                entity_name="Report",
                entity_id=None,
                details=f"Сформирован DOCX-отчет: {result.file_path}",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка формирования отчета",
                f"Не удалось сформировать DOCX-отчет.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Отчет сформирован",
            f"Файл успешно создан:\n{result.file_path}",
        )

        self._load_reports()

    def _generate_xlsx_report(self) -> None:
        """
        Формирует XLSX-отчет.
        """
        session = SessionLocal()

        try:
            service = ReportService(session)
            result = service.generate_analytics_xlsx_report(self.current_user)

            audit_service = AuditService(session)
            audit_service.log_action(
                user_id=self.current_user.id,
                action="Формирование XLSX-отчета",
                entity_name="Report",
                entity_id=None,
                details=f"Сформирован XLSX-отчет: {result.file_path}",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка формирования отчета",
                f"Не удалось сформировать XLSX-отчет.\n\n{error}",
            )
            return

        finally:
            session.close()

        QMessageBox.information(
            self,
            "Отчет сформирован",
            f"Файл успешно создан:\n{result.file_path}",
        )

        self._load_reports()

    def _load_reports(self) -> None:
        """
        Загружает список сформированных отчетов из базы данных.
        """
        session = SessionLocal()

        try:
            service = ReportService(session)
            self.reports = service.get_reports()

        finally:
            session.close()

        self.table.setRowCount(len(self.reports))

        for row_index, report in enumerate(self.reports):
            self._set_table_item(row_index, 0, str(report.id))
            self._set_table_item(row_index, 1, report.report_name)
            self._set_table_item(row_index, 2, report.report_type)
            self._set_table_item(row_index, 3, report.file_path)
            self._set_table_item(
                row_index,
                4,
                report.created_at.strftime("%d.%m.%Y %H:%M"),
            )

        self.table.resizeColumnsToContents()

    def _open_exports_folder(self) -> None:
        """
        Открывает папку exports в файловой системе.

        Реализована поддержка macOS, Windows и Linux.
        """
        EXPORTS_DIR.mkdir(exist_ok=True)

        system_name = platform.system()

        try:
            if system_name == "Windows":
                os.startfile(EXPORTS_DIR)
            elif system_name == "Darwin":
                subprocess.run(["open", str(EXPORTS_DIR)], check=False)
            else:
                subprocess.run(["xdg-open", str(EXPORTS_DIR)], check=False)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка открытия папки",
                f"Не удалось открыть папку exports.\n\n{error}",
            )

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение в ячейку таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, column, item)