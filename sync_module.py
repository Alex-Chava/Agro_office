# sync_module.py

import time
import logging
from datetime import datetime, timedelta, date
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker
from models import Parameter, Scenario, Log  # DensityRecord удалён
import minimalmodbus
import requests
from app import db
from app_instance import app

session = db.session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный словарь для отслеживания отсутствия связи по устройствам.
# Ключ: device_name; значение: {'start': datetime, 'last_sent': datetime}
offline_counters = {}

# Глобальный словарь для уведомлений о низком уровне для определённых параметров.
# Ключ: параметр.id; значение: время последнего отправленного уведомления.
low_level_notifications = {}

# Перечень параметров для уведомлений при низком уровне (из 1 в 0)
low_level_params = ["уровень БАК минимум", "уровень А мин", "уровень В мин", "уровень К мин"]

# Перечень параметров, за изменением которых нужно отправлять уведомления.
monitored_params = {"полка 1", "полка 2", "полка 3", "полка 4", "перемешивание",
                    "Канал красного света", "Канал белого света"}

# Словари для хранения предыдущих значений (используются в poll_parameters).
previous_db_values = {}
previous_device_values = {}

# Словарь для хранения клиентов Modbus по устройствам.
modbus_clients = {}

def insert_log_message(message, level="INFO"):
    """
    Вставляет сообщение в таблицу логов и отправляет его в Telegram.
    Сообщение отправляется с указанным уровнем (например, "INFO" или "ERROR").
    """
    try:
        log_entry = Log(message=message, level=level, timestamp=datetime.now())
        session.add(log_entry)
        session.commit()
        # Отправляем сообщение в Telegram через insert_log_message,
        # что обеспечивает единообразное логирование и уведомление.
        # Формат: [LEVEL] сообщение
        bot_message = f"[{level}] {message}"
        # Здесь можно установить разные уровни отправки (например, только для ERROR или INFO)
        # В данном примере отправляем все.
        send_telegram_message(bot_message)
    except Exception as e:
        logger.error(f"Ошибка при записи лога: {e}")
        session.rollback()

def send_telegram_message(message):
    """Отправляет сообщение в Telegram через бота."""
    try:
        bot_token = '7748412244:AAEH6uAHKG4HR6p_DkrIwELdhsst65VBsMY'
        chat_id = '-4611365228'
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(send_text, data=params)
        if response.status_code == 200:
            logger.info("Сообщение успешно отправлено в Telegram.")
        else:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения в Telegram: {e}")

def setup_modbus_client(param):
    mode = param.mode
    network_address = int(param.network_address)
    device_type = param.device_type
    device_name = f"{device_type}_addr{network_address}"

    if mode == "com":
        com_port = str(param.com)
        speed = int(param.speed)
        instrument = minimalmodbus.Instrument(com_port, network_address)
        instrument.serial.baudrate = speed
        instrument.serial.bytesize = 8
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 0.1  # Тайм-аут 0.1 сек для COM-порта
        instrument.mode = minimalmodbus.MODE_RTU
        # Устанавливаем обработку локального эха
        instrument.handle_local_echo = True

    elif mode == "tcp":
        ip_address = param.ip_address
        port = int(param.port)
        instrument = minimalmodbus.Instrument(ip_address, network_address, mode=minimalmodbus.MODE_TCP)
        instrument.serial.timeout = 1
    else:
        raise ValueError(f"Неподдерживаемый режим подключения: {mode}")

    return instrument

