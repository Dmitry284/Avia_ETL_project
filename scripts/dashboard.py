import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import json

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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("Aviation Analytics Dashboard")
st.markdown("---")

# Получаем подключение
engine = get_dwh_engine()

# Загрузка данных
@st.cache_data
def load_data():
    """Загружает данные из DWH с расшифровкой через JOIN"""
    
    # Рейсы с расшифровкой
    flights_query = """
    SELECT 
        ff.flight_instance_id,
        df.flight_number,
        da_dep.airport_code as departure,
        da_arr.airport_code as arrival,
        dd.full_date as flight_date,
        ds.status_code as status,
        ff.scheduled_departure_time as scheduled_departure,
        ff.scheduled_arrival_time as scheduled_arrival,
        ff.actual_departure_time as actual_departure,
        ff.actual_arrival_time as actual_arrival,
        ff.delay_minutes,
        dac.aircraft_code as aircraft_id
    FROM dwh.fact_flights ff
    JOIN dwh.dim_flights df ON ff.flight_id = df.flight_id
    JOIN dwh.dim_airports da_dep ON df.departure_airport_id = da_dep.airport_id
    JOIN dwh.dim_airports da_arr ON df.arrival_airport_id = da_arr.airport_id
    JOIN dwh.dim_dates dd ON ff.flight_date_id = dd.date_id
    JOIN dwh.dim_statuses ds ON ff.status_id = ds.status_id
    LEFT JOIN dwh.dim_aircraft dac ON df.aircraft_id = dac.aircraft_id
    ORDER BY dd.full_date, df.flight_number
    """
    flights_df = pd.read_sql(flights_query, engine)
    
    # Бронирования с расшифровкой
    bookings_query = """
    SELECT 
        fb.booking_id,
        fb.booking_ref,
        dp.passenger_name,
        df.flight_number,
        da_dep.airport_code as departure_airport,
        da_arr.airport_code as arrival_airport,
        dd.full_date as booking_date,
        ds.status_code as status,
        fb.ticket_price,
        fb.currency,
        dac.aircraft_code as aircraft_type
    FROM dwh.fact_bookings fb
    JOIN dwh.dim_passengers dp ON fb.passenger_id = dp.passenger_id
    JOIN dwh.dim_flights df ON fb.flight_id = df.flight_id
    JOIN dwh.dim_airports da_dep ON df.departure_airport_id = da_dep.airport_id
    JOIN dwh.dim_airports da_arr ON df.arrival_airport_id = da_arr.airport_id
    JOIN dwh.dim_dates dd ON fb.booking_date_id = dd.date_id
    JOIN dwh.dim_statuses ds ON fb.status_id = ds.status_id
    LEFT JOIN dwh.dim_aircraft dac ON df.aircraft_id = dac.aircraft_id
    ORDER BY dd.full_date DESC
    """
    bookings_df = pd.read_sql(bookings_query, engine)
    
    # Справочники
    airports_df = pd.read_sql("SELECT * FROM dwh.dim_airports ORDER BY airport_code", engine)
    aircraft_df = pd.read_sql("SELECT * FROM dwh.dim_aircraft ORDER BY aircraft_code", engine)
    
    return flights_df, bookings_df, airports_df, aircraft_df

flights_df, bookings_df, airports_df, aircraft_df = load_data()

@st.cache_data
def load_maintenance_data():
    query = """
    SELECT 
        fm.maintenance_id,
        da.aircraft_code,
        da.aircraft_type,
        dmt.type_code,
        dmt.type_name,
        ds.status_code,
        ds.status_name,
        fm.scheduled_date,
        fm.completed_date,
        fm.cost,
        fm.description
    FROM dwh.fact_maintenance fm
    JOIN dwh.dim_aircraft da ON fm.aircraft_id = da.aircraft_id
    JOIN dwh.dim_maintenance_types dmt ON fm.maintenance_type_id = dmt.maintenance_type_id
    JOIN dwh.dim_statuses ds ON fm.status_id = ds.status_id
    ORDER BY fm.scheduled_date DESC
    """
    return pd.read_sql(query, engine)

maint_df = load_maintenance_data()

# ========================================
# БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ
# ========================================
st.sidebar.header("Фильтры")

# Фильтр по аэропорту вылета
selected_departure = st.sidebar.multiselect(
    "Аэропорт вылета",
    options=sorted(bookings_df['departure_airport'].unique()),
    default=sorted(bookings_df['departure_airport'].unique())
)

