Aviation ETL System
ETL-система для консолидации данных авиапредприятия.

## Структура проекта
`sources/` - Встроенные источники данных
`sql_schema/` - SQL-Схемs DWH
`scripts/` - ETL скрипты
`output/` - Результаты работы ETL 
`venv/` - Виртуальное окружение
`tests/` - тесты качества DWH, структуры, функций очистки 

## Установка
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
# Aviation ETL System 