def execute_scenarios():
    """
    Выполняет сценарии из таблицы Scenario.
    Для каждого сценария обновляется значение параметра в БД, при этом value_date
    записывается с секундами и микросекундами, обнулёнными (например, 07:07:00.000000).
    Затем отправляется сообщение вида:
    "Изменение по сценарию параметра <имя> в положение <новое значение>. Уровень PH: <PH>, Уровень EC: <EC>"
    """
    try:
        current_date = date.today()
        current_time = datetime.now().time()
        scenarios = session.query(Scenario).filter(
            and_(
                Scenario.time <= current_time,
                (Scenario.last_execution == None) | (func.date(Scenario.last_execution) < current_date)
            )
        ).order_by(Scenario.time, Scenario.id).all()

        for scenario in scenarios:
            param = session.query(Parameter).filter_by(controlled_parameter_name=scenario.parameter).first()
            if not param:
                logger.error(f"Параметр {scenario.parameter} не найден.")
                continue

            # Обновляем значение по сценарию
            previous_value = param.value
            param.value = scenario.value
            # Записываем время с обнулёнными секундами и микросекундами
            scenario_time = datetime.now().replace(second=0, microsecond=0)
            param.value_date = scenario_time
            session.commit()

            # Получаем текущие значения PH и EC из БД
            ph_param = session.query(Parameter).filter_by(controlled_parameter_name="Уровень PH").first()
            ec_param = session.query(Parameter).filter_by(controlled_parameter_name="Уровень EC").first()
            current_ph = ph_param.value if ph_param else "неизвестно"
            current_ec = ec_param.value if ec_param else "неизвестно"

            scenario_message = (
                f"Изменение по сценарию параметра {param.controlled_parameter_name} в положение {scenario.value}. "
                f"Уровень PH: {current_ph}, Уровень EC: {current_ec}"
            )
            scenario.result = f"Значение {scenario.value} записано в параметр {param.controlled_parameter_name}"
            scenario.last_execution = datetime.now()
            session.commit()
            insert_log_message(scenario_message, level="INFO")
    except Exception as e:
        logger.error(f"Ошибка при выполнении сценариев: {e}")
        session.rollback()

def read_registers_batch(group):
    """
    Читает пакет регистров из устройства по одной попытке.
    Если чтение не удалось, обновляет offline-счётчик для устройства, удаляет клиента,
    и возвращает None.
    """
    global modbus_clients, offline_counters
    parameters = group['parameters']
    device_name = group['device_name']
    register_type = group['register_type']
    start_address = group['start_address']
    count = group['count']
    logger.info(f"Получили группу {group}")
    param_example = parameters[0]
    client_key = device_name
    if client_key not in modbus_clients:
        try:
            modbus_clients[client_key] = setup_modbus_client(param_example)
        except Exception as e:
            logger.error(f"Ошибка настройки клиента для {device_name}: {e}")
            update_offline_counter(device_name)
            return None
    client = modbus_clients[client_key]

    try:
        if register_type == '1':  # Coils
            values = client.read_bits(start_address, count, functioncode=1)
        elif register_type == '2':  # Discrete Inputs
            values = client.read_bits(start_address, count, functioncode=2)
        elif register_type == '3':  # Holding Registers
            values = client.read_registers(start_address, count, functioncode=3)
        elif register_type == '4':  # Input Registers
            values = client.read_registers(start_address, count, functioncode=4)
        else:
            logger.error(f"Неизвестный тип регистра: {register_type}")
            return None

        if values is None:
            raise Exception("Получены пустые данные при чтении регистров.")
        logger.error(f"Результат при чтении регистров с устройства {device_name}: {values}")
        reset_offline_counter(device_name)
        result_values = []
        for i, param in enumerate(parameters):
            K = float(param.K) if param.K else 1.0
            value = values[i]
            if K != 1.0:
                value = value / K
            result_values.append(value)
        return result_values

    except Exception as e:
        logger.error(f"Ошибка при чтении регистров с устройства {device_name}: {e}")
        if device_name in modbus_clients:
            del modbus_clients[device_name]
        update_offline_counter(device_name)
        return None

def update_offline_counter(device_name):
    """Обновляет счётчик отсутствия связи для устройства."""
    global offline_counters
    now = datetime.now()
    counter = offline_counters.get(device_name)
    if counter is None:
        offline_counters[device_name] = {'start': now, 'last_sent': None}
    else:
        if (now - counter['start']).total_seconds() >= 60:
            if counter['last_sent'] is None or (now - counter['last_sent']).total_seconds() >= 300:
                insert_log_message(f"Отсутствует связь с устройством {device_name}", level="ERROR")
                offline_counters[device_name]['last_sent'] = now

def reset_offline_counter(device_name):
    global offline_counters
    if device_name in offline_counters:
        del offline_counters[device_name]

