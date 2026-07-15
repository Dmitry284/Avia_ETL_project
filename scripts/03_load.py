import pandas as pd
import logging
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

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

# Создаем подключение к DWH
def get_dwh_engine():
    """Создает подключение к целевой БД (aviation_dwh)"""
    host = os.getenv('DWH_DB_HOST', 'localhost')
    port = os.getenv('DWH_DB_PORT', '5434')
    user = os.getenv('DWH_DB_USER', 'aviation_user')
    password = os.getenv('DWH_DB_PASSWORD', 'aviation_pass')
    dbname = os.getenv('DWH_DB_NAME', 'aviation_dwh')
    
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    return create_engine(connection_string)

def load_dim_airports(engine):
    logger.info("Загрузка dim_airports...")

    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')

    airports_from_bookings = set(bookings_df['departure_airport'].dropna().unique()) | \
                             set(bookings_df['arrival_airport'].dropna().unique())
    airports_from_flights = set(flights_df['departure'].dropna().unique()) | \
                            set(flights_df['arrival'].dropna().unique())
    
    all_airports = airports_from_bookings | airports_from_flights

    airports_df = pd.DataFrame({
        'airport_code': list(all_airports),
        'airport_name': list(all_airports),
        'city': list(all_airports),
        'country': ['Россия'] * len(all_airports)
    })

    with engine.connect() as conn:
        for _, row in airports_df.iterrows():
            query = text("""
                INSERT INTO dwh.dim_airports (airport_code, airport_name, city, country)
                VALUES (:code, :name, :city, :country)
                ON CONFLICT (airport_code) DO UPDATE 
                SET airport_name = EXCLUDED.airport_name,
                    city = EXCLUDED.city,
                    country = EXCLUDED.country
            """)
            conn.execute(query, {
                'code': row['airport_code'],
                'name': row['airport_name'],
                'city': row['city'],
                'country': row['country']
            })
        conn.commit()
    
    logger.info(f"Загружено {len(airports_df)} аэропортов")

def load_dim_aircraft(engine):
    logger.info("Загрузка dim_aircraft...")
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')

    aircraft_from_bookings = set(bookings_df['aircraft_type'].dropna().unique())
    aircraft_from_flights = set(flights_df['aircraft_id'].dropna().unique())
    all_aircraft = aircraft_from_bookings | aircraft_from_flights
    
    aircraft_df = pd.DataFrame({
        'aircraft_code': list(all_aircraft),
        'aircraft_type': list(all_aircraft),
        'capacity': [180] * len(all_aircraft),
        'manufacturer': ['Unknown'] * len(all_aircraft)
    })
    
    with engine.connect() as conn:
        for _, row in aircraft_df.iterrows():
            query = text("""
                INSERT INTO dwh.dim_aircraft (aircraft_code, aircraft_type, capacity, manufacturer)
                VALUES (:code, :type, :capacity, :manufacturer)
                ON CONFLICT (aircraft_code) DO UPDATE 
                SET aircraft_type = EXCLUDED.aircraft_type,
                    capacity = EXCLUDED.capacity,
                    manufacturer = EXCLUDED.manufacturer
            """)
            conn.execute(query, {
                'code': row['aircraft_code'],
                'type': row['aircraft_type'],
                'capacity': row['capacity'],
                'manufacturer': row['manufacturer']
            })
        conn.commit()
    
    logger.info(f"Загружено {len(aircraft_df)} самолётов")

