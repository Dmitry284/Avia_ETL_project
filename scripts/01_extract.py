import pandas as pd
import json
import os
import logging
import yaml
from pathlib import Path

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

def load_config():
    config_path = Path('../config.yaml')
    if not config_path.exists():
        logger.error(f"Конфигурационный файл не найден: {config_path}")
        raise FileNotFoundError(f"Конфиг не найден: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_csv_structure(df, expected_columns, file_path):
    missing_cols = set(expected_columns) - set(df.columns)
    extra_cols = set(df.columns) - set(expected_columns)
    
    if missing_cols:
        logger.error(f"Файл {file_path}: отсутствуют колонки: {missing_cols}")
        return False
    if extra_cols:
        logger.warning(f"Файл {file_path}: лишние колонки (будут проигнорированы): {extra_cols}")
    return True

# Извлечение из PostgreSQL
def extract_postgres(config):
    """Извлекает данные из PostgreSQL"""
    if not config['sources']['postgres']['enabled']:
        logger.info("PostgreSQL источник отключён в конфигурации")
        return None
    
    logger.info("Извлечение из PostgreSQL...")
    
    try:
        from sqlalchemy import create_engine
        
        pg_config = config['sources']['postgres']
        connection_string = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        engine = create_engine(connection_string)
        
        query = f"SELECT * FROM {pg_config['table']}"
        df = pd.read_sql(query, engine)
        
        output_path = '../output/raw/bookings_raw.parquet'
        os.makedirs('../output/raw', exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Извлечено {len(df)} записей из PostgreSQL")
        logger.info(f"Сохранено в {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении из PostgreSQL: {str(e)}")
        if config['processing']['on_validation_error'] == 'fail':
            raise
        return None

# Извлечение из CSV файлов
def extract_csv_files(config):
    if not config['sources']['csv_flights']['enabled']:
        logger.info("CSV источник отключён в конфигурации")
        return None
    
    logger.info("Извлечение из CSV файлов...")
    
    csv_config = config['sources']['csv_flights']
    files = csv_config['files']
    expected_columns = [
        'flight_date', 'flight_number', 'departure', 'arrival',
        'scheduled_departure', 'scheduled_arrival',
        'actual_departure', 'actual_arrival', 'status', 'aircraft_id'
    ]
    
    all_dfs = []
    
    for file_path in files:
        file_path = str(file_path)
        
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            if config['processing']['on_validation_error'] == 'fail':
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            continue
        
        try:
            logger.info(f"Чтение файла: {file_path}")
            df = pd.read_csv(file_path)
            
            # Валидация структуры
            if not validate_csv_structure(df, expected_columns, file_path):
                logger.error(f"Файл {file_path} имеет неверную структуру, пропускаем")
                if config['processing']['on_validation_error'] == 'fail':
                    raise ValueError(f"Неверная структура файла: {file_path}")
                continue
            
            all_dfs.append(df)
            logger.info(f"Успешно прочитан файл {file_path}: {len(df)} записей")
            
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
            if config['processing']['on_validation_error'] == 'fail':
                raise
    
    if not all_dfs:
        logger.warning("Не удалось прочитать ни один CSV файл")
        return None
    
    # Объединяем все файлы
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    output_path = '../output/raw/flights_report_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    combined_df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(combined_df)} записей из {len(all_dfs)} CSV файлов")
    logger.info(f"Сохранено в {output_path}")
    
    return combined_df

def extract_json_logs(config):
    """Извлекает данные из JSON логов"""
    if not config['sources']['json_logs']['enabled']:
        logger.info("JSON логи отключены в конфигурации")
        return None
    
    logger.info("Извлечение из JSON логов...")
    
    file_path = config['sources']['json_logs']['file']
    
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        if config['processing']['on_validation_error'] == 'fail':
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
        
        df = pd.DataFrame(logs_data)
        
        output_path = '../output/raw/logs_raw.parquet'
        os.makedirs('../output/raw', exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Извлечено {len(df)} записей из логов")
        logger.info(f"Сохранено в {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении логов: {str(e)}")
        if config['processing']['on_validation_error'] == 'fail':
            raise
        return None
def extract_weather_api(config):
    if not config['sources']['api_weather']['enabled']:
        logger.info("API погоды отключено в конфигурации")
        return None
    
    logger.info("Извлечение данных о погоде...")
    
    file_path = config['sources']['api_weather']['file']
    
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        if config['processing']['on_validation_error'] == 'fail':
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            weather_data = json.load(f)
        
        df = pd.DataFrame(weather_data)
        
        output_path = '../output/raw/weather_raw.parquet'
        os.makedirs('../output/raw', exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Извлечено {len(df)} записей о погоде")
        logger.info(f"Сохранено в {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении погоды: {str(e)}")
        if config['processing']['on_validation_error'] == 'fail':
            raise
        return None
def extract_maintenance_csv(config):
    if not config['sources'].get('csv_maintenance', {}).get('enabled', False):
        logger.info("CSV обслуживание отключено в конфигурации")
        return None
    
    logger.info("Извлечение данных о обслуживании из CSV...")
    
    csv_config = config['sources']['csv_maintenance']
    files = csv_config['files']
    
    expected_columns = [
        'aircraft_code', 'maintenance_type', 'scheduled_date',
        'completed_date', 'status', 'cost', 'description'
    ]
    
    all_dfs = []
    
    for file_path in files:
        file_path = str(file_path)
        
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            continue
        
        try:
            logger.info(f"Чтение файла: {file_path}")
            df = pd.read_csv(file_path)
            
            if not validate_csv_structure(df, expected_columns, file_path):
                logger.error(f"Файл {file_path} имеет неверную структуру")
                continue
            
            all_dfs.append(df)
            logger.info(f"Успешно прочитан файл {file_path}: {len(df)} записей")
            
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
    
    if not all_dfs:
        logger.warning("Не удалось прочитать ни один CSV файл обслуживания")
        return None
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    output_path = '../output/raw/maintenance_raw.parquet'
    os.makedirs('../output/raw', exist_ok=True)
    combined_df.to_parquet(output_path, index=False)
    
    logger.info(f"Извлечено {len(combined_df)} записей об обслуживании")
    logger.info(f"Сохранено в {output_path}")
    
    return combined_df

if __name__ == '__main__':
    logger.info("НАЧАЛО ЭТАПА EXTRACT")
    
    try:
        config = load_config()
        logger.info("Конфигурация загружена успешно")
        
        bookings_df = extract_postgres(config)
        csv_df = extract_csv_files(config)
        logs_df = extract_json_logs(config)
        weather_df = extract_weather_api(config)
        maintenance_df = extract_maintenance_csv(config)

        logger.info("ЭТАП EXTRACT ЗАВЕРШЕН УСПЕШНО")

    except Exception as e:
        logger.error(f"Ошибка на этапе Extract: {str(e)}", exc_info=True)
        raise
