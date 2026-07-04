import pandas as pd
import json
import os
import logging
from db_utils import get_booking_db_engine
from sqlalchemy import text

# Настройка логирования
os.makedirs('../output/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../output/logs/extract.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_bookings():
    """Извлекает данные бронирований из PostgreSQL"""
    logger.info("Начало извлечения бронирований из booking_db...")
    
    engine = get_booking_db_engine()
    
    query = "SELECT * FROM raw_bookings"
    
    # Используем прямой подход через SQLAlchemy, чтобы обойти баг в pandas 3.0.3
    with engine.connect() as conn:
        result = conn.execute(text(query))
        columns = result.keys()
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=columns)
    
    # Сохраняем в raw формат
    output_path = '../output/raw/bookings_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(df)} записей бронирований")
    logger.info(f"Сохранено в {output_path}")
    
    return df

def extract_csv_reports():
    """Извлекает данные из CSV отчетов"""
    logger.info("Начало извлечения CSV отчетов...")
    
    csv_path = '../sources/csv_reports/flights_report.csv'
    df = pd.read_csv(csv_path)
    
    output_path = '../output/raw/flights_report_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(df)} записей из CSV")
    logger.info(f"Сохранено в {output_path}")
    
    return df

def extract_logs():
    """Извлекает данные из JSON логов"""
    logger.info("Начало извлечения логов...")
    
    log_path = '../sources/logs/server_logs.json'
    
    with open(log_path, 'r', encoding='utf-8') as f:
        logs_data = json.load(f)
    
    df = pd.DataFrame(logs_data)
    
    output_path = '../output/raw/logs_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(df)} записей из логов")
    logger.info(f"Сохранено в {output_path}")
    
    return df

def extract_weather_api():
    """Извлекает данные о погоде из API мока"""
    logger.info("Начало извлечения данных о погоде...")
    
    weather_path = '../sources/api_mocks/weather_api.json'
    
    with open(weather_path, 'r', encoding='utf-8') as f:
        weather_data = json.load(f)
    
    df = pd.DataFrame(weather_data)
    
    output_path = '../output/raw/weather_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(df)} записей о погоде")
    logger.info(f"Сохранено в {output_path}")
    
    return df

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("НАЧАЛО ЭТАПА EXTRACT")
    logger.info("=" * 60)
    
    try:
        bookings_df = extract_bookings()
        csv_df = extract_csv_reports()
        logs_df = extract_logs()
        weather_df = extract_weather_api()
        
        logger.info("=" * 60)
        logger.info("ЭТАП EXTRACT ЗАВЕРШЕН УСПЕШНО")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Ошибка на этапе Extract: {str(e)}", exc_info=True)
        raise