# Фильтр по аэропорту прилёта
selected_arrival = st.sidebar.multiselect(
    "Аэропорт прилёта",
    options=sorted(bookings_df['arrival_airport'].unique()),
    default=sorted(bookings_df['arrival_airport'].unique())
)

# Фильтр по статусу
selected_status = st.sidebar.multiselect(
    "Статус бронирования",
    options=sorted(bookings_df['status'].unique()),
    default=sorted(bookings_df['status'].unique())
)

# Фильтр по типу самолёта
selected_aircraft = st.sidebar.multiselect(
    "Тип самолёта",
    options=sorted(bookings_df['aircraft_type'].dropna().unique()),
    default=sorted(bookings_df['aircraft_type'].dropna().unique())
)

# Фильтр по диапазону цен
min_price = float(bookings_df['ticket_price'].min())
max_price = float(bookings_df['ticket_price'].max())
price_range = st.sidebar.slider(
    "Диапазон цен (руб.)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price)
)

# Фильтр по дате
if 'booking_date' in bookings_df.columns and len(bookings_df) > 0:
    min_date = pd.to_datetime(bookings_df['booking_date']).min().date()
    max_date = pd.to_datetime(bookings_df['booking_date']).max().date()
    date_range = st.sidebar.date_input(
        "Диапазон дат бронирования",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Применяем фильтры
filtered_bookings = bookings_df[
    (bookings_df['departure_airport'].isin(selected_departure)) &
    (bookings_df['arrival_airport'].isin(selected_arrival)) &
    (bookings_df['status'].isin(selected_status)) &
    (bookings_df['ticket_price'] >= price_range[0]) &
    (bookings_df['ticket_price'] <= price_range[1])
]

if 'aircraft_type' in filtered_bookings.columns:
    filtered_bookings = filtered_bookings[
        (filtered_bookings['aircraft_type'].isin(selected_aircraft)) | 
        (filtered_bookings['aircraft_type'].isna())
    ]

# Фильтр по дате
if 'booking_date' in filtered_bookings.columns and len(filtered_bookings) > 0 and len(date_range) == 2:
    filtered_bookings = filtered_bookings[
        (pd.to_datetime(filtered_bookings['booking_date']).dt.date >= date_range[0]) &
        (pd.to_datetime(filtered_bookings['booking_date']).dt.date <= date_range[1])
    ]

# Показываем количество отфильтрованных записей
st.sidebar.markdown("---")
st.sidebar.info(f"Найдено бронирований: {len(filtered_bookings)} из {len(bookings_df)}")

# ========================================
# KPI МЕТРИКИ
# ========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Всего рейсов", len(flights_df))

with col2:
    st.metric("Всего бронирований", len(bookings_df))

with col3:
    total_revenue = bookings_df['ticket_price'].sum()
    st.metric("Общая выручка", f"{total_revenue:,.0f} руб.")

with col4:
    avg_price = bookings_df['ticket_price'].mean()
    st.metric("Средняя цена билета", f"{avg_price:,.0f} руб.")

st.markdown("---")

# ========================================
# ВКЛАДКИ
# ========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Рейсы", "Бронирования", "Аэропорты", "Самолеты", "Тех. обслуживание", "Статистика данных"
])

# ========================================
# ВКЛАДКА 1: РЕЙСЫ
# ========================================
with tab1:
    st.header("Анализ рейсов")
    
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
    
    st.subheader("Детали рейсов")
    st.dataframe(flights_df, use_container_width=True, hide_index=True)

