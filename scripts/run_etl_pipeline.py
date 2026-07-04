import subprocess
import sys
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../output/logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Запускает Python скрипт"""
    logger.info(f"Запуск скрипта: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Скрипт {script_name} завершен успешно")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении {script_name}: {e.stderr}")
        return False

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("НАЧАЛО ETL ПАЙПЛАЙНА")
    logger.info("=" * 80)
    
    scripts = [
        '01_extract.py',
        '02_transform.py',
        '03_load.py'
    ]
    
    for script in scripts:
        if not run_script(script):
            logger.error(f"Пайплайн прерван на скрипте {script}")
            sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("ETL ПАЙПЛАЙН ЗАВЕРШЕН УСПЕШНО")
    logger.info("=" * 80)
    logger.info("Запуск тестов качества данных...")
    try:
        result = subprocess.run(
            ['pytest', '../tests/test_data_quality.py', '-v'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Тесты качества данных пройдены успешно")
    except subprocess.CalledProcessError as e:
        logger.error(f"Тесты качества данных не пройдены: {e.stdout}")
        logger.warning("Пайплайн завершен с предупреждениями")
