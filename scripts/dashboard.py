import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Создаем подключение к DWH
@st.cache_resource
def get_dwh_engine():
    host = os.getenv('DWH_DB_HOST', 'localhost')
    port = os.getenv('DWH_DB_PORT', '5434')
    user = os.getenv('DWH_DB_USER', 'aviation_user')
    password = os.getenv('DWH_DB_PASSWORD', 'aviation_pass')
    dbname = os.getenv('DWH_DB_NAME', 'aviation_dwh')
    
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    return create_engine(connection_string)

# Настройка страницы
st.set_page_config(
    page_title="Aviation Analytics Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("✈️ Aviation Analytics Dashboard")
st.markdown("---")

# Получаем данные
engine = get_dwh_engine()

# Боковая панель
st.sidebar.header("Фильтры")

# Загружаем данные
@st.cache_data
def load_data():
    flights_df = pd.read_sql("SELECT * FROM dwh.fact_flights", engine)
    bookings_df = pd.read_sql("SELECT * FROM dwh.fact_bookings", engine)
    airports_df = pd.read_sql("SELECT * FROM dwh.dim_airports", engine)
    aircraft_df = pd.read_sql("SELECT * FROM dwh.dim_aircraft", engine)
    return flights_df, bookings_df, airports_df, aircraft_df

flights_df, bookings_df, airports_df, aircraft_df = load_data()

# KPI метрики
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Всего рейсов", len(flights_df))

with col2:
    st.metric("Всего бронирований", len(bookings_df))

with col3:
    total_revenue = bookings_df['ticket_price'].sum()
    st.metric("Общая выручка", f"{total_revenue:,.0f} ₽")

with col4:
    avg_price = bookings_df['ticket_price'].mean()
    st.metric("Средняя цена билета", f"{avg_price:,.0f} ₽")

st.markdown("---")

# Вкладки
tab1, tab2, tab3, tab4 = st.tabs(["📊 Рейсы", "💰 Бронирования", "🛫 Аэропорты", "✈️ Самолеты"])

with tab1:
    st.header("Анализ рейсов")
    
    # Статусы рейсов
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение статусов рейсов")
        status_counts = flights_df['status'].value_counts().reset_index()
        status_counts.columns = ['Статус', 'Количество']
        fig1 = px.pie(status_counts, values='Количество', names='Статус', 
                      title='Статусы рейсов')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Рейсы по датам")
        flights_by_date = flights_df.groupby('flight_date').size().reset_index(name='count')
        fig2 = px.line(flights_by_date, x='flight_date', y='count', 
                       title='Количество рейсов по датам')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Таблица рейсов
    st.subheader("Детали рейсов")
    st.dataframe(flights_df, use_container_width=True)

with tab2:
    st.header("Анализ бронирований")
    
    # Статусы бронирований
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение статусов бронирований")
        booking_status = bookings_df['status'].value_counts().reset_index()
        booking_status.columns = ['Статус', 'Количество']
        fig3 = px.bar(booking_status, x='Статус', y='Количество', 
                      title='Статусы бронирований', color='Статус')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("Выручка по аэропортам вылета")
        revenue_by_airport = bookings_df.groupby('departure_airport')['ticket_price'].sum().reset_index()
        fig4 = px.bar(revenue_by_airport, x='departure_airport', y='ticket_price', 
                      title='Выручка по аэропортам вылета')
        st.plotly_chart(fig4, use_container_width=True)
    
    # Распределение цен
    st.subheader("Распределение цен билетов")
    fig5 = px.histogram(bookings_df, x='ticket_price', nbins=20, 
                        title='Распределение цен билетов')
    st.plotly_chart(fig5, use_container_width=True)
    
    # Таблица бронирований
    st.subheader("Детали бронирований")
    st.dataframe(bookings_df, use_container_width=True)

with tab3:
    st.header("Информация об аэропортах")
    
    # Статистика по аэропортам
    airport_stats = pd.DataFrame({
        'Аэропорт': airports_df['airport_code'],
        'Название': airports_df['airport_name'],
        'Город': airports_df['city'],
        'Страна': airports_df['country']
    })
    
    st.dataframe(airport_stats, use_container_width=True)
    
    # Количество рейсов по аэропортам
    st.subheader("Количество рейсов по аэропортам")
    flights_by_airport = flights_df['departure'].value_counts().reset_index()
    flights_by_airport.columns = ['Аэропорт', 'Количество рейсов']
    fig6 = px.bar(flights_by_airport, x='Аэропорт', y='Количество рейсов', 
                  title='Количество рейсов по аэропортам вылета')
    st.plotly_chart(fig6, use_container_width=True)

with tab4:
    st.header("Информация о самолетах")
    
    # Статистика по самолетам
    aircraft_stats = pd.DataFrame({
        'Код': aircraft_df['aircraft_code'],
        'Тип': aircraft_df['aircraft_type'],
        'Вместимость': aircraft_df['capacity'],
        'Производитель': aircraft_df['manufacturer']
    })
    
    st.dataframe(aircraft_stats, use_container_width=True)
    
    # Использование самолетов
    st.subheader("Использование самолетов")
    aircraft_usage = flights_df['aircraft_id'].value_counts().reset_index()
    aircraft_usage.columns = ['Самолет', 'Количество рейсов']
    fig7 = px.pie(aircraft_usage, values='Количество рейсов', names='Самолет', 
                  title='Использование самолетов')
    st.plotly_chart(fig7, use_container_width=True)

# Футер
st.markdown("---")
st.markdown("**Данные обновлены:** " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
