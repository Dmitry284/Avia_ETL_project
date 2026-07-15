import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_booking_db_engine():
    """Создает подключение к исходной БД (booking_db)"""
    host = os.getenv('BOOKING_DB_HOST', 'localhost')
    port = os.getenv('BOOKING_DB_PORT', '5434')
    user = os.getenv('BOOKING_DB_USER', 'aviation_user')
    password = os.getenv('BOOKING_DB_PASSWORD', 'aviation_pass')
    dbname = os.getenv('BOOKING_DB_NAME', 'booking_db')
    
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    return create_engine(connection_string)

def get_dwh_engine():
    host = os.getenv('DWH_DB_HOST', 'localhost')
    port = os.getenv('DWH_DB_PORT', '5434')
    user = os.getenv('DWH_DB_USER', 'aviation_user')
    password = os.getenv('DWH_DB_PASSWORD', 'aviation_pass')
    dbname = os.getenv('DWH_DB_NAME', 'aviation_dwh')
    
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    return create_engine(connection_string)