# ========================================
# ВКЛАДКА 2: БРОНИРОВАНИЯ (С ФИЛЬТРАМИ)
# ========================================
with tab2:
    st.header("Анализ бронирований")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение статусов бронирований")
        booking_status = filtered_bookings['status'].value_counts().reset_index()
        booking_status.columns = ['Статус', 'Количество']
        fig3 = px.bar(booking_status, x='Статус', y='Количество', 
                      title='Статусы бронирований', color='Статус')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("Выручка по аэропортам вылета")
        revenue_by_airport = filtered_bookings.groupby('departure_airport')['ticket_price'].sum().reset_index()
        fig4 = px.bar(revenue_by_airport, x='departure_airport', y='ticket_price', 
                      title='Выручка по аэропортам вылета')
        st.plotly_chart(fig4, use_container_width=True)
    
    st.subheader("Распределение цен билетов")
    fig5 = px.histogram(filtered_bookings, x='ticket_price', nbins=20, 
                        title='Распределение цен билетов')
    st.plotly_chart(fig5, use_container_width=True)
    
    # НОВОЕ: Распределение цен по категориям
    st.subheader("Распределение цен по категориям")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**По аэропортам вылета**")
        price_by_dep = filtered_bookings.groupby('departure_airport')['ticket_price'].agg(['mean', 'median', 'count']).reset_index()
        price_by_dep.columns = ['Аэропорт', 'Средняя цена', 'Медианная цена', 'Количество']
        fig_dep = px.bar(price_by_dep, x='Аэропорт', y='Средняя цена',
                        title='Средняя цена по аэропортам вылета',
                        color='Средняя цена', color_continuous_scale='Blues')
        st.plotly_chart(fig_dep, use_container_width=True)
    
    with col2:
        st.markdown("**По типам самолётов**")
        price_by_aircraft = filtered_bookings.groupby('aircraft_type')['ticket_price'].agg(['mean', 'median', 'count']).reset_index()
        price_by_aircraft.columns = ['Тип самолёта', 'Средняя цена', 'Медианная цена', 'Количество']
        fig_ac = px.bar(price_by_aircraft, x='Тип самолёта', y='Средняя цена',
                       title='Средняя цена по типам самолётов',
                       color='Средняя цена', color_continuous_scale='Greens')
        st.plotly_chart(fig_ac, use_container_width=True)
    
    st.markdown("**По дням недели**")
    if 'booking_date' in filtered_bookings.columns and len(filtered_bookings) > 0:
        filtered_with_dow = filtered_bookings.copy()
        filtered_with_dow['day_of_week'] = pd.to_datetime(filtered_with_dow['booking_date']).dt.day_name()
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names_ru = {
            'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
            'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
        }
        
        price_by_day = filtered_with_dow.groupby('day_of_week')['ticket_price'].agg(['mean', 'count']).reset_index()
        price_by_day.columns = ['День недели', 'Средняя цена', 'Количество']
        price_by_day['День недели (RU)'] = price_by_day['День недели'].map(day_names_ru)
        price_by_day = price_by_day.sort_values('День недели', key=lambda x: x.map({v: i for i, v in enumerate(day_order)}))
        
        fig_day = px.bar(price_by_day, x='День недели (RU)', y='Средняя цена',
                        title='Средняя цена по дням недели',
                        color='Количество', color_continuous_scale='Oranges')
        st.plotly_chart(fig_day, use_container_width=True)
    
    st.subheader("Детали бронирований")
    st.dataframe(filtered_bookings, use_container_width=True, hide_index=True)

# ========================================
# ВКЛАДКА 3: АЭРОПОРТЫ
# ========================================
with tab3:
    st.header("Информация об аэропортах")
    
    airport_stats = pd.DataFrame({
        'Код': airports_df['airport_code'],
        'Название': airports_df['airport_name'],
        'Город': airports_df['city'],
        'Страна': airports_df['country']
    })
    
    st.dataframe(airport_stats, use_container_width=True, hide_index=True)
    
    st.subheader("Количество рейсов по аэропортам")
    flights_by_airport = flights_df['departure'].value_counts().reset_index()
    flights_by_airport.columns = ['Аэропорт', 'Количество рейсов']
    fig6 = px.bar(flights_by_airport, x='Аэропорт', y='Количество рейсов', 
                  title='Количество рейсов по аэропортам вылета')
    st.plotly_chart(fig6, use_container_width=True)

# ========================================
# ВКЛАДКА 4: САМОЛЁТЫ
# ========================================
with tab4:
    st.header("Информация о самолетах")
    
    aircraft_stats = pd.DataFrame({
        'Код': aircraft_df['aircraft_code'],
        'Тип': aircraft_df['aircraft_type'],
        'Вместимость': aircraft_df['capacity'],
        'Производитель': aircraft_df['manufacturer']
    })
    
    st.dataframe(aircraft_stats, use_container_width=True, hide_index=True)
    
    st.subheader("Использование самолетов")
    aircraft_usage = flights_df['aircraft_id'].value_counts().reset_index()
    aircraft_usage.columns = ['Самолет', 'Количество рейсов']
    fig7 = px.pie(aircraft_usage, values='Количество рейсов', names='Самолет', 
                  title='Использование самолетов')
    st.plotly_chart(fig7, use_container_width=True)

