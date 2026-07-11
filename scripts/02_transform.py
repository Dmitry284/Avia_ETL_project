import pandas as pd
import numpy as np
import logging
import os
import json
from datetime import datetime

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

AIRPORT_MAPPING = {
    'sheremetyevo': 'SVO', 'svo': 'SVO', 'SVO': 'SVO',
    'pulkovo': 'LED', 'led': 'LED', 'LED': 'LED',
    'domodedovo': 'DME', 'dme': 'DME', 'DME': 'DME',
    'koltsovo': 'SVX', 'svx': 'SVX', 'SVX': 'SVX',
    'kazan': 'KZN', 'kzn': 'KZN', 'KZN': 'KZN',
    'tolmachevo': 'OVB', 'ovb': 'OVB', 'OVB': 'OVB',
    'adler': 'AER', 'aer': 'AER', 'AER': 'AER',
    'emelyanovo': 'KJA', 'kja': 'KJA', 'KJA': 'KJA',
    'ufa': 'UFA', 'ufa': 'UFA', 'UFA': 'UFA',
    'rostov': 'ROV', 'rov': 'ROV', 'ROV': 'ROV',
}

def validate_completeness(df, required_columns, source_name):
    """
    Проверяет полноту данных — сколько обязательных полей заполнено.
    Возвращает отчёт и процент полноты.
    """
    logger.info(f"[{source_name}] Проверка полноты данных...")
    
    # Проверяем наличие колонок
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        logger.error(f"[{source_name}] Отсутствуют обязательные колонки: {missing_cols}")
        return None, 0
    
    # Считаем пропуски по каждой колонке
    null_counts = df[required_columns].isnull().sum()
    total_cells = len(df) * len(required_columns)
    null_total = null_counts.sum()
    completeness = (1 - null_total / total_cells) * 100
    
    logger.info(f"[{source_name}] Полнота данных: {completeness:.2f}%")
    
    # Логируем пропуски по колонкам
    for col, count in null_counts.items():
        if count > 0:
            logger.warning(f"[{source_name}] Колонка '{col}': {count} пропусков ({count/len(df)*100:.1f}%)")
    
    return null_counts, completeness

def mark_bad_rows(df, max_nulls=2):
    """
    Помечает строки как "плохие", если в них пропущено больше max_nulls колонок.
    Возвращает DataFrame с колонкой 'null_count' и отдельно "плохие" строки.
    """
    df = df.copy()
    df['null_count'] = df.isnull().sum(axis=1)
    
    good_rows = df[df['null_count'] <= max_nulls].copy()
    bad_rows = df[df['null_count'] > max_nulls].copy()
    
    logger.info(f"Строк с пропусками <= {max_nulls}: {len(good_rows)} (оставляем)")
    logger.info(f"Строк с пропусками > {max_nulls}: {len(bad_rows)} (отбрасываем)")
    
    # Удаляем служебную колонку
    good_rows = good_rows.drop('null_count', axis=1)
    
    return good_rows, bad_rows

def smart_fill_missing(df, source_name):
    """
    Заполняет пропуски умными методами:
    - Числовые: медиана (устойчива к выбросам)
    - Категориальные: мода (самое частое значение)
    - Временные: линейная интерполяция
    """
    logger.info(f"[{source_name}] Аппроксимация пропусков...")
    
    df = df.copy()
    fill_report = {}
    
    # Числовые колонки — медиана
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            fill_report[col] = {'method': 'median', 'value': median_val, 'filled': null_count}
            logger.info(f"[{source_name}] '{col}': заполнено {null_count} пропусков медианой ({median_val})")
    
    # Категориальные колонки — мода
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            mode_vals = df[col].mode()
            mode_val = mode_vals[0] if not mode_vals.empty else 'UNKNOWN'
            df[col] = df[col].fillna(mode_val)
            fill_report[col] = {'method': 'mode', 'value': mode_val, 'filled': null_count}
            logger.info(f"[{source_name}] '{col}': заполнено {null_count} пропусков модой ('{mode_val}')")
    
    # Временные колонки — НЕ заполняем (они должны оставаться NULL если отсутствуют)
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    for col in datetime_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.info(f"[{source_name}] '{col}': {null_count} пропусков оставлены (временные данные)")
    
    return df, fill_report

