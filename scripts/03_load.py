import pandas as pd
import logging
import os
from sqlalchemy import text
from db_utils import get_dwh_engine
from datetime import datetime

# Настройка логирования
os.makedirs('../output/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../output/logs/load.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_dimensions():
    logger.info("Загрузка таблиц измерений...")
    engine = get_dwh_engine()
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    
    # --- dim_airports ---
    airports = bookings_df['departure_airport'].dropna().unique()
    airports_df = pd.DataFrame({'airport_code': airports})
    airports_df['airport_name'] = airports_df['airport_code']
    airports_df['city'] = airports_df['airport_code']
    airports_df['country'] = 'Россия'
    airports_df = airports_df.drop_duplicates(subset=['airport_code'])
    
    # Используем replace чтобы перезаписать таблицу при каждом запуске
    airports_df.to_sql('dim_airports', engine, schema='dwh', if_exists='replace', index=False)
    logger.info(f"Загружено {len(airports_df)} аэропортов")
    
    # --- dim_aircraft ---
    aircraft_list = bookings_df['aircraft_type'].dropna().unique()
    aircraft_df = pd.DataFrame({'aircraft_code': aircraft_list})
    aircraft_df['aircraft_type'] = aircraft_df['aircraft_code']
    aircraft_df['capacity'] = 180
    aircraft_df['manufacturer'] = 'Unknown'
    aircraft_df = aircraft_df.drop_duplicates(subset=['aircraft_code'])
    
    aircraft_df.to_sql('dim_aircraft', engine, schema='dwh', if_exists='replace', index=False)
    logger.info(f"Загружено {len(aircraft_df)} самолетов")
    
    # --- dim_dates ---
    if 'departure_time' in bookings_df.columns:
        dates_series = pd.to_datetime(bookings_df['departure_time']).dt.date.dropna().unique()
        dates = [d for d in dates_series if pd.notna(d)]
        if dates:
            dates_df = pd.DataFrame({
                'date_key': [int(d.strftime('%Y%m%d')) for d in dates],
                'full_date': dates,
                'year': [d.year for d in dates],
                'month': [d.month for d in dates],
                'day': [d.day for d in dates],
                'day_of_week': [d.weekday() for d in dates],
                'day_name': [d.strftime('%A') for d in dates],
                'month_name': [d.strftime('%B') for d in dates],
                'quarter': [(d.month - 1) // 3 + 1 for d in dates],
                'is_weekend': [d.weekday() >= 5 for d in dates]
            })
            dates_df = dates_df.drop_duplicates(subset=['date_key'])
            
            dates_df.to_sql('dim_dates', engine, schema='dwh', if_exists='replace', index=False)
            logger.info(f"Загружено {len(dates_df)} дат")
        else:
            logger.warning("Нет дат для загрузки в dim_dates")
    else:
        logger.warning("В данных нет столбца departure_time")
def load_fact_flights():
    logger.info("Загрузка фактической таблицы рейсов...")
    engine = get_dwh_engine()
    
    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')
    
    # Конвертация типов данных
    for col in ['scheduled_departure', 'scheduled_arrival', 'actual_departure', 'actual_arrival']:
        if col in flights_df.columns:
            flights_df[col] = pd.to_datetime(flights_df[col], errors='coerce')
    
    # Используем replace чтобы перезаписать таблицу при каждом запуске
    flights_df.to_sql('fact_flights', engine, schema='dwh', if_exists='replace', index=False)
    logger.info(f"Загружено {len(flights_df)} рейсов")

def load_fact_bookings():
    logger.info("Загрузка фактической таблицы бронирований...")
    engine = get_dwh_engine()
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    
    # Удаляем колонку id - она не нужна в DWH
    if 'id' in bookings_df.columns:
        bookings_df = bookings_df.drop('id', axis=1)
        logger.info("Удалена колонка 'id' из данных бронирований")
    
    # Конвертация типов данных
    if 'departure_time' in bookings_df.columns:
        bookings_df['departure_time'] = pd.to_datetime(bookings_df['departure_time'], errors='coerce')
    
    if 'arrival_time' in bookings_df.columns:
        bookings_df['arrival_time'] = pd.to_datetime(bookings_df['arrival_time'], errors='coerce')
    
    if 'booking_date' in bookings_df.columns:
        bookings_df['booking_date'] = pd.to_datetime(bookings_df['booking_date'], errors='coerce')
    
    for col in ['ticket_price']:
        if col in bookings_df.columns:
            bookings_df[col] = pd.to_numeric(bookings_df[col], errors='coerce')
    
    # Используем replace чтобы перезаписать таблицу при каждом запуске
    bookings_df.to_sql('fact_bookings', engine, schema='dwh', if_exists='replace', index=False)
    logger.info(f"Загружено {len(bookings_df)} бронирований")
if __name__ == '__main__':
    logger.info("НАЧАЛО ЭТАПА LOAD")
    
    try:
        os.makedirs('../output/cleaned', exist_ok=True)
        load_dimensions()
        load_fact_flights()
        load_fact_bookings()
        logger.info("ЭТАП LOAD ЗАВЕРШЕН УСПЕШНО")
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}. Убедитесь, что этап TRANSFORM выполнен успешно.")
        raise
    except Exception as e:
        logger.error(f"Ошибка на этапе Load: {str(e)}", exc_info=True)
        raise
