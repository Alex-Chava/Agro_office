import time
import logging
from regulation import Regulation
from database import get_parameter_value, insert_log_message, get_mixing_parameters
from app_instance import app  # Импортируем объект app из app_instance.py

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    with app.app_context():
        try:
            # Инициализация регулирования с параметрами из mixing_parameters
            regulation = Regulation()
            # max_relay_time = 5
            pump_status_old = 0

            # Основной цикл регулирования
            while True:
                try:
                    regulation.update_parameters()

                    # logger.info(f"Ожидание работы насосов в течение {max_relay_time} секунд.")
                    # time.sleep(max_relay_time)

                    # Получаем значения из базы данных
                    pump_status = get_parameter_value("перемешивание")  # Статус насоса из базы данных

                    # Список ключей для времени подачи компонентов
                    # ab_keys = [
                    #     "Время подачи А в бак",
                    #     "Время подачи В в бак",
                    #     "Время подачи К в бак"
                    # ]

                    # Считываем значения и преобразуем в int
                    # ab_values = [int(get_parameter_value(key) or 0) for key in ab_keys]

                    # Вычисляем максимальное значение /10
                    # max_relay_time = max(ab_values) / 10

                    # Логирование
                    # logger.info(f"Максимальное время среди насосов: {max_relay_time}")
                    logger.info(
                        f"перемешивание : {pump_status}"
                    )

                    if (pump_status == "1"):
                        logger.info("Условия выполнены. Начало процесса регулирования.")
                        if (pump_status_old == 0):
                            logger.info(f"Начало перемешивания, Ожидание стабилизации в течение {regulation.stabilization_time} секунд.")
                            time.sleep(regulation.stabilization_time)
                            pump_status_old = 1
                        pump_status = get_parameter_value("перемешивание")  # повторно смотрим Статус перемешивания из базы данных
                        if (pump_status == "1"): regulation.regulate()
                    else:
                        logger.info("Условия не выполнены. Регулирование не запускается.")
                        pump_status_old = 0

                except Exception as e:
                    logger.error(f"Ошибка в основном цикле: {e}")
                    insert_log_message(f"Ошибка в основном цикле: {e}", "ERROR")
                    time.sleep(5)  # Ожидание перед повторной попыткой
                time.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")
            insert_log_message(f"Ошибка при инициализации: {e}", "ERROR")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Процесс регулирования завершен.")
