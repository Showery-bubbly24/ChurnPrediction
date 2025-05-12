# -
# --
# ---
# ----
# -----
# Быстрый гайд по Автоматическому дообучению
# 1) Нужно установить Airflow и развернуть через докер
"""bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.0.0/docker-compose.yaml'
"""

# Создадим нужные директории и .env
"""bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
"""

# Создайте Dockerfile и наполните его данным кодом
"""dockerfile
FROM apache/airflow:3.0.0

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    sqlalchemy \
    pickle-mixin
"""

# Дальше: Инициализируем airflow-init
"""bash
docker compose up airflow-init
"""

# Поднимаем наше веб приложение ('localhost:8080' / '0.0.0.0:8080')
"""bash
docker compose up -d 
"""

# Создаем файл в котором будет наш Airflow: DAG и пишем туда наш алгоритм автоматического дообучения
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
from sqlalchemy import create_engine
from sklearn.linear_model import SGDClassifier
import pickle
import os

# Конфигурация
THRESHOLD = 500
TABLE_NAME = "your_table"  # Замените на имя вашей таблицы


def check_db_and_retrain():
    # Подключение к БД
    engine = create_engine(DB_URL)

    # Проверка количества строк
    count = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME}", engine).iloc[0, 0]

    if count > THRESHOLD:
        print(f"Найдено {count} строк. Начинаю дообучение модели...")

        # Загрузка новых данных
        new_data = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
        X = new_data.drop('target_column', axis=1)
        y = new_data['target_column']

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Загрузка или создание модели
        with open('clas_model.pkl', 'rb') as file:
            cls_model = pickle.load(file)

        # Дообучение
        new_model = cls_model.fit(df.drop('adv_Churn', axis=1), df['adv_Churn'])
        ennsemble = VotingClassifier([('old', cls_model), ('new', new_model)], voting='soft')

        # Сохранение модели
        with open('clas_model.pkl', 'wb') as file:
            pickle.dump(ennsemble, file)

        print("Модель дообучена и сохранена!")
    else:
        print("Model need more data")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        'weekly_model_retraining',
        default_args=default_args,
        description='Еженедельная проверка БД и дообучение модели',
        schedule_interval='0 0 * * 1',  # Каждый понедельник в 00:00
        start_date=datetime(2025, 4, 28),
        catchup=False,
        tags=['ml'],
) as dag:
    retrain_task = PythonOperator(
        task_id='check_and_retrain_model',
        python_callable=check_db_and_retrain,
    )

    retrain_task
