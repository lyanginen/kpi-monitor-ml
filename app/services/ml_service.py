"""
Сервис машинного обучения.

Модуль отвечает за:
- подготовку обучающего набора данных на основе KPI-записей;
- обучение модели классификации риска снижения KPI;
- сохранение обученной модели в файл;
- загрузку модели из файла;
- применение модели для прогноза риска по сотрудникам;
- сохранение метрик и прогнозов в базе данных.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.database.connection import BASE_DIR
from app.database.models import (
    Employee,
    KpiRecord,
    MlModelInfo,
    MlPrediction,
    ModelMetric,
)


MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

DEFAULT_MODEL_PATH = MODEL_DIR / "model.pkl"


@dataclass
class MlTrainingResult:
    """
    Результат обучения ML-модели.
    """

    model_id: int
    model_path: str
    rows_count: int
    features_count: int
    accuracy: float
    precision: float
    recall: float
    f1: float


@dataclass
class EmployeePredictionResult:
    """
    Результат прогноза по сотруднику.
    """

    employee_id: int
    employee_name: str
    department_name: str
    prediction_label: str
    prediction_score: float


class MlService:
    """
    Сервис машинного обучения для анализа KPI.
    """

    def __init__(self, session):
        """
        Создает ML-сервис.

        Параметры:
            session: активная сессия SQLAlchemy.
        """
        self.session = session

    def build_training_dataset(self) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """
        Формирует обучающий датасет на основе KPI-записей из базы данных.

        Каждая строка датасета соответствует сотруднику за конкретный период.
        Признаками являются оценки по отдельным KPI-показателям и средняя оценка.

        Целевая переменная:
        - высокий риск;
        - средний риск;
        - низкий риск.
        """
        records = (
            self.session.query(KpiRecord)
            .join(Employee)
            .order_by(KpiRecord.employee_id, KpiRecord.period_start)
            .all()
        )

        if not records:
            raise ValueError("В базе данных отсутствуют KPI-записи для обучения модели.")

        rows = []

        for record in records:
            rows.append(
                {
                    "employee_id": record.employee_id,
                    "period_start": record.period_start,
                    "indicator_name": record.indicator.name,
                    "score": record.score,
                }
            )

        dataframe = pd.DataFrame(rows)

        pivot = dataframe.pivot_table(
            index=["employee_id", "period_start"],
            columns="indicator_name",
            values="score",
            aggfunc="mean",
        )

        pivot = pivot.fillna(0.0)
        pivot["average_score"] = pivot.mean(axis=1)

        pivot["risk_label"] = pivot["average_score"].apply(self._convert_score_to_risk)

        feature_columns = [
            column
            for column in pivot.columns
            if column != "risk_label"
        ]

        features = pivot[feature_columns]
        target = pivot["risk_label"]

        if len(features) < 10:
            raise ValueError(
                "Недостаточно данных для обучения модели. "
                "Нужно минимум 10 строк обучающего набора."
            )

        return features, target, feature_columns

    def train_model(self) -> MlTrainingResult:
        """
        Обучает модель классификации риска KPI и сохраняет ее в файл.
        """
        features, target, feature_columns = self.build_training_dataset()

        stratify_target = None
        class_counts = target.value_counts()

        if len(class_counts) > 1 and class_counts.min() >= 2:
            stratify_target = target

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.3,
            random_state=42,
            stratify=stratify_target,
        )

        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=5,
        )

        model.fit(x_train, y_train)

        predictions = model.predict(x_test)

        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        )
        recall = recall_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        )
        f1 = f1_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        )

        model_payload = {
            "model": model,
            "feature_columns": feature_columns,
            "trained_at": datetime.now().isoformat(),
        }

        joblib.dump(model_payload, DEFAULT_MODEL_PATH)

        model_info = MlModelInfo(
            name="RandomForest KPI Risk Classifier",
            algorithm="RandomForestClassifier",
            model_path=str(DEFAULT_MODEL_PATH),
            description=(
                "Модель классификации риска снижения KPI сотрудника "
                "на основе исторических KPI-показателей."
            ),
        )

        self.session.add(model_info)
        self.session.flush()

        metric_values = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        for metric_name, metric_value in metric_values.items():
            metric = ModelMetric(
                model_id=model_info.id,
                metric_name=metric_name,
                metric_value=round(float(metric_value), 4),
            )
            self.session.add(metric)

        self.session.commit()

        return MlTrainingResult(
            model_id=model_info.id,
            model_path=str(DEFAULT_MODEL_PATH),
            rows_count=len(features),
            features_count=len(feature_columns),
            accuracy=round(float(accuracy), 4),
            precision=round(float(precision), 4),
            recall=round(float(recall), 4),
            f1=round(float(f1), 4),
        )

    def predict_for_employees(self) -> List[EmployeePredictionResult]:
        """
        Выполняет прогноз риска KPI для сотрудников.

        Для прогноза используются последние доступные KPI-записи каждого сотрудника.
        """
        if not DEFAULT_MODEL_PATH.exists():
            raise FileNotFoundError(
                "Файл модели не найден. Сначала необходимо обучить модель."
            )

        model_payload = joblib.load(DEFAULT_MODEL_PATH)
        model = model_payload["model"]
        feature_columns = model_payload["feature_columns"]

        prediction_dataframe = self._build_latest_employee_features(feature_columns)

        if prediction_dataframe.empty:
            return []

        employee_ids = prediction_dataframe.index.tolist()
        predicted_labels = model.predict(prediction_dataframe[feature_columns])

        prediction_scores = self._calculate_prediction_scores(
            model,
            prediction_dataframe[feature_columns],
            predicted_labels,
        )

        latest_model = (
            self.session.query(MlModelInfo)
            .order_by(MlModelInfo.created_at.desc())
            .first()
        )

        if latest_model is None:
            raise ValueError("В базе данных не найдена информация об обученной модели.")

        results = []

        for index, employee_id in enumerate(employee_ids):
            employee = (
                self.session.query(Employee)
                .filter(Employee.id == employee_id)
                .first()
            )

            if employee is None:
                continue

            prediction_label = str(predicted_labels[index])
            prediction_score = float(prediction_scores[index])

            prediction = MlPrediction(
                employee_id=employee.id,
                model_id=latest_model.id,
                prediction_label=prediction_label,
                prediction_score=round(prediction_score, 4),
            )

            self.session.add(prediction)

            department_name = employee.department.name if employee.department else ""

            results.append(
                EmployeePredictionResult(
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    department_name=department_name,
                    prediction_label=prediction_label,
                    prediction_score=round(prediction_score, 4),
                )
            )

        self.session.commit()

        return results

    def get_last_model_metrics(self) -> Dict[str, float]:
        """
        Возвращает метрики последней обученной модели.
        """
        latest_model = (
            self.session.query(MlModelInfo)
            .order_by(MlModelInfo.created_at.desc())
            .first()
        )

        if latest_model is None:
            return {}

        metrics = (
            self.session.query(ModelMetric)
            .filter(ModelMetric.model_id == latest_model.id)
            .all()
        )

        return {
            metric.metric_name: metric.metric_value
            for metric in metrics
        }

    def _build_latest_employee_features(
        self,
        feature_columns: List[str],
    ) -> pd.DataFrame:
        """
        Формирует признаки для прогноза по последнему периоду каждого сотрудника.
        """
        records = (
            self.session.query(KpiRecord)
            .order_by(KpiRecord.employee_id, KpiRecord.period_start)
            .all()
        )

        rows = []

        for record in records:
            rows.append(
                {
                    "employee_id": record.employee_id,
                    "period_start": record.period_start,
                    "indicator_name": record.indicator.name,
                    "score": record.score,
                }
            )

        dataframe = pd.DataFrame(rows)

        if dataframe.empty:
            return pd.DataFrame(columns=feature_columns)

        latest_periods = (
            dataframe.groupby("employee_id")["period_start"]
            .max()
            .reset_index()
        )

        latest_dataframe = dataframe.merge(
            latest_periods,
            on=["employee_id", "period_start"],
            how="inner",
        )

        pivot = latest_dataframe.pivot_table(
            index="employee_id",
            columns="indicator_name",
            values="score",
            aggfunc="mean",
        )

        pivot = pivot.fillna(0.0)
        pivot["average_score"] = pivot.mean(axis=1)

        for column in feature_columns:
            if column not in pivot.columns:
                pivot[column] = 0.0

        return pivot[feature_columns]

    def _calculate_prediction_scores(
        self,
        model,
        features: pd.DataFrame,
        predicted_labels,
    ) -> List[float]:
        """
        Рассчитывает уверенность модели в выбранном классе.

        Если модель поддерживает predict_proba, берется вероятность выбранного класса.
        """
        if not hasattr(model, "predict_proba"):
            return [0.0 for _ in predicted_labels]

        probabilities = model.predict_proba(features)
        classes = list(model.classes_)

        scores = []

        for row_index, predicted_label in enumerate(predicted_labels):
            class_index = classes.index(predicted_label)
            scores.append(float(probabilities[row_index][class_index]))

        return scores

    def _convert_score_to_risk(self, average_score: float) -> str:
        """
        Преобразует среднюю оценку KPI в класс риска.

        Логика:
        - ниже 80: высокий риск;
        - от 80 до 90: средний риск;
        - 90 и выше: низкий риск.
        """
        if average_score < 80:
            return "Высокий риск"

        if average_score < 90:
            return "Средний риск"

        return "Низкий риск"