import pytest
import os
import subprocess
import sys

class TestETLPipeline:
    """Тесты ETL пайплайна"""
    
    def test_extract_script_exists(self):
        """Проверка существования скрипта extract"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', '01_extract.py')
        assert os.path.exists(script_path), f"Скрипт не найден: {script_path}"
    
    def test_transform_script_exists(self):
        """Проверка существования скрипта transform"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', '02_transform.py')
        assert os.path.exists(script_path), f"Скрипт не найден: {script_path}"
    
    def test_load_script_exists(self):
        """Проверка существования скрипта load"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', '03_load.py')
        assert os.path.exists(script_path), f"Скрипт не найден: {script_path}"
    
    def test_pipeline_script_exists(self):
        """Проверка существования главного скрипта"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_etl_pipeline.py')
        assert os.path.exists(script_path), f"Скрипт не найден: {script_path}"
    
    def test_raw_output_directory_exists(self):
        """Проверка существования директории для raw данных"""
        dir_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw')
        assert os.path.exists(dir_path), f"Директория не найдена: {dir_path}"
    
    def test_cleaned_output_directory_exists(self):
        """Проверка существования директории для cleaned данных"""
        dir_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'cleaned')
        assert os.path.exists(dir_path), f"Директория не найдена: {dir_path}"
    
    def test_logs_directory_exists(self):
        """Проверка существования директории для логов"""
        dir_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'logs')
        assert os.path.exists(dir_path), f"Директория не найдена: {dir_path}"
    
    def test_raw_bookings_file_exists(self):
        """Проверка существования файла raw бронирований"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw', 'bookings_raw.parquet')
        assert os.path.exists(file_path), f"Файл не найден: {file_path}"
    
    def test_cleaned_bookings_file_exists(self):
        """Проверка существования файла cleaned бронирований"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'cleaned', 'bookings_clean.parquet')
        assert os.path.exists(file_path), f"Файл не найден: {file_path}"
    
    def test_pipeline_log_exists(self):
        """Проверка существования лога пайплайна"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'logs', 'pipeline.log')
        assert os.path.exists(file_path), f"Файл не найден: {file_path}"
    
    def test_source_data_exists(self):
        """Проверка существования исходных данных"""
        sources = [
            'sources/booking_db/init.sql',
            'sources/csv_reports/flights_report.csv',
            'sources/logs/server_logs.json',
            'sources/api_mocks/weather_api.json'
        ]
        
        for source in sources:
            file_path = os.path.join(os.path.dirname(__file__), '..', source)
            assert os.path.exists(file_path), f"Исходный файл не найден: {file_path}"
