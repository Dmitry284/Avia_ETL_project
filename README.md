# Aviation ETL System

ETL-система для консолидации данных авиапредприятия.

## Структура проекта
`sources/` - Источники данных
`sql_schema/` - Схема DWH
`scripts/` - ETL скрипты
`output/` - Результаты работы
`docs/` - Документация

## Установка
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
cat > README.md << 'EOF'
# Aviation ETL System 

ETL-система для консолидации данных авиапредприятия. 

## Структура проекта 
`sources/` - Источники данных 
`sql_schema/` - Схема DWH                         
`scripts/` - ETL скрипты              
`output/` - Результаты работы 
`docs/` - Документация            
                      
## Установка 
python3 -m venv venv 
source venv/bin/activate 
pip install -r requirements.txt 
docker-compose up -d

