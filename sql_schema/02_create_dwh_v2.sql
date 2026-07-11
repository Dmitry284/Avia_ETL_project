DROP SCHEMA IF EXISTS dwh CASCADE;
CREATE SCHEMA dwh;
-- Справочник аэропортов
CREATE TABLE dwh.dim_airports (
    airport_id SERIAL PRIMARY KEY,
    airport_code VARCHAR(10) NOT NULL UNIQUE,
    airport_name VARCHAR(200),
    city VARCHAR(100),
    country VARCHAR(100)
);

-- Справочник самолётов
CREATE TABLE dwh.dim_aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    aircraft_code VARCHAR(50) NOT NULL UNIQUE,
    aircraft_type VARCHAR(100),
    capacity INTEGER,
    manufacturer VARCHAR(100)
);

-- Справочник дат
CREATE TABLE dwh.dim_dates (
    date_id INTEGER PRIMARY KEY,
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

-- Справочник рейсов
CREATE TABLE dwh.dim_flights (
    flight_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    departure_airport_id INTEGER REFERENCES dwh.dim_airports(airport_id),
    arrival_airport_id INTEGER REFERENCES dwh.dim_airports(airport_id),
    aircraft_id INTEGER REFERENCES dwh.dim_aircraft(aircraft_id),
    scheduled_duration_minutes INTEGER,
    UNIQUE(flight_number, departure_airport_id, arrival_airport_id)
);

-- Справочник пассажиров
CREATE TABLE dwh.dim_passengers (
    passenger_id SERIAL PRIMARY KEY,
    passenger_name VARCHAR(200) NOT NULL UNIQUE
);

-- Справочник погоды
CREATE TABLE dwh.dim_weather (
    weather_id SERIAL PRIMARY KEY,
    airport_id INTEGER REFERENCES dwh.dim_airports(airport_id),
    observation_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity INTEGER,
    wind_speed DECIMAL(5,2),
    visibility INTEGER,
    conditions VARCHAR(50),
    UNIQUE(airport_id, observation_time)
);

-- Справочник типов обслуживания самолётов
CREATE TABLE dwh.dim_maintenance_types (
    maintenance_type_id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(200),
    description TEXT
);

-- Справочник статусов
CREATE TABLE dwh.dim_statuses (
    status_id SERIAL PRIMARY KEY,
    status_code VARCHAR(30) NOT NULL UNIQUE,
    status_name VARCHAR(100),
    category VARCHAR(30)  -- 'booking', 'flight', 'maintenance'
);

-- Все атрибуты зависят только от booking_id
CREATE TABLE dwh.fact_bookings (
    booking_id SERIAL PRIMARY KEY,
    booking_ref VARCHAR(20) NOT NULL,
    passenger_id INTEGER REFERENCES dwh.dim_passengers(passenger_id),
    flight_id INTEGER REFERENCES dwh.dim_flights(flight_id),
    booking_date_id INTEGER REFERENCES dwh.dim_dates(date_id),
    status_id INTEGER REFERENCES dwh.dim_statuses(status_id),
    ticket_price DECIMAL(10,2),
    currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- выполненные рейсы
CREATE TABLE dwh.fact_flights (
    flight_instance_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES dwh.dim_flights(flight_id),
    flight_date_id INTEGER REFERENCES dwh.dim_dates(date_id),
    status_id INTEGER REFERENCES dwh.dim_statuses(status_id),
    actual_departure_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    delay_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  выручка по рейсам
CREATE TABLE dwh.fact_revenue (
    revenue_id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES dwh.dim_flights(flight_id),
    date_id INTEGER REFERENCES dwh.dim_dates(date_id),
    total_revenue DECIMAL(15,2) NOT NULL,
    passenger_count INTEGER NOT NULL,
    avg_ticket_price DECIMAL(10,2),
    confirmed_count INTEGER,
    cancelled_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- техническое обслуживание самолётов
CREATE TABLE dwh.fact_maintenance (
    maintenance_id SERIAL PRIMARY KEY,
    aircraft_id INTEGER REFERENCES dwh.dim_aircraft(aircraft_id),
    maintenance_type_id INTEGER REFERENCES dwh.dim_maintenance_types(maintenance_type_id),
    status_id INTEGER REFERENCES dwh.dim_statuses(status_id),
    scheduled_date DATE NOT NULL,
    completed_date DATE,
    cost DECIMAL(12,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO dwh.dim_statuses (status_code, status_name, category) VALUES
('confirmed', 'Подтверждено', 'booking'),
('cancelled', 'Отменено', 'booking'),
('pending', 'В ожидании', 'booking'),
('completed', 'Завершено', 'booking'),
('landed', 'Приземлился', 'flight'),
('scheduled', 'Запланирован', 'flight'),
('delayed', 'Задержан', 'flight'),
('diverted', 'Перенаправлен', 'flight'),
('planned', 'Запланировано', 'maintenance'),
('in_progress', 'В процессе', 'maintenance');

INSERT INTO dwh.dim_maintenance_types (type_code, type_name, description) VALUES
('technical_inspection', 'Технический осмотр', 'Плановая проверка технического состояния'),
('fueling', 'Заправка топливом', 'Заправка самолёта авиатопливом'),
('scheduled_maintenance', 'Регламентное ТО', 'Плановое техническое обслуживание'),
('repair', 'Ремонт', 'Устранение неисправностей'),
('engine_check', 'Проверка двигателя', 'Диагностика двигателей'),
('cabin_check', 'Проверка салона', 'Проверка состояния салона');

CREATE INDEX idx_fact_bookings_flight ON dwh.fact_bookings(flight_id);
CREATE INDEX idx_fact_bookings_passenger ON dwh.fact_bookings(passenger_id);
CREATE INDEX idx_fact_bookings_date ON dwh.fact_bookings(booking_date_id);
CREATE INDEX idx_fact_bookings_status ON dwh.fact_bookings(status_id);

CREATE INDEX idx_fact_flights_flight ON dwh.fact_flights(flight_id);
CREATE INDEX idx_fact_flights_date ON dwh.fact_flights(flight_date_id);
CREATE INDEX idx_fact_flights_status ON dwh.fact_flights(status_id);

CREATE INDEX idx_fact_revenue_flight ON dwh.fact_revenue(flight_id);
CREATE INDEX idx_fact_revenue_date ON dwh.fact_revenue(date_id);

CREATE INDEX idx_fact_maintenance_aircraft ON dwh.fact_maintenance(aircraft_id);
CREATE INDEX idx_fact_maintenance_type ON dwh.fact_maintenance(maintenance_type_id);

CREATE INDEX idx_dim_flights_number ON dwh.dim_flights(flight_number);
CREATE INDEX idx_dim_weather_airport ON dwh.dim_weather(airport_id);