def normalize_airport(airport_name):
    """Нормализует название аэропорта"""
    if pd.isna(airport_name):
        return None
    airport_str = str(airport_name).strip()
    airport_lower = airport_str.lower()
    
    if airport_lower in AIRPORT_MAPPING:
        return AIRPORT_MAPPING[airport_lower]
    
    airport_upper = airport_str.upper()
    if airport_upper in AIRPORT_MAPPING:
        return AIRPORT_MAPPING[airport_upper]
    
    return airport_upper

def normalize_flight_number(flight_num):
    """Нормализует номер рейса"""
    if pd.isna(flight_num):
        return None
    return str(flight_num).upper().replace(' ', '')

def standardize_formats(df, source_name):
    """
    Стандартизирует форматы данных:
    - Аэропорты → 3-буквенный код в верхнем регистре
    - Номера рейсов → без пробелов, в верхнем регистре
    - Статусы → нижний регистр
    - Валюты → верхний регистр
    """
    logger.info(f"[{source_name}] Стандартизация форматов...")
    
    df = df.copy()
    
    # Нормализация аэропортов
    for col in ['departure_airport', 'arrival_airport', 'departure', 'arrival']:
        if col in df.columns:
            df[col] = df[col].apply(normalize_airport)
    
    # Нормализация номеров рейсов
    if 'flight_number' in df.columns:
        df['flight_number'] = df['flight_number'].apply(normalize_flight_number)
    
    # Статусы в нижний регистр
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str).str.lower().str.strip()
    
    # Валюты в верхний регистр
    if 'currency' in df.columns:
        df['currency'] = df['currency'].astype(str).str.upper().str.strip()
    
    return df

def detect_outliers(df, columns, source_name):
    """
    Выявляет выбросы методом IQR (межквартильный размах).
    Возвращает отчёт по выбросам для каждой колонки.
    """
    logger.info(f"[{source_name}] Выявление выбросов...")
    
    outliers_report = {}
    
    for col in columns:
        if col not in df.columns:
            continue
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        
        outliers_report[col] = {
            'count': len(outliers),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'min': float(df[col].min()) if not df[col].empty else None,
            'max': float(df[col].max()) if not df[col].empty else None,
            'mean': float(df[col].mean()) if not df[col].empty else None,
            'median': float(df[col].median()) if not df[col].empty else None
        }
        
        if len(outliers) > 0:
            logger.warning(f"[{source_name}] '{col}': найдено {len(outliers)} выбросов "
                          f"(границы: [{lower_bound:.2f}, {upper_bound:.2f}])")
        else:
            logger.info(f"[{source_name}] '{col}': выбросов не найдено")
    
    return outliers_report

def validate_results(df, source_name, required_columns):
    """
    Финальная проверка результатов очистки.
    Возвращает отчёт о качестве.
    """
    logger.info(f"[{source_name}] Финальная проверка результатов...")
    
    report = {
        'source': source_name,
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'null_counts': df.isnull().sum().to_dict(),
        'duplicate_count': int(df.duplicated().sum()),
        'timestamp': datetime.now().isoformat()
    }
    
    # Проверка обязательных колонок
    missing_cols = set(required_columns) - set(df.columns)
    report['missing_required_columns'] = list(missing_cols)
    
    # Проверка на полностью пустые строки
    empty_rows = df.isnull().all(axis=1).sum()
    report['empty_rows'] = int(empty_rows)
    
    # Общая оценка качества
    total_cells = len(df) * len(df.columns)
    null_total = df.isnull().sum().sum()
    report['completeness_percent'] = float((1 - null_total / total_cells) * 100)
    
    # Логируем отчёт
    logger.info(f"[{source_name}] Итоговый отчёт:")
    logger.info(f"  - Строк: {report['total_rows']}")
    logger.info(f"  - Дубликатов: {report['duplicate_count']}")
    logger.info(f"  - Пустых строк: {report['empty_rows']}")
    logger.info(f"  - Полнота: {report['completeness_percent']:.2f}%")
    
    return report

