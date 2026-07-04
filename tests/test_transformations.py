import pytest
import pandas as pd
import sys
import os
import importlib.util

# Загружаем модуль трансформаций динамически
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', '02_transform.py')
spec = importlib.util.spec_from_file_location("transform_module", script_path)
transform_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transform_module)

# Получаем функции из модуля
normalize_airport = transform_module.normalize_airport
normalize_flight_number = transform_module.normalize_flight_number

class TestTransformations:
    """Тесты функций трансформации"""
    
    def test_normalize_airport_svo(self):
        """Проверка нормализации Шереметьево"""
        assert normalize_airport('sheremetyevo') == 'SVO'
        assert normalize_airport('SVO') == 'SVO'
        assert normalize_airport('svo') == 'SVO'
    
    def test_normalize_airport_led(self):
        """Проверка нормализации Пулково"""
        assert normalize_airport('pulkovo') == 'LED'
        assert normalize_airport('LED') == 'LED'
        assert normalize_airport('led') == 'LED'
    
    def test_normalize_airport_dme(self):
        """Проверка нормализации Домодедово"""
        assert normalize_airport('domodedovo') == 'DME'
        assert normalize_airport('DME') == 'DME'
    
    def test_normalize_airport_null(self):
        """Проверка обработки NULL"""
        result = normalize_airport(None)
        assert result is None or pd.isna(result)
    
    def test_normalize_flight_number_basic(self):
        """Проверка нормализации номеров рейсов"""
        assert normalize_flight_number('SU101') == 'SU101'
        assert normalize_flight_number('su101') == 'SU101'
        assert normalize_flight_number('SU 101') == 'SU101'
        assert normalize_flight_number('su 102') == 'SU102'
    
    def test_normalize_flight_number_with_spaces(self):
        """Проверка удаления пробелов"""
        assert normalize_flight_number('SU  101') == 'SU101'
        assert normalize_flight_number(' SU 101 ') == 'SU101'
    
    def test_normalize_flight_number_null(self):
        """Проверка обработки NULL"""
        result = normalize_flight_number(None)
        assert result is None or pd.isna(result)
    
    def test_normalize_flight_number_mixed_case(self):
        """Проверка смешанного регистра"""
        assert normalize_flight_number('Su101') == 'SU101'
        assert normalize_flight_number('sU102') == 'SU102'