def load_dim_dates(engine):
    logger.info("Загрузка dim_dates...")
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')

    dates = set()
    if 'departure_time' in bookings_df.columns:
        dates.update(pd.to_datetime(bookings_df['departure_time']).dt.date.dropna().unique())
    if 'booking_date' in bookings_df.columns:
        dates.update(pd.to_datetime(bookings_df['booking_date']).dt.date.dropna().unique())
    if 'flight_date' in flights_df.columns:
        dates.update(pd.to_datetime(flights_df['flight_date']).dt.date.dropna().unique())
    
    dates = sorted([d for d in dates if pd.notna(d)])
    
    dates_df = pd.DataFrame({
        'date_id': [int(d.strftime('%Y%m%d')) for d in dates],
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

    with engine.connect() as conn:
        for _, row in dates_df.iterrows():
            query = text("""
                INSERT INTO dwh.dim_dates (date_id, full_date, year, month, day, 
                                          day_of_week, day_name, month_name, quarter, is_weekend)
                VALUES (:date_id, :full_date, :year, :month, :day, 
                        :day_of_week, :day_name, :month_name, :quarter, :is_weekend)
                ON CONFLICT (date_id) DO UPDATE 
                SET full_date = EXCLUDED.full_date,
                    year = EXCLUDED.year,
                    month = EXCLUDED.month,
                    day = EXCLUDED.day,
                    day_of_week = EXCLUDED.day_of_week,
                    day_name = EXCLUDED.day_name,
                    month_name = EXCLUDED.month_name,
                    quarter = EXCLUDED.quarter,
                    is_weekend = EXCLUDED.is_weekend
            """)
            conn.execute(query, {
                'date_id': int(row['date_id']),
                'full_date': row['full_date'],
                'year': int(row['year']),
                'month': int(row['month']),
                'day': int(row['day']),
                'day_of_week': int(row['day_of_week']),
                'day_name': str(row['day_name']),
                'month_name': str(row['month_name']),
                'quarter': int(row['quarter']),
                'is_weekend': bool(row['is_weekend'])
            })
        conn.commit()
    
    logger.info(f"Загружено {len(dates_df)} дат")

def load_dim_passengers(engine):
    logger.info("Загрузка dim_passengers...")
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')

    passengers = bookings_df['passenger_name'].dropna().unique()
    
    passengers_df = pd.DataFrame({
        'passenger_name': passengers
    })
    
    with engine.connect() as conn:
        for _, row in passengers_df.iterrows():
            query = text("""
                INSERT INTO dwh.dim_passengers (passenger_name)
                VALUES (:name)
                ON CONFLICT (passenger_name) DO NOTHING
            """)
            conn.execute(query, {'name': row['passenger_name']})
        conn.commit()
    
    logger.info(f"Загружено {len(passengers_df)} пассажиров")

def load_dim_flights(engine):
    logger.info("Загрузка dim_flights...")
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')
    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')

    unique_flights = []

    for _, row in bookings_df.drop_duplicates(subset=['flight_number', 'departure_airport', 'arrival_airport']).iterrows():
        unique_flights.append({
            'flight_number': row['flight_number'],
            'departure_airport': row['departure_airport'],
            'arrival_airport': row['arrival_airport'],
            'aircraft_type': row.get('aircraft_type')
        })

    for _, row in flights_df.drop_duplicates(subset=['flight_number', 'departure', 'arrival']).iterrows():
        unique_flights.append({
            'flight_number': row['flight_number'],
            'departure_airport': row['departure'],
            'arrival_airport': row['arrival'],
            'aircraft_type': row.get('aircraft_id')
        })

    flights_unique_df = pd.DataFrame(unique_flights).drop_duplicates(
        subset=['flight_number', 'departure_airport', 'arrival_airport']
    )

    with engine.connect() as conn:
        airports_df = pd.read_sql("SELECT airport_id, airport_code FROM dwh.dim_airports", conn)
        aircraft_df = pd.read_sql("SELECT aircraft_id, aircraft_code FROM dwh.dim_aircraft", conn)

    airport_map = dict(zip(airports_df['airport_code'], airports_df['airport_id']))
    aircraft_map = dict(zip(aircraft_df['aircraft_code'], aircraft_df['aircraft_id']))

    with engine.connect() as conn:
        for _, row in flights_unique_df.iterrows():
            dep_id = airport_map.get(row['departure_airport'])
            arr_id = airport_map.get(row['arrival_airport'])
            ac_id = aircraft_map.get(row['aircraft_type'])
            
            query = text("""
                INSERT INTO dwh.dim_flights (flight_number, departure_airport_id, arrival_airport_id, aircraft_id)
                VALUES (:number, :dep_id, :arr_id, :ac_id)
                ON CONFLICT (flight_number, departure_airport_id, arrival_airport_id) DO UPDATE 
                SET aircraft_id = EXCLUDED.aircraft_id
            """)
            conn.execute(query, {
                'number': row['flight_number'],
                'dep_id': dep_id,
                'arr_id': arr_id,
                'ac_id': ac_id
            })
        conn.commit()
    
    logger.info(f"Загружено {len(flights_unique_df)} маршрутов")

def load_fact_bookings(engine):
    logger.info("Загрузка fact_bookings...")
    
    bookings_df = pd.read_parquet('../output/cleaned/bookings_clean.parquet')

    with engine.connect() as conn:
        passengers_df = pd.read_sql("SELECT passenger_id, passenger_name FROM dwh.dim_passengers", conn)
        flights_df = pd.read_sql("""
            SELECT f.flight_id, f.flight_number, 
                   da.airport_code as dep_code, aa.airport_code as arr_code
            FROM dwh.dim_flights f
            JOIN dwh.dim_airports da ON f.departure_airport_id = da.airport_id
            JOIN dwh.dim_airports aa ON f.arrival_airport_id = aa.airport_id
        """, conn)
        statuses_df = pd.read_sql("SELECT status_id, status_code FROM dwh.dim_statuses WHERE category = 'booking'", conn)
        dates_df = pd.read_sql("SELECT date_id, full_date FROM dwh.dim_dates", conn)
    
    passenger_map = dict(zip(passengers_df['passenger_name'], passengers_df['passenger_id']))
    status_map = dict(zip(statuses_df['status_code'], statuses_df['status_id']))
    date_map = dict(zip(pd.to_datetime(dates_df['full_date']).dt.date, dates_df['date_id']))

    flight_map = {}
    for _, row in flights_df.iterrows():
        key = (row['flight_number'], row['dep_code'], row['arr_code'])
        flight_map[key] = row['flight_id']
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM dwh.fact_bookings"))
        conn.commit()

    records = []
    for _, row in bookings_df.iterrows():
        passenger_id = passenger_map.get(row['passenger_name'])
        flight_id = flight_map.get((row['flight_number'], row['departure_airport'], row['arrival_airport']))
        booking_date = pd.to_datetime(row['booking_date']).date() if pd.notna(row['booking_date']) else None
        booking_date_id = date_map.get(booking_date)
        status_id = status_map.get(row['status'])
        
        records.append({
            'booking_ref': row['booking_ref'],
            'passenger_id': passenger_id,
            'flight_id': flight_id,
            'booking_date_id': booking_date_id,
            'status_id': status_id,
            'ticket_price': row['ticket_price'],
            'currency': row['currency']
        })
    
    records_df = pd.DataFrame(records)
    records_df.to_sql('fact_bookings', engine, schema='dwh', if_exists='append', index=False)
    
    logger.info(f"Загружено {len(records_df)} бронирований")

def load_fact_flights(engine):
    logger.info("Загрузка fact_flights...")

    flights_df = pd.read_parquet('../output/cleaned/flights_report_clean.parquet')

    with engine.connect() as conn:
        flights_dim_df = pd.read_sql("""
            SELECT f.flight_id, f.flight_number,
                   da.airport_code AS dep_code, aa.airport_code AS arr_code
            FROM dwh.dim_flights f
            JOIN dwh.dim_airports da ON f.departure_airport_id = da.airport_id
            JOIN dwh.dim_airports aa ON f.arrival_airport_id = aa.airport_id
        """, conn)

        statuses_df = pd.read_sql("""
            SELECT status_id, status_code
            FROM dwh.dim_statuses
            WHERE category = 'flight'
        """, conn)

        dates_df = pd.read_sql("SELECT date_id, full_date FROM dwh.dim_dates", conn)

    flight_map = {}
    for _, row in flights_dim_df.iterrows():
        key = (row['flight_number'], row['dep_code'], row['arr_code'])
        flight_map[key] = row['flight_id']

    status_map = dict(zip(statuses_df['status_code'], statuses_df['status_id']))
    date_map = dict(zip(pd.to_datetime(dates_df['full_date']).dt.date, dates_df['date_id']))

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM dwh.fact_flights"))
        conn.commit()

    records = []
    for _, row in flights_df.iterrows():
        flight_id = flight_map.get((row['flight_number'], row['departure'], row['arrival']))

        flight_date = pd.to_datetime(row['flight_date']).date() if pd.notna(row['flight_date']) else None
        flight_date_id = date_map.get(flight_date)
        status_id = status_map.get(row['status'])

        delay_minutes = None
        if pd.notna(row['actual_departure']) and pd.notna(row['scheduled_departure']):
            delay = (pd.to_datetime(row['actual_departure']) -
                     pd.to_datetime(row['scheduled_departure'])).total_seconds() / 60
            delay_minutes = int(delay) if delay > 0 else 0

        records.append({
            'flight_id': flight_id,
            'flight_date_id': flight_date_id,
            'status_id': status_id,
            'scheduled_departure_time': row.get('scheduled_departure'),
            'scheduled_arrival_time': row.get('scheduled_arrival'),
            'actual_departure_time': row.get('actual_departure'),
            'actual_arrival_time': row.get('actual_arrival'),
            'delay_minutes': delay_minutes
        })

    records_df = pd.DataFrame(records)
    records_df.to_sql('fact_flights', engine, schema='dwh', if_exists='append', index=False)

    logger.info(f"Загружено {len(records_df)} рейсов")

def load_fact_revenue(engine):
    logger.info("Загрузка fact_revenue...")
    
    query = """
    SELECT 
        fb.flight_id,
        fb.booking_date_id as date_id,
        SUM(fb.ticket_price) as total_revenue,
        COUNT(fb.booking_id) as passenger_count,
        AVG(fb.ticket_price) as avg_ticket_price,
        COUNT(CASE WHEN ds.status_code = 'confirmed' THEN 1 END) as confirmed_count,
        COUNT(CASE WHEN ds.status_code = 'cancelled' THEN 1 END) as cancelled_count
    FROM dwh.fact_bookings fb
    JOIN dwh.dim_statuses ds ON fb.status_id = ds.status_id
    WHERE ds.status_code IN ('confirmed', 'completed')
    GROUP BY fb.flight_id, fb.booking_date_id
    """
    
    with engine.connect() as conn:
        revenue_df = pd.read_sql(query, conn)
        conn.execute(text("DELETE FROM dwh.fact_revenue"))
        conn.commit()
    
    revenue_df.to_sql('fact_revenue', engine, schema='dwh', if_exists='append', index=False)
    
    logger.info(f"Загружено {len(revenue_df)} записей выручки")

def load_fact_maintenance(engine):
    logger.info("Загрузка fact_maintenance...")
    
    maintenance_df = pd.read_parquet('../output/cleaned/maintenance_clean.parquet')

    with engine.connect() as conn:
        aircraft_df = pd.read_sql("SELECT aircraft_id, aircraft_code FROM dwh.dim_aircraft", conn)
        maint_types_df = pd.read_sql("SELECT maintenance_type_id, type_code FROM dwh.dim_maintenance_types", conn)
        statuses_df = pd.read_sql("SELECT status_id, status_code FROM dwh.dim_statuses WHERE category = 'maintenance'", conn)
    
    aircraft_map = dict(zip(aircraft_df['aircraft_code'], aircraft_df['aircraft_id']))
    maint_type_map = dict(zip(maint_types_df['type_code'], maint_types_df['maintenance_type_id']))
    status_map = dict(zip(statuses_df['status_code'], statuses_df['status_id']))
    

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM dwh.fact_maintenance"))
        conn.commit()

    records = []
    for _, row in maintenance_df.iterrows():
        aircraft_id = aircraft_map.get(row['aircraft_code'])
        maint_type_id = maint_type_map.get(row['maintenance_type'])
        status_id = status_map.get(row['status'])
        
        records.append({
            'aircraft_id': aircraft_id,
            'maintenance_type_id': maint_type_id,
            'status_id': status_id,
            'scheduled_date': row['scheduled_date'],
            'completed_date': row.get('completed_date'),
            'cost': row['cost'],
            'description': row.get('description', '')
        })
    
    records_df = pd.DataFrame(records)
    records_df.to_sql('fact_maintenance', engine, schema='dwh', if_exists='append', index=False)
    
    logger.info(f"Загружено {len(records_df)} записей обслуживания")
if __name__ == '__main__':
    logger.info("НАЧАЛО ЭТАПА LOAD")
    
    try:
        engine = get_dwh_engine()

        load_dim_airports(engine)
        load_dim_aircraft(engine)
        load_dim_dates(engine)
        load_dim_passengers(engine)
        load_dim_flights(engine)
        load_fact_bookings(engine)
        load_fact_flights(engine)
        load_fact_revenue(engine)
        load_fact_maintenance(engine)
        logger.info("ЭТАП LOAD ЗАВЕРШЕН УСПЕШНО")
        
    except Exception as e:
        logger.error(f"Ошибка на этапе Load: {str(e)}", exc_info=True)
        raise