def transform_bookings(df):
    """Полный цикл трансформации бронирований"""
    logger.info("=" * 60)
    logger.info("ТРАНСФОРМАЦИЯ БРОНИРОВАНИЙ")
    logger.info("=" * 60)
    
    source_name = "bookings"
    required_columns = ['booking_ref', 'passenger_name', 'flight_number', 
                       'departure_airport', 'arrival_airport', 'ticket_price', 'status']
    
    # ШАГ 1: Проверка полноты
    null_report, completeness = validate_completeness(df, required_columns, source_name)
    
    # ШАГ 2: Отбрасываем "плохие" строки (больше 2 пропусков)
    df, bad_rows = mark_bad_rows(df, max_nulls=2)
    
    # Сохраняем отброшенные строки для анализа
    if len(bad_rows) > 0:
        bad_rows.to_parquet('../output/cleaned/bookings_rejected.parquet', index=False)
        logger.warning(f"Сохранено {len(bad_rows)} отброшенных строк в bookings_rejected.parquet")
    
    # ШАГ 3: Удаление дубликатов
    initial_count = len(df)
    df = df.drop_duplicates()
    logger.info(f"Удалено {initial_count - len(df)} дубликатов")
    
    # ШАГ 4: Стандартизация форматов
    df = standardize_formats(df, source_name)
    
    # ШАГ 5: Умное заполнение пропусков
    df, fill_report = smart_fill_missing(df, source_name)
    
    # ШАГ 6: Выявление выбросов
    outliers_report = detect_outliers(df, ['ticket_price'], source_name)
    
    # ШАГ 7: Финальная проверка
    final_report = validate_results(df, source_name, required_columns)
    
    # Сохраняем отчёт о качестве
    quality_report = {
        'source': source_name,
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rejected_rows': len(bad_rows),
        'duplicates_removed': initial_count - len(df) - len(bad_rows),
        'completeness_before': completeness,
        'completeness_after': final_report['completeness_percent'],
        'fill_report': fill_report,
        'outliers_report': outliers_report
    }
    
    return df, quality_report

def transform_flights_report(df):
    """Полный цикл трансформации рейсов"""
    logger.info("=" * 60)
    logger.info("ТРАНСФОРМАЦИЯ РЕЙСОВ")
    logger.info("=" * 60)
    
    source_name = "flights"
    required_columns = ['flight_number', 'departure', 'arrival', 'status']
    
    # ШАГ 1: Проверка полноты
    null_report, completeness = validate_completeness(df, required_columns, source_name)
    
    # ШАГ 2: Отбрасываем "плохие" строки
    df, bad_rows = mark_bad_rows(df, max_nulls=2)
    
    if len(bad_rows) > 0:
        bad_rows.to_parquet('../output/cleaned/flights_rejected.parquet', index=False)
        logger.warning(f"Сохранено {len(bad_rows)} отброшенных строк в flights_rejected.parquet")
    
    # ШАГ 3: Удаление дубликатов
    initial_count = len(df)
    df = df.drop_duplicates()
    logger.info(f"Удалено {initial_count - len(df)} дубликатов")
    
    # ШАГ 4: Стандартизация
    df = standardize_formats(df, source_name)
    
    # ШАГ 5: Умное заполнение пропусков
    df, fill_report = smart_fill_missing(df, source_name)
    
    # ШАГ 6: Выявление выбросов
    outliers_report = detect_outliers(df, [], source_name)
    
    # ШАГ 7: Финальная проверка
    final_report = validate_results(df, source_name, required_columns)
    
    quality_report = {
        'source': source_name,
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rejected_rows': len(bad_rows),
        'duplicates_removed': initial_count - len(df) - len(bad_rows),
        'completeness_before': completeness,
        'completeness_after': final_report['completeness_percent'],
        'fill_report': fill_report,
        'outliers_report': outliers_report
    }
    
    return df, quality_report

