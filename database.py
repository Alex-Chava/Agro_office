import logging
from sqlalchemy import and_, func
from datetime import datetime
from app import db
from models import Parameter, MixingParameter, Log, DensityRecord
import requests
import time

logger = logging.getLogger(__name__)
session = db.session

def get_parameter_value(parameter_name):
    """Возвращает значение параметра из таблицы Parameter по его имени."""
    try:
        param = session.query(Parameter).filter_by(controlled_parameter_name=parameter_name).first()
        if param is None:
            raise ValueError(f"Параметр '{parameter_name}' не найден в базе данных.")
        return param.value
    except Exception as e:
        logger.error(f"Ошибка при получении параметра {parameter_name}: {e}")
        raise

def update_parameter_value(parameter_name, value):
    """Обновляет значение параметра и дату в таблице Parameter."""
    try:
        param = session.query(Parameter).filter_by(controlled_parameter_name=parameter_name).first()
        if param is None:
            raise ValueError(f"Параметр '{parameter_name}' не найден в базе данных.")
        param.value = value
        param.value_date = datetime.utcnow()
        session.commit()
        logger.info(f"Параметр '{parameter_name}' обновлен до значения '{value}'.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении параметра {parameter_name}: {e}")
        session.rollback()
        raise

def get_mixing_parameters():
    """Возвращает параметры смешивания из таблицы MixingParameter."""
    try:
        mixing_params = session.query(MixingParameter).first()
        if mixing_params is None:
            raise ValueError("Параметры смешивания не найдены в базе данных.")
        return mixing_params
    except Exception as e:
        logger.error(f"Ошибка при получении параметров смешивания: {e}")
        raise

def insert_log_message(message, level="INFO"):
    """Вставляет сообщение в таблицу логов и отправляет его в Telegram."""
    try:
        log_entry = Log(message=message, level=level, timestamp=datetime.utcnow())
        session.add(log_entry)
        session.commit()
        logger.info(f"Лог записан: {message} с уровнем {level}.")
        # Отправляем сообщение в Telegram
        # if level == 'ERROR': send_telegram_message(message, level)
        send_telegram_message(message, level)
        # Проверка количества записей в таблице Log
        log_count = session.query(Log).count()
        if log_count > 150:
            # Удаляем 50 самых старых записей
            old_logs = session.query(Log).order_by(Log.timestamp.asc()).limit(50).all()
            for old_log in old_logs:
                session.delete(old_log)
            session.commit()
            logger.info("Удалено 50 самых старых записей из таблицы Log.")
    except Exception as e:
        logger.error(f"Ошибка при записи лога: {e}")
        session.rollback()
        raise

def send_telegram_message(message, level="INFO"):
    """Отправляет сообщение в группу Telegram через бота."""
    try:
        # Замените на токен вашего бота и ID вашей группы
        bot_token = '7748412244:AAEH6uAHKG4HR6p_DkrIwELdhsst65VBsMY'  # Замените на токен вашего бота
        chat_id = '-4611365228'  # Замените на ID вашей группы (с учетом знака минус)
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': f"[{level}] {message}",
            'parse_mode': 'HTML'
        }
        response = requests.post(send_text, data=params)
        if response.status_code == 200:
            logger.info("Сообщение успешно отправлено в Telegram.")
        else:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения в Telegram: {e}")

def insert_density_record(name, value):
    """Вставляет запись о плотности в таблицу DensityRecord."""
    try:
        density_record = DensityRecord(density_name=name, value=value, timestamp=datetime.utcnow())
        session.add(density_record)
        session.commit()
        logger.info(f"Записана плотность: {name}: {value}")
        # Проверяем общее количество записей в таблице DensityRecord
        log_count = session.query(DensityRecord).count()

        if log_count > 150:
            # Получаем 50 самых старых записей
            old_records = session.query(DensityRecord).order_by(DensityRecord.timestamp.asc()).limit(50).all()

            # Удаляем полученные старые записи
            for record in old_records:
                session.delete(record)

            # Применяем изменения к базе данных
            session.commit()

            # Логируем удаление старых записей
            logger.info("Удалено 50 самых старых записей из таблицы DensityRecord.")

    except Exception as e:
        logger.error(f"Ошибка при записи плотности: {e}")
        session.rollback()
        raise

def insert_buffer_capacity_record(bf_value):
    """Вставляет запись о буферности в таблицу DensityRecord."""
    try:
        density_record = DensityRecord(density_name='buffer_capacity', value=bf_value, timestamp=datetime.utcnow())
        session.add(density_record)
        session.commit()
        logger.info(f"Записана буферность: {bf_value}")
    except Exception as e:
        logger.error(f"Ошибка при записи буферности: {e}")
        session.rollback()
        raise