def write_parameter_value(param, value_to_write=None):
    """
    Пишет значение в параметр устройства Modbus (одна попытка).
    При ошибке обновляет offline-счётчик.
    """
    global modbus_clients, offline_counters
    device_name = f"{param.device_type}_addr{param.network_address}"
    if param.mode == 'com':
        communication_params = f"COM{param.com}"
    else:
        communication_params = f"IP{param.ip_address}"
    client_key = device_name
    if client_key not in modbus_clients:
        try:
            modbus_clients[client_key] = setup_modbus_client(param)
        except Exception as e:
            logger.error(f"Ошибка настройки клиента для записи {device_name}: {e}")
            update_offline_counter(device_name)
            return False
    client = modbus_clients[client_key]

    try:
        register_address = int(param.register_number)
        register_type = param.register_type
        K = float(param.K) if param.K else 1.0
        if value_to_write is None:
            value_to_write = param.value
        value = float(value_to_write) * K if K != 1.0 else float(value_to_write)
        if register_type == '1':
            client.write_bit(register_address, int(value), functioncode=5)
        elif register_type == '3':
            client.write_register(register_address, int(value), functioncode=6)
        else:
            logger.error(f"Запись в регистры типа {register_type} не поддерживается.")
            return False
        logger.info(f"Записано значение {value} в параметр {param.controlled_parameter_name}")
        reset_offline_counter(device_name)
        return True
    except Exception as e:
        logger.error(f"Ошибка при записи параметра {param.controlled_parameter_name}: {e}")
        update_offline_counter(device_name)
        return False

def poll_parameters():
    """
    Опрос параметров устройств и синхронизация с базой.
    Если изменение вызвано не сценарием (то есть изменение через ВЕБ),
    отправляется уведомление вида:
    "Изменение с ВЕБ интерфейса параметра <имя> в положение <новое значение>. Уровень PH: <PH>, Уровень EC: <EC>"
    Уведомление не отправляется, если время обновления имеет секунды и микросекунды, равные 0 (то есть изменение было по сценарию).
    Для каждого параметра уведомление отправляется не чаще 1 раза в минуту.
    """
    global previous_db_values, previous_device_values, low_level_notifications, monitored_params

    # Словарь для уведомлений, связанных с ВЕБ изменениями (не чаще 1 раза в минуту)
    web_notifications = {}
    try:
        all_parameters = session.query(Parameter).all()
        # Словарь для быстрого доступа по имени
        params_dict = {p.controlled_parameter_name: p for p in all_parameters}
        current_ph = params_dict.get("Уровень PH").value if params_dict.get("Уровень PH") else None
        current_ec = params_dict.get("Уровень EC").value if params_dict.get("Уровень EC") else None

        offline_devices = set()
        parameters = [p for p in all_parameters if p.mode in ("com", "tcp")]
        grouped_params = group_parameters(parameters)
        for group in grouped_params:
            device_name = group['device_name']
            if device_name in offline_devices:
                continue
            values = read_registers_batch(group)
            if values is None:
                offline_devices.add(device_name)
                continue
            parameters_in_group = group['parameters']
            for i, param in enumerate(parameters_in_group):
                value = values[i]
                operation_type = param.operation_type
                current_db_value = str(param.value) if param.value is not None else None
                device_value = str(value) if value is not None else None

                # Если изменение вызвано только чтением – обновляем базу
                if operation_type == 'чтение':
                    param.value = str(value)
                    param.value_date = datetime.now()
                else:
                    previous_db_value = previous_db_values.get(param.id)
                    previous_device_value = previous_device_values.get(param.id)
                    db_changed = current_db_value != previous_db_value
                    device_changed = device_value != previous_device_value

                    # Если изменение обнаружено в БД (из ВЕБ)
                    if db_changed:
                        success = write_parameter_value(param)
                        if success:
                            previous_db_values[param.id] = current_db_value
                            previous_device_values[param.id] = current_db_value
                            # Если параметр отслеживается и время обновления не имеет обнулённых секунд (то есть не сценарий)
                            if param.controlled_parameter_name in monitored_params:
                                if not (param.value_date and param.value_date.second == 0 and param.value_date.microsecond == 0):
                                    now = datetime.now()
                                    last_sent = web_notifications.get(param.id)
                                    if last_sent is None or (now - last_sent).total_seconds() >= 60:
                                        insert_log_message(
                                            f"Изменение с ВЕБ интерфейса параметра {param.controlled_parameter_name} в положение {current_db_value}. "
                                            f"Уровень PH: {current_ph}, Уровень EC: {current_ec}",
                                            level="INFO"
                                        )
                                        web_notifications[param.id] = now
                    # Если изменение обнаружено только на устройстве
                    elif not db_changed and device_changed:
                        param.value = device_value
                        param.value_date = datetime.now()
                        previous_db_values[param.id] = device_value
                        previous_device_values[param.id] = device_value
                        if param.controlled_parameter_name in monitored_params:
                            if not (param.value_date and param.value_date.second == 0 and param.value_date.microsecond == 0):
                                now = datetime.now()
                                last_sent = web_notifications.get(param.id)
                                if last_sent is None or (now - last_sent).total_seconds() >= 60:
                                    insert_log_message(
                                        f"Изменение с ВЕБ интерфейса параметра {param.controlled_parameter_name} в положение {device_value}. "
                                        f"Уровень PH: {current_ph}, Уровень EC: {current_ec}",
                                        level="INFO"
                                    )
                                    web_notifications[param.id] = now
                    # Если ни изменение БД, ни изменение на устройстве – ничего не делаем
                logger.info(f"сейчас нюхаем: {param.controlled_parameter_name}")

                # Обработка уведомлений для параметров низкого уровня
                if param.controlled_parameter_name in low_level_params:
                    logger.info(f"Низкий уровень: {param.controlled_parameter_name}")
                    if current_db_value == "0":
                        last_sent = low_level_notifications.get(param.id)
                        now = datetime.now()
                        if last_sent is None or (now - last_sent).total_seconds() >= 300:
                            insert_log_message(
                                f"Низкий уровень, необходимо добавить: {param.controlled_parameter_name}",
                                level="WARNING"
                            )
                            low_level_notifications[param.id] = now
                    else:
                        if param.id in low_level_notifications:
                            del low_level_notifications[param.id]

        session.commit()
    except Exception as e:
        logger.error(f"Ошибка при опросе параметров: {e}")
        session.rollback()