# ========================================
# ВКЛАДКА 5: ТЕХ. ОБСЛУЖИВАНИЕ
# ========================================
with tab5:
    st.header("Техническое обслуживание самолётов")
    
    # KPI метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего обслуживаний", len(maint_df))
    
    with col2:
        total_cost = maint_df['cost'].sum()
        st.metric("Общие расходы", f"{total_cost:,.0f} руб.")
    
    with col3:
        completed = len(maint_df[maint_df['status_code'] == 'completed'])
        st.metric("Завершено", completed)
    
    with col4:
        planned = len(maint_df[maint_df['status_code'] == 'planned'])
        st.metric("Запланировано", planned)
    
    st.markdown("---")
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение по типам обслуживания")
        type_counts = maint_df['type_name'].value_counts().reset_index()
        type_counts.columns = ['Тип', 'Количество']
        fig_type = px.pie(type_counts, values='Количество', names='Тип', 
                         title='Типы обслуживания')
        st.plotly_chart(fig_type, use_container_width=True)
    
    with col2:
        st.subheader("Распределение по статусам")
        status_counts = maint_df['status_name'].value_counts().reset_index()
        status_counts.columns = ['Статус', 'Количество']
        fig_status = px.bar(status_counts, x='Статус', y='Количество',
                           title='Статусы обслуживания', color='Статус')
        st.plotly_chart(fig_status, use_container_width=True)
    
    st.subheader("Расходы по типам обслуживания")
    cost_by_type = maint_df.groupby('type_name')['cost'].sum().reset_index()
    cost_by_type.columns = ['Тип', 'Расходы']
    fig_cost = px.bar(cost_by_type, x='Тип', y='Расходы',
                     title='Общие расходы по типам обслуживания')
    st.plotly_chart(fig_cost, use_container_width=True)
    
    st.subheader("Расходы по самолётам")
    cost_by_aircraft = maint_df.groupby('aircraft_code')['cost'].sum().reset_index()
    cost_by_aircraft.columns = ['Самолёт', 'Расходы']
    fig_aircraft = px.bar(cost_by_aircraft, x='Самолёт', y='Расходы',
                         title='Общие расходы по самолётам')
    st.plotly_chart(fig_aircraft, use_container_width=True)
    
    st.subheader("Детальная информация об обслуживании")
    st.dataframe(maint_df, use_container_width=True, hide_index=True)

