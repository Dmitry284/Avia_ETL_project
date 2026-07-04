from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Добавляем путь к скриптам
sys.path.append('/opt/airflow/scripts')

default_args = {
    'owner': 'aviation_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

def extract_data(**kwargs):
    """Задача извлечения данных"""
    import subprocess
    result = subprocess.run(
        ['python', '/opt/airflow/scripts/01_extract.py'],
        cwd='/opt/airflow/scripts',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Extract failed: {result.stderr}")
    print(result.stdout)

def transform_data(**kwargs):
    """Задача трансформации данных"""
    import subprocess
    result = subprocess.run(
        ['python', '/opt/airflow/scripts/02_transform.py'],
        cwd='/opt/airflow/scripts',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Transform failed: {result.stderr}")
    print(result.stdout)

def load_data(**kwargs):
    """Задача загрузки данных"""
    import subprocess
    result = subprocess.run(
        ['python', '/opt/airflow/scripts/03_load.py'],
        cwd='/opt/airflow/scripts',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Load failed: {result.stderr}")
    print(result.stdout)

def run_tests(**kwargs):
    """Задача запуска тестов"""
    import subprocess
    result = subprocess.run(
        ['pytest', '/opt/airflow/tests/', '-v'],
        cwd='/opt/airflow',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Tests failed: {result.stderr}")
    print(result.stdout)

dag = DAG(
    'aviation_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for aviation data consolidation',
    schedule_interval='@daily',
    catchup=False,
    tags=['aviation', 'etl', 'dwh'],
)

# Задачи
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

test_task = PythonOperator(
    task_id='run_tests',
    python_callable=run_tests,
    dag=dag,
)

# Зависимости
extract_task >> transform_task >> load_task >> test_task