def group_parameters(parameters):
    grouped = []
    sorted_params = sorted(parameters, key=lambda p: (
        p.device_type,
        p.network_address,
        p.mode,
        p.com if p.mode == 'com' else p.ip_address,
        p.register_type,
        int(p.register_number)
    ))
    group = {}
    prev_param = None
    for param in sorted_params:
        device_name = f"{param.device_type}_addr{param.network_address}"
        register_numbers = [param.register_number]
        communication_channel = param.mode
        if param.mode == 'com':
            communication_params = f"COM{param.com}"
        else:
            communication_params = f"IP{param.ip_address}"
        register_type = param.register_type
        address = int(param.register_number)
        if prev_param is None:
            group = {
                'device_name': device_name,
                'communication_channel': communication_channel,
                'communication_params': communication_params,
                'register_numbers': register_numbers,
                'register_type': register_type,
                'start_address': address,
                'count': 1,
                'parameters': [param]
            }
        else:
            if (device_name == group['device_name'] and
                communication_channel == group['communication_channel'] and
                communication_params == group['communication_params'] and
                register_type == group['register_type'] and
                address == group['start_address'] + group['count']):
                group['count'] += 1
                group['parameters'].append(param)
                group['register_numbers'].append(param.register_number)
            else:
                grouped.append(group)
                group = {
                    'device_name': device_name,
                    'communication_channel': communication_channel,
                    'communication_params': communication_params,
                    'register_numbers': register_numbers,
                    'register_type': register_type,
                    'start_address': address,
                    'count': 1,
                    'parameters': [param]
                }
        prev_param = param
    if group:
        grouped.append(group)
    return grouped

def run_sync_module():
    """Запуск модуля синхронизации."""
    with app.app_context():
        while True:
            try:
                execute_scenarios()  # Выполнение сценариев перед опросом параметров
                poll_parameters()    # Опрос параметров и синхронизация
            except Exception as e:
                logger.error(f"Ошибка в цикле синхронизации: {e}")
                logger.exception("Детали исключения:")
                session.rollback()
            finally:
                time.sleep(1)

if __name__ == "__main__":
    with app.app_context():
        try:
            run_sync_module()
        except KeyboardInterrupt:
            logger.info("Модуль синхронизации остановлен пользователем.")
        finally:
            session.close()
