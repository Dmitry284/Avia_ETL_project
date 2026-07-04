-- Создаем схему для DWH
CREATE SCHEMA IF NOT EXISTS dwh;

-- Измерение: Аэропорты
CREATE TABLE IF NOT EXISTS dwh.dim_airports (
    airport_key SERIAL PRIMARY KEY,
    airport_code VARCHAR(50) NOT NULL UNIQUE,
    airport_name VARCHAR(200),
    city VARCHAR(100),
    country VARCHAR(100)
);

-- Измерение: Самолеты
CREATE TABLE IF NOT EXISTS dwh.dim_aircraft (
    aircraft_key SERIAL PRIMARY KEY,
    aircraft_code VARCHAR(50) NOT NULL UNIQUE,
    aircraft_type VARCHAR(100),
    capacity INTEGER,
    manufacturer VARCHAR(100)
);

-- Измерение: Даты
CREATE TABLE IF NOT EXISTS dwh.dim_dates (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    quarter INTEGER,
    is_weekend BOOLEAN
);

-- Факт: Рейсы (упрощенная структура под реальные данные)
CREATE TABLE IF NOT EXISTS dwh.fact_flights (
    flight_key SERIAL PRIMARY KEY,
    flight_date DATE,
    flight_number VARCHAR(20),
    departure VARCHAR(50),
    arrival VARCHAR(50),
    scheduled_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    status VARCHAR(50),
    aircraft_id VARCHAR(50)
);

-- Факт: Бронирования (упрощенная структура под реальные данные)
CREATE TABLE IF NOT EXISTS dwh.fact_bookings (
    booking_key SERIAL PRIMARY KEY,
    booking_ref VARCHAR(20),
    passenger_name VARCHAR(200),
    flight_number VARCHAR(20),
    departure_airport VARCHAR(50),
    arrival_airport VARCHAR(50),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    aircraft_type VARCHAR(100),
    ticket_price DECIMAL(10,2),
    currency VARCHAR(10),
    booking_date TIMESTAMP,
    status VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX idx_fact_flights_date ON dwh.fact_flights(flight_date);
CREATE INDEX idx_fact_flights_number ON dwh.fact_flights(flight_number);
CREATE INDEX idx_fact_bookings_ref ON dwh.fact_bookings(booking_ref);
CREATE INDEX idx_fact_bookings_flight ON dwh.fact_bookings(flight_number);