def transform_logs(df):
    """Трансформация логов"""
    logger.info("=" * 60)
    logger.info("ТРАНСФОРМАЦИЯ ЛОГОВ")
    logger.info("=" * 60)
    
    source_name = "logs"
    
    initial_count = len(df)
    
    # Нормализация номеров рейсов
    if 'flight_number' in df.columns:
        df['flight_number'] = df['flight_number'].apply(normalize_flight_number)
    
    # Конвертация timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Стандартизация level
    if 'level' in df.columns:
        df['level'] = df['level'].astype(str).str.upper().str.strip()
    
    final_report = validate_results(df, source_name, ['timestamp', 'level'])
    
    quality_report = {
        'source': source_name,
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rejected_rows': 0,
        'duplicates_removed': 0,
        'completeness_after': final_report['completeness_percent']
    }
    
    return df, quality_report

# =====================================================
# ТРАНСФОРМАЦИЯ ПОГОДЫ
# =====================================================

def transform_weather(df):
    """Трансформация погоды"""
    logger.info("=" * 60)
    logger.info("ТРАНСФОРМАЦИЯ ПОГОДЫ")
    logger.info("=" * 60)
    
    source_name = "weather"
    
    initial_count = len(df)
    
    # Конвертация timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Нормализация аэропортов
    if 'airport_code' in df.columns:
        df['airport_code'] = df['airport_code'].apply(normalize_airport)
    
    # Выявление выбросов в температуре
    outliers_report = detect_outliers(df, ['temperature', 'humidity', 'wind_speed'], source_name)
    
    final_report = validate_results(df, source_name, ['airport_code', 'timestamp'])
    
    quality_report = {
        'source': source_name,
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rejected_rows': 0,
        'duplicates_removed': 0,
        'completeness_after': final_report['completeness_percent'],
        'outliers_report': outliers_report
    }
    
    return df, quality_report
def transform_maintenance(df):
    """Трансформация данных обслуживания"""
    logger.info("=" * 60)
    logger.info("ТРАНСФОРМАЦИЯ ОБСЛУЖИВАНИЯ")
    logger.info("=" * 60)
    
    source_name = "maintenance"
    required_columns = ['aircraft_code', 'maintenance_type', 'scheduled_date', 'status', 'cost']
    
    initial_count = len(df)
    
    # Проверка полноты
    null_report, completeness = validate_completeness(df, required_columns, source_name)
    
    # Отбрасываем плохие строки
    df, bad_rows = mark_bad_rows(df, max_nulls=2)
    
    # Стандартизация
    df = df.copy()
    
    # Нормализация кодов самолётов
    if 'aircraft_code' in df.columns:
        df['aircraft_code'] = df['aircraft_code'].astype(str).str.upper().str.strip()
    
    # Стандартизация типов обслуживания
    type_mapping = {
        'technical_inspection': 'technical_inspection',
        'fueling': 'fueling',
        'scheduled_maintenance': 'scheduled_maintenance',
        'repair': 'repair',
        'engine_check': 'engine_check',
        'cabin_check': 'cabin_check'
    }
    
    if 'maintenance_type' in df.columns:
        df['maintenance_type'] = df['maintenance_type'].astype(str).str.lower().str.strip()
        df['maintenance_type'] = df['maintenance_type'].map(type_mapping).fillna(df['maintenance_type'])
    
    # Стандартизация статусов
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str).str.lower().str.strip()
    
    # Конвертация дат
    if 'scheduled_date' in df.columns:
        df['scheduled_date'] = pd.to_datetime(df['scheduled_date'], errors='coerce')
    
    if 'completed_date' in df.columns:
        df['completed_date'] = pd.to_datetime(df['completed_date'], errors='coerce')
    
    # Конвертация стоимости
    if 'cost' in df.columns:
        df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
    
    # Умное заполнение пропусков
    df, fill_report = smart_fill_missing(df, source_name)
    
    # Финальная проверка
    final_report = validate_results(df, source_name, required_columns)
    
    quality_report = {
        'source': source_name,
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rejected_rows': len(bad_rows),
        'duplicates_removed': initial_count - len(df) - len(bad_rows),
        'completeness_after': final_report['completeness_percent'],
        'fill_report': fill_report
    }
    
    return df, quality_report