# ========================================
# ВКЛАДКА 6: СТАТИСТИКА ДАННЫХ
# ========================================
with tab6:
    st.header("Статистика качества данных")
    
    # Загружаем отчёт о качестве
    quality_report_path = '../reports/quality_report.json'
    quality_report = None
    
    if os.path.exists(quality_report_path):
        with open(quality_report_path, 'r', encoding='utf-8') as f:
            quality_report = json.load(f)
        st.success(f"Отчёт о качестве загружен: {quality_report_path}")
    else:
        st.warning("Отчёт о качестве не найден. Запустите ETL пайплайн.")
    
    st.markdown("---")
    
    # БЛОК 1: Общая сводка
    st.subheader("Общая сводка по источникам")
    
    if quality_report:
        summary_data = []
        for report in quality_report:
            summary_data.append({
                'Источник': report['source'],
                'Строк до': report['initial_rows'],
                'Строк после': report['final_rows'],
                'Отброшено': report.get('rejected_rows', 0),
                'Дубликатов удалено': report.get('duplicates_removed', 0),
                'Полнота, %': f"{report.get('completeness_after', 0):.2f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # БЛОК 2: Статистика по бронированиям
    st.subheader("Статистика по бронированиям")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Описательная статистика цен**")
        
        price_stats = bookings_df['ticket_price'].describe()
        price_stats_df = pd.DataFrame({
            'Метрика': ['Количество', 'Среднее', 'Стандартное отклонение', 
                       'Минимум', '25%', 'Медиана (50%)', '75%', 'Максимум'],
            'Значение': [
                f"{price_stats['count']:.0f}",
                f"{price_stats['mean']:,.2f} руб.",
                f"{price_stats['std']:,.2f} руб.",
                f"{price_stats['min']:,.2f} руб.",
                f"{price_stats['25%']:,.2f} руб.",
                f"{price_stats['50%']:,.2f} руб.",
                f"{price_stats['75%']:,.2f} руб.",
                f"{price_stats['max']:,.2f} руб."
            ]
        })
        st.dataframe(price_stats_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Пропуски и выбросы**")
        
        null_counts = bookings_df.isnull().sum()
        null_df = pd.DataFrame({
            'Колонка': null_counts.index,
            'Пропусков': null_counts.values,
            'Процент': [f"{(v / len(bookings_df) * 100):.1f}%" for v in null_counts.values]
        })
        null_df = null_df[null_df['Пропусков'] > 0]
        
        if len(null_df) > 0:
            st.markdown("**Пропуски по колонкам:**")
            st.dataframe(null_df, use_container_width=True, hide_index=True)
        else:
            st.success("Пропусков не обнаружено")
        
        # Выбросы
        Q1 = bookings_df['ticket_price'].quantile(0.25)
        Q3 = bookings_df['ticket_price'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = bookings_df[
            (bookings_df['ticket_price'] < lower_bound) | 
            (bookings_df['ticket_price'] > upper_bound)
        ]
        
        st.markdown(f"**Границы выбросов (IQR метод):**")
        st.markdown(f"- Нижняя: {lower_bound:,.2f} руб.")
        st.markdown(f"- Верхняя: {upper_bound:,.2f} руб.")
        st.markdown(f"**Найдено выбросов:** {len(outliers)}")
        
        if len(outliers) > 0:
            st.dataframe(outliers[['booking_ref', 'passenger_name', 'ticket_price']], 
                        use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # БЛОК 3: Статистика по рейсам
    st.subheader("Статистика по рейсам")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Распределение статусов**")
        status_counts = flights_df['status'].value_counts().reset_index()
        status_counts.columns = ['Статус', 'Количество']
        status_counts['Процент'] = (status_counts['Количество'] / status_counts['Количество'].sum() * 100).round(1).astype(str) + '%'
        st.dataframe(status_counts, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Анализ задержек**")
        
        flights_with_delay = flights_df[
            (flights_df['actual_departure'].notna()) & 
            (flights_df['scheduled_departure'].notna())
        ].copy()
        
        if len(flights_with_delay) > 0:
            flights_with_delay['delay_minutes_calc'] = (
                pd.to_datetime(flights_with_delay['actual_departure']) - 
                pd.to_datetime(flights_with_delay['scheduled_departure'])
            ).dt.total_seconds() / 60
            
            avg_delay = flights_with_delay['delay_minutes_calc'].mean()
            max_delay = flights_with_delay['delay_minutes_calc'].max()
            delayed_count = len(flights_with_delay[flights_with_delay['delay_minutes_calc'] > 0])
            
            delay_stats = pd.DataFrame({
                'Метрика': ['Рейсов с данными', 'Средняя задержка', 
                           'Максимальная задержка', 'Рейсов с задержкой',
                           'Рейсов вовремя'],
                'Значение': [
                    f"{len(flights_with_delay)}",
                    f"{avg_delay:.1f} мин",
                    f"{max_delay:.1f} мин",
                    f"{delayed_count}",
                    f"{len(flights_with_delay) - delayed_count}"
                ]
            })
            st.dataframe(delay_stats, use_container_width=True, hide_index=True)
        else:
            st.info("Нет данных для анализа задержек")
    
    st.markdown("---")
    
    # БЛОК 4: Детальный отчёт
    st.subheader("Детальный отчёт о трансформациях")
    
    if quality_report:
        for report in quality_report:
            with st.expander(f"Источник: {report['source']}"):
                st.markdown(f"**Строк до обработки:** {report['initial_rows']}")
                st.markdown(f"**Строк после обработки:** {report['final_rows']}")
                st.markdown(f"**Отброшено строк:** {report.get('rejected_rows', 0)}")
                st.markdown(f"**Дубликатов удалено:** {report.get('duplicates_removed', 0)}")
                
                if 'fill_report' in report and report['fill_report']:
                    st.markdown("**Заполнение пропусков:**")
                    fill_data = []
                    for col, info in report['fill_report'].items():
                        fill_data.append({
                            'Колонка': col,
                            'Метод': info['method'],
                            'Значение': info['value'],
                            'Заполнено': info['filled']
                        })
                    st.dataframe(pd.DataFrame(fill_data), use_container_width=True, hide_index=True)
                
                if 'outliers_report' in report and report['outliers_report']:
                    st.markdown("**Выбросы:**")
                    outlier_data = []
                    for col, info in report['outliers_report'].items():
                        outlier_data.append({
                            'Колонка': col,
                            'Найдено': info['count'],
                            'Мин': f"{info['min']:.2f}" if info['min'] else '-',
                            'Макс': f"{info['max']:.2f}" if info['max'] else '-',
                            'Нижняя граница': f"{info['lower_bound']:.2f}",
                            'Верхняя граница': f"{info['upper_bound']:.2f}"
                        })
                    st.dataframe(pd.DataFrame(outlier_data), use_container_width=True, hide_index=True)

# Футер
st.markdown("---")
st.markdown("**Данные обновлены:** " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
