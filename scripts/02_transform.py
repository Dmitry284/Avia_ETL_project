import pandas as pd
import numpy as np
import logging
import os

# Настройка логирования
os.makedirs('../output/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../output/logs/transform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Словарь для нормализации аэропортов (IATA-коды)
AIRPORT_MAPPING = {
    'sheremetyevo': 'SVO',
    'pulkovo': 'LED',
    'domodedovo': 'DME',
    'koltsovo': 'SVX',
    'kazan': 'KZN',
    'tolmachevo': 'OVB',
    'SVO': 'SVO',
    'LED': 'LED',
    'DME': 'DME',
    'SVX': 'SVX',
    'KZN': 'KZN',
    'OVB': 'OVB'
}

def normalize_airport(airport_name):
    """Нормализует название аэропорта"""
    if pd.isna(airport_name):
        return None
    airport_str = str(airport_name).strip()
    airport_lower = airport_str.lower()
    
    # Сначала пытаемся найти по полному названию (в нижнем регистре)
    if airport_lower in AIRPORT_MAPPING:
        return AIRPORT_MAPPING[airport_lower]
    
    # Если не нашли, проверяем в верхнем регистре (для кодов типа 'SVO', 'LED')
    airport_upper = airport_str.upper()
    if airport_upper in AIRPORT_MAPPING:
        return AIRPORT_MAPPING[airport_upper]
    
    # Если ничего не нашли, возвращаем как есть в верхнем регистре
    return airport_upper
def normalize_flight_number(flight_num):
    """Нормализует номер рейса (убирает пробелы, к верхнему регистру)"""
    if pd.isna(flight_num):
        return None
    return str(flight_num).upper().replace(' ', '')

def transform_bookings(df):
    """Трансформирует данные бронирований"""
    logger.info("Трансформация бронирований...")
    
    initial_count = len(df)
    df = df.drop_duplicates()
    logger.info(f"Удалено {initial_count - len(df)} дубликатов")
    
    # Нормализация аэропортов (если столбцы существуют)
    if 'departure_airport' in df.columns:
        df['departure_airport'] = df['departure_airport'].apply(normalize_airport)
    if 'arrival_airport' in df.columns:
        df['arrival_airport'] = df['arrival_airport'].apply(normalize_airport)
    
    # Нормализация номеров рейсов
    if 'flight_number' in df.columns:
        df['flight_number'] = df['flight_number'].apply(normalize_flight_number)
    
    # Статус -> нижний регистр
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str).str.lower()
    
    # Валюта -> верхний регистр
    if 'currency' in df.columns:
        df['currency'] = df['currency'].astype(str).str.upper()
    
    # Заполнение пропусков в ticket_price и приведение к float
    if 'ticket_price' in df.columns:
        df['ticket_price'] = pd.to_numeric(df['ticket_price'], errors='coerce')
        mean_price = df['ticket_price'].mean()
        df['ticket_price'] = df['ticket_price'].fillna(mean_price)
        df['ticket_price'] = df['ticket_price'].astype(float)
    
    # Приведение departure_time к datetime
    if 'departure_time' in df.columns:
        df['departure_time'] = pd.to_datetime(df['departure_time'], errors='coerce')
    
    logger.info(f"Трансформация завершена. Итого {len(df)} записей")
    return df

def transform_flights_report(df):
    """Трансформирует данные из CSV отчетов"""
    logger.info("Трансформация CSV отчетов...")
    
    # Нормализация аэропортов (проверяем возможные имена колонок)
    for col in ['departure', 'departure_airport']:
        if col in df.columns:
            df[col] = df[col].apply(normalize_airport)
    for col in ['arrival', 'arrival_airport']:
        if col in df.columns:
            df[col] = df[col].apply(normalize_airport)
    
    # Нормализация номеров рейсов
    if 'flight_number' in df.columns:
        df['flight_number'] = df['flight_number'].apply(normalize_flight_number)
    
    # Статусы -> нижний регистр
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str).str.lower()
    
    # Приводим числовые колонки к float, если они есть
    for col in ['duration_min', 'distance_km', 'price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Если есть колонка со временем -> datetime
    for col in ['departure_time', 'departure_datetime', 'timestamp']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    logger.info(f"Трансформация завершена. Итого {len(df)} записей")
    return df

def transform_logs(df):
    """Трансформирует логи"""
    logger.info("Трансформация логов...")
    
    if 'flight_number' in df.columns:
        df['flight_number'] = df['flight_number'].apply(normalize_flight_number)
    
    # Конвертация timestamp в datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    logger.info(f"Трансформация завершена. Итого {len(df)} записей")
    return df

def transform_weather(df):
    """Трансформирует данные о погоде"""
    logger.info("Трансформация погоды...")
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    if 'airport_code' in df.columns:
        df['airport_code'] = df['airport_code'].apply(normalize_airport)
    elif 'airport' in df.columns:
        df['airport_code'] = df['airport'].apply(normalize_airport)
    
    # Приводим числовые колонки к float
    for col in ['temperature', 'wind_speed', 'humidity', 'pressure']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Трансформация завершена. Итого {len(df)} записей")
    return df

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("НАЧАЛО ЭТАПА TRANSFORM")
    logger.info("=" * 60)
    
    try:
        # Создаём папку для cleaned, если её нет
        os.makedirs('../output/cleaned', exist_ok=True)
        
        # Загружаем raw данные
        bookings_df = pd.read_parquet('../output/raw/bookings_raw.parquet')
        csv_df = pd.read_parquet('../output/raw/flights_report_raw.parquet')
        logs_df = pd.read_parquet('../output/raw/logs_raw.parquet')
        weather_df = pd.read_parquet('../output/raw/weather_raw.parquet')
        
        # Трансформируем
        bookings_clean = transform_bookings(bookings_df)
        csv_clean = transform_flights_report(csv_df)
        logs_clean = transform_logs(logs_df)
        weather_clean = transform_weather(weather_df)
        
        # Сохраняем cleaned данные
        bookings_clean.to_parquet('../output/cleaned/bookings_clean.parquet', index=False)
        csv_clean.to_parquet('../output/cleaned/flights_report_clean.parquet', index=False)
        logs_clean.to_parquet('../output/cleaned/logs_clean.parquet', index=False)
        weather_clean.to_parquet('../output/cleaned/weather_clean.parquet', index=False)
        
        logger.info("=" * 60)
        logger.info("ЭТАП TRANSFORM ЗАВЕРШЕН УСПЕШНО")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}. Убедитесь, что этап EXTRACT выполнен успешно.")
        raise
    except Exception as e:
        logger.error(f"Ошибка на этапе Transform: {str(e)}", exc_info=True)
        raise
