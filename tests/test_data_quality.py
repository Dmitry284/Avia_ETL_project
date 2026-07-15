import pytest
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Создаем подключение к DWH
def get_dwh_engine():
    host = os.getenv('DWH_DB_HOST', 'localhost')
    port = os.getenv('DWH_DB_PORT', '5434')
    user = os.getenv('DWH_DB_USER', 'aviation_user')
    password = os.getenv('DWH_DB_PASSWORD', 'aviation_pass')
    dbname = os.getenv('DWH_DB_NAME', 'aviation_dwh')
    
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    return create_engine(connection_string)

class TestDataQuality:
    """Тесты качества данных в DWH (для схемы 3НФ)"""
    
    @pytest.fixture
    def engine(self):
        return get_dwh_engine()
    
    def test_dim_airports_not_empty(self, engine):
        """Проверка что таблица аэропортов не пустая"""
        query = "SELECT COUNT(*) FROM dwh.dim_airports"
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] > 0, "Таблица dim_airports пустая"
    
    def test_dim_aircraft_not_empty(self, engine):
        """Проверка что таблица самолетов не пустая"""
        query = "SELECT COUNT(*) FROM dwh.dim_aircraft"
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] > 0, "Таблица dim_aircraft пустая"
    
    def test_dim_dates_not_empty(self, engine):
        """Проверка что таблица дат не пустая"""
        query = "SELECT COUNT(*) FROM dwh.dim_dates"
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] > 0, "Таблица dim_dates пустая"
    
    def test_fact_flights_not_empty(self, engine):
        """Проверка что таблица рейсов не пустая"""
        query = "SELECT COUNT(*) FROM dwh.fact_flights"
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] > 0, "Таблица fact_flights пустая"
    
    def test_fact_bookings_not_empty(self, engine):
        """Проверка что таблица бронирований не пустая"""
        query = "SELECT COUNT(*) FROM dwh.fact_bookings"
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] > 0, "Таблица fact_bookings пустая"
    
    def test_no_duplicate_airports(self, engine):
        """Проверка отсутствия дубликатов аэропортов"""
        query = """
        SELECT airport_code, COUNT(*) as cnt 
        FROM dwh.dim_airports 
        GROUP BY airport_code 
        HAVING COUNT(*) > 1
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены дубликаты аэропортов: {result}"
    
    def test_no_duplicate_aircraft(self, engine):
        """Проверка отсутствия дубликатов самолетов"""
        query = """
        SELECT aircraft_code, COUNT(*) as cnt 
        FROM dwh.dim_aircraft 
        GROUP BY aircraft_code 
        HAVING COUNT(*) > 1
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены дубликаты самолетов: {result}"
    
    def test_no_duplicate_dates(self, engine):
        """Проверка отсутствия дубликатов дат"""
        query = """
        SELECT date_id, COUNT(*) as cnt 
        FROM dwh.dim_dates 
        GROUP BY date_id 
        HAVING COUNT(*) > 1
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены дубликаты дат: {result}"
    
    def test_flight_prices_positive(self, engine):
        """Проверка что цены билетов положительные"""
        query = """
        SELECT COUNT(*) FROM dwh.fact_bookings 
        WHERE ticket_price < 0 OR ticket_price IS NULL
        """
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] == 0, "Найдены отрицательные или NULL цены билетов"
    
    def test_flight_dates_valid(self, engine):
        """Проверка что даты рейсов валидные (через JOIN с dim_dates)"""
        query = """
        SELECT COUNT(*) FROM dwh.fact_flights ff
        JOIN dwh.dim_dates dd ON ff.flight_date_id = dd.date_id
        WHERE dd.full_date < '2020-01-01' OR dd.full_date > '2030-12-31'
        """
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] == 0, "Найдены невалидные даты рейсов"
    
    def test_airport_codes_format(self, engine):
        """Проверка формата кодов аэропортов (3 буквы)"""
        query = """
        SELECT airport_code FROM dwh.dim_airports 
        WHERE LENGTH(airport_code) != 3 OR airport_code !~ '^[A-Z]{3}$'
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены невалидные коды аэропортов: {result}"
    
    def test_flight_numbers_format(self, engine):
        """Проверка формата номеров рейсов (через JOIN с dim_flights)"""
        query = """
        SELECT df.flight_number FROM dwh.fact_flights ff
        JOIN dwh.dim_flights df ON ff.flight_id = df.flight_id
        WHERE df.flight_number IS NULL OR LENGTH(df.flight_number) < 2
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены невалидные номера рейсов: {result}"
    
    def test_booking_status_values(self, engine):
        """Проверка допустимых значений статусов бронирований (через JOIN с dim_statuses)"""
        valid_statuses = ['confirmed', 'cancelled', 'pending', 'completed']
        query = f"""
        SELECT DISTINCT ds.status_code FROM dwh.fact_bookings fb
        JOIN dwh.dim_statuses ds ON fb.status_id = ds.status_id
        WHERE ds.status_code NOT IN ({','.join([f"'{s}'" for s in valid_statuses])})
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены невалидные статусы: {result}"
    
    def test_flight_status_values(self, engine):
        valid_statuses = ['scheduled', 'landed', 'delayed', 'cancelled', 'diverted']
        query = f"""
        SELECT DISTINCT ds.status_code FROM dwh.fact_flights ff
        JOIN dwh.dim_statuses ds ON ff.status_id = ds.status_id
        WHERE ds.status_code NOT IN ({','.join([f"'{s}'" for s in valid_statuses])})
        """
        result = pd.read_sql(query, engine)
        assert len(result) == 0, f"Найдены невалидные статусы рейсов: {result}"
    
    def test_no_null_flight_numbers(self, engine):
        query = """
        SELECT COUNT(*) FROM dwh.fact_flights ff
        JOIN dwh.dim_flights df ON ff.flight_id = df.flight_id
        WHERE df.flight_number IS NULL
        """
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] == 0, "Найдены NULL номера рейсов"
    
    def test_no_null_booking_refs(self, engine):
        """Проверка отсутствия NULL в ссылках бронирований"""
        query = """
        SELECT COUNT(*) FROM dwh.fact_bookings 
        WHERE booking_ref IS NULL
        """
        result = pd.read_sql(query, engine)
        assert result.iloc[0, 0] == 0, "Найдены NULL ссылки бронирований"
