"""
Окно ML-анализа KPI.

Окно позволяет:
- обучить модель машинного обучения;
- сохранить модель в файл model.pkl;
- посмотреть метрики качества;
- выполнить прогноз риска KPI по сотрудникам.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import AuthenticatedUser
from app.services.ml_service import MlService
from app.services.permission_service import can_train_ml_model
from app.services.audit_service import AuditService


class MlWindow(QDialog):
    """
    Окно машинного обучения.
    """

    def __init__(self, current_user: AuthenticatedUser):
        """
        Создает окно ML-анализа.

        Параметры:
            current_user: авторизованный пользователь.
        """
        super().__init__()

        self.current_user = current_user

        self.setWindowTitle("KPI Monitor ML — ML-анализ")
        self.resize(1050, 720)

        self._create_interface()
        self._load_last_metrics()

    def _create_interface(self) -> None:
        """
        Создает интерфейс окна.
        """
        main_layout = QVBoxLayout()

        title_label = QLabel("ML-анализ KPI")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        description_label = QLabel(
            "Модуль машинного обучения прогнозирует риск снижения KPI сотрудника "
            "на основе исторических KPI-показателей."
        )
        description_label.setWordWrap(True)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setText(
            "Алгоритм: RandomForestClassifier.\n"
            "Задача: классификация риска KPI.\n"
            "Классы: низкий риск, средний риск, высокий риск.\n"
            "Файл модели: models/model.pkl."
        )

        metrics_frame = self._create_metrics_frame()

        train_button = QPushButton("Обучить модель")
        train_button.clicked.connect(self._train_model)
        train_button.setEnabled(can_train_ml_model(self.current_user))

        predict_button = QPushButton("Выполнить прогноз")
        predict_button.clicked.connect(self._run_prediction)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        self.predictions_table = QTableWidget()
        self.predictions_table.setColumnCount(5)
        self.predictions_table.setHorizontalHeaderLabels(
            [
                "ID сотрудника",
                "Сотрудник",
                "Отдел",
                "Прогноз риска",
                "Уверенность модели",
            ]
        )
        self.predictions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.predictions_table.setSelectionBehavior(QTableWidget.SelectRows)

        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(self.info_text)
        main_layout.addWidget(metrics_frame)
        main_layout.addWidget(train_button)
        main_layout.addWidget(predict_button)
        main_layout.addWidget(self.predictions_table)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _create_metrics_frame(self) -> QFrame:
        """
        Создает блок отображения метрик модели.
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QGridLayout()

        self.accuracy_label = self._create_metric_label("Accuracy", "-")
        self.precision_label = self._create_metric_label("Precision", "-")
        self.recall_label = self._create_metric_label("Recall", "-")
        self.f1_label = self._create_metric_label("F1-score", "-")

        layout.addWidget(self.accuracy_label, 0, 0)
        layout.addWidget(self.precision_label, 0, 1)
        layout.addWidget(self.recall_label, 0, 2)
        layout.addWidget(self.f1_label, 0, 3)

        frame.setLayout(layout)

        return frame

    def _create_metric_label(self, title: str, value: str) -> QLabel:
        """
        Создает подпись для метрики.
        """
        label = QLabel(f"{title}\n{value}")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        label.metric_title = title

        return label

    def _load_last_metrics(self) -> None:
        """
        Загружает метрики последней обученной модели.
        """
        session = SessionLocal()

        try:
            service = MlService(session)
            metrics = service.get_last_model_metrics()

        finally:
            session.close()

        if not metrics:
            return

        self._update_metrics_labels(metrics)

    def _train_model(self) -> None:
        """
        Запускает обучение ML-модели.
        """
        session = SessionLocal()

        try:
            service = MlService(session)
            result = service.train_model()

            audit_service = AuditService(session)
            audit_service.log_action(
                user_id=self.current_user.id,
                action="Обучение ML-модели",
                entity_name="MlModelInfo",
                entity_id=result.model_id,
                details=(
                    f"Обучена модель RandomForestClassifier. "
                    f"Accuracy={result.accuracy:.4f}, F1={result.f1:.4f}."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка обучения модели",
                f"Не удалось обучить модель.\n\n{error}",
            )
            return

        finally:
            session.close()

        metrics = {
            "accuracy": result.accuracy,
            "precision": result.precision,
            "recall": result.recall,
            "f1": result.f1,
        }

        self._update_metrics_labels(metrics)

        QMessageBox.information(
            self,
            "Обучение завершено",
            "ML-модель успешно обучена и сохранена.\n\n"
            f"Строк обучающего набора: {result.rows_count}\n"
            f"Количество признаков: {result.features_count}\n"
            f"Файл модели: {result.model_path}\n"
            f"Accuracy: {result.accuracy:.4f}\n"
            f"F1-score: {result.f1:.4f}",
        )

    def _run_prediction(self) -> None:
        """
        Выполняет прогноз риска KPI.
        """
        session = SessionLocal()

        try:
            service = MlService(session)
            predictions = service.predict_for_employees()

            audit_service = AuditService(session)
            audit_service.log_action(
                user_id=self.current_user.id,
                action="Выполнение ML-прогноза",
                entity_name="MlPrediction",
                entity_id=None,
                details=f"Выполнен прогноз риска KPI для сотрудников: {len(predictions)} записей.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка прогноза",
                f"Не удалось выполнить прогноз.\n\n{error}",
            )
            return

        finally:
            session.close()

        self.predictions_table.setRowCount(len(predictions))

        for row_index, prediction in enumerate(predictions):
            self._set_table_item(row_index, 0, str(prediction.employee_id))
            self._set_table_item(row_index, 1, prediction.employee_name)
            self._set_table_item(row_index, 2, prediction.department_name)
            self._set_table_item(row_index, 3, prediction.prediction_label)
            self._set_table_item(
                row_index,
                4,
                f"{prediction.prediction_score:.4f}",
            )

        self.predictions_table.resizeColumnsToContents()

    def _update_metrics_labels(self, metrics) -> None:
        """
        Обновляет значения метрик на экране.
        """
        self.accuracy_label.setText(
            f"Accuracy\n{metrics.get('accuracy', 0):.4f}"
        )
        self.precision_label.setText(
            f"Precision\n{metrics.get('precision', 0):.4f}"
        )
        self.recall_label.setText(
            f"Recall\n{metrics.get('recall', 0):.4f}"
        )
        self.f1_label.setText(
            f"F1-score\n{metrics.get('f1', 0):.4f}"
        )

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        """
        Устанавливает значение ячейки таблицы.
        """
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.predictions_table.setItem(row, column, item)