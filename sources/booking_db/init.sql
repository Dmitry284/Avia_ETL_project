
CREATE DATABASE aviation_dwh;

-- Переключаемся на booking_db
\c booking_db;

-- Таблица сырых бронирований (УВЕЛИЧЕНЫ длины полей!)
CREATE TABLE raw_bookings (
    id SERIAL PRIMARY KEY,
    booking_ref VARCHAR(20),
    passenger_name VARCHAR(200),
    flight_number VARCHAR(20),
    departure_airport VARCHAR(50),
    arrival_airport VARCHAR(50),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    aircraft_type VARCHAR(50),
    ticket_price DECIMAL(10,2),
    currency VARCHAR(10),
    booking_date TIMESTAMP,
    status VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Тестовые данные с "грязью"
INSERT INTO raw_bookings (booking_ref, passenger_name, flight_number, departure_airport, arrival_airport, departure_time, arrival_time, aircraft_type, ticket_price, currency, booking_date, status) VALUES
('BK001', 'Иванов Иван Иванович', 'SU101', 'SVO', 'LED', '2024-01-15 10:00:00', '2024-01-15 12:30:00', 'Boeing 737', 15000.00, 'RUB', '2024-01-10 14:30:00', 'confirmed'),
('BK002', 'Petrov Petr', 'su 102', 'sheremetyevo', 'pulkovo', '2024-01-15 14:00:00', '2024-01-15 16:30:00', 'Airbus A320', 12500.00, 'rub', '2024-01-11 09:15:00', 'CONFIRMED'),
('BK003', 'Сидорова Мария', 'SU103', 'SVO', 'SVX', '2024-01-16 08:00:00', '2024-01-16 12:00:00', 'Boeing 777', 25000.00, 'RUB', '2024-01-12 16:45:00', 'cancelled'),
('BK004', 'Smirnov Alexey', 'SU 104', 'DME', 'KZN', '2024-01-16 11:30:00', '2024-01-16 13:45:00', 'Boeing 737', 18000.00, 'RUB', '2024-01-13 11:20:00', 'confirmed'),
('BK005', 'Козлова Елена', 'SU105', 'SVO', 'LED', '2024-01-17 15:00:00', '2024-01-17 17:30:00', 'Airbus A320', NULL, 'RUB', '2024-01-14 10:00:00', 'confirmed'),
('BK001', 'Иванов Иван Иванович', 'SU101', 'SVO', 'LED', '2024-01-15 10:00:00', '2024-01-15 12:30:00', 'Boeing 737', 15000.00, 'RUB', '2024-01-10 14:30:00', 'confirmed'),
('BK006', 'Новиков Дмитрий', 'SU106', 'LED', 'SVO', '2024-01-17 18:00:00', '2024-01-17 20:30:00', 'Boeing 737', 14500.00, 'RUB', '2024-01-14 15:30:00', 'confirmed'),
('BK007', 'Волкова Анна', 'SU107', 'SVO', 'OVB', '2024-01-18 09:00:00', '2024-01-18 15:00:00', 'Airbus A321', 28000.00, 'RUB', '2024-01-15 09:00:00', 'confirmed');

-- Таблица самолетов
CREATE TABLE raw_aircraft (
    id SERIAL PRIMARY KEY,
    aircraft_code VARCHAR(20),
    aircraft_type VARCHAR(100),
    capacity INTEGER,
    manufacturer VARCHAR(100)
);

INSERT INTO raw_aircraft (aircraft_code, aircraft_type, capacity, manufacturer) VALUES
('B737', 'Boeing 737', 180, 'Boeing'),
('A320', 'Airbus A320', 150, 'Airbus'),
('B777', 'Boeing 777', 350, 'Boeing'),
('A321', 'Airbus A321', 185, 'Airbus');

-- Таблица аэропортов
CREATE TABLE raw_airports (
    id SERIAL PRIMARY KEY,
    airport_code VARCHAR(20),
    airport_name VARCHAR(200),
    city VARCHAR(100),
    country VARCHAR(100)
);

INSERT INTO raw_airports (airport_code, airport_name, city, country) VALUES
('SVO', 'Шереметьево', 'Москва', 'Россия'),
('LED', 'Пулково', 'Санкт-Петербург', 'Россия'),
('DME', 'Домодедово', 'Москва', 'Россия'),
('SVX', 'Кольцово', 'Екатеринбург', 'Россия'),
('KZN', 'Казань', 'Казань', 'Россия'),
('OVB', 'Толмачево', 'Новосибирск', 'Россия');