if __name__ == '__main__':
    logger.info("НАЧАЛО ЭТАПА TRANSFORM")
    
    all_quality_reports = []
    
    try:
        # Загружаем raw данные
        bookings_df = pd.read_parquet('../output/raw/bookings_raw.parquet')
        csv_df = pd.read_parquet('../output/raw/flights_report_raw.parquet')
        logs_df = pd.read_parquet('../output/raw/logs_raw.parquet')
        weather_df = pd.read_parquet('../output/raw/weather_raw.parquet')
        maintenance_df = pd.read_parquet('../output/raw/maintenance_raw.parquet')
        
        # Трансформируем
        bookings_clean, bookings_report = transform_bookings(bookings_df)
        csv_clean, csv_report = transform_flights_report(csv_df)
        logs_clean, logs_report = transform_logs(logs_df)
        weather_clean, weather_report = transform_weather(weather_df)
        maintenance_clean, maintenance_report = transform_maintenance(maintenance_df)
        
        all_quality_reports = [bookings_report, csv_report, logs_report, weather_report, maintenance_report]
        
        # Сохраняем cleaned данные
        os.makedirs('../output/cleaned', exist_ok=True)
        
        bookings_clean.to_parquet('../output/cleaned/bookings_clean.parquet', index=False)
        csv_clean.to_parquet('../output/cleaned/flights_report_clean.parquet', index=False)
        logs_clean.to_parquet('../output/cleaned/logs_clean.parquet', index=False)
        weather_clean.to_parquet('../output/cleaned/weather_clean.parquet', index=False)
        maintenance_clean.to_parquet('../output/cleaned/maintenance_clean.parquet', index=False)
        
        # Сохраняем общий отчёт о качестве
        os.makedirs('../reports', exist_ok=True)
        with open('../reports/quality_report.json', 'w', encoding='utf-8') as f:
            json.dump(all_quality_reports, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("=" * 80)
        logger.info("ЭТАП TRANSFORM ЗАВЕРШЕН УСПЕШНО")
        logger.info("=" * 80)
        
        # Итоговая сводка
        logger.info("\nИТОГОВАЯ СВОДКА ПО КАЧЕСТВУ ДАННЫХ:")
        logger.info("-" * 60)
        for report in all_quality_reports:
            logger.info(f"Источник: {report['source']}")
            logger.info(f"  Строк до: {report['initial_rows']}")
            logger.info(f"  Строк после: {report['final_rows']}")
            logger.info(f"  Отброшено: {report.get('rejected_rows', 0)}")
            logger.info(f"  Дубликатов удалено: {report.get('duplicates_removed', 0)}")
            logger.info(f"  Полнота: {report.get('completeness_after', 0):.2f}%")
            logger.info("-" * 60)
        
        logger.info(f"\nОтчёт о качестве сохранён: reports/quality_report.json")
        
    except Exception as e:
        logger.error(f"Ошибка на этапе Transform: {str(e)}", exc_info=True)
        raise
