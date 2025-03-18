import time
import logging
from database import (
    get_parameter_value,
    update_parameter_value,
    get_mixing_parameters,
    insert_log_message,
    insert_density_record,
    insert_buffer_capacity_record
)

logger = logging.getLogger(__name__)

class Regulation:
    def __init__(self):
        self.previous_ec = None
        self.previous_ph = None
        self.expected_ec_change = None
        self.expected_ph_change = None


    def update_parameters(self):
        mixing_params = get_mixing_parameters()

        # Инициализируем параметры из mixing_parameters
        self.tank_volume = mixing_params.tank_volume
        self.density_a = mixing_params.density_a
        self.density_b = mixing_params.density_b
        self.density_acid = mixing_params.density_acid
        self.bf = mixing_params.bf  # Буферность раствора
        self.pump_flow_rate = mixing_params.pump_flow_rate
        self.target_ec = mixing_params.target_ec
        self.target_ph = mixing_params.target_ph
        self.stabilization_time = mixing_params.stabilization_time
        self.mixing_speed = mixing_params.mixing_speed / 100  # Процент от полного времени
        self.max_ec_deviation = mixing_params.ec_deviation
        self.max_ph_deviation = mixing_params.ph_deviation
        self.maxtime = mixing_params.maxtime
        self.start_mix = mixing_params.start_mix  # Новое поле

    """===================================================================================================================================================================================="""
    def regulate(self):
        """Основной метод для запуска цикла регулирования"""
        logger.info("[Начало процесса регулирования]")
        current_ec = get_parameter_value("Уровень EC") # Считывание текущих значений EC из базы данных
        current_ph = get_parameter_value("Уровень PH") # Считывание текущих значений pH из базы данных
        logger.info(f"Текущий уровень EC: {current_ec}")
        logger.info(f"Текущий уровень PH: {current_ph}")
        if current_ec is None or current_ph is None: # если что-то не удалось считать успешно - печалимся!!!
            logger.error("Не удалось получить значения EC или pH из базы данных.")
            insert_log_message("Не удалось получить значения EC или pH из базы данных.", "ERROR")
            return
        self.regulate_ec(float(current_ec)) # Проверяем и регулируем EC
        self.regulate_ph(float(current_ph)) # Проверяем и регулируем pH

        # Ждем, пока завершатся операции насосов.
        # Получаем время работы каждого насоса (значения в базе – в десятых долях секунды)
        pump_time_a = int(get_parameter_value("Время подачи А в бак") or 0) / 10
        pump_time_b = int(get_parameter_value("Время подачи В в бак") or 0) / 10
        pump_time_k = int(get_parameter_value("Время подачи К в бак") or 0) / 10
        max_pump_time = max(pump_time_a, pump_time_b, pump_time_k)
        logger.info(f"Ожидание завершения работы насосов в течение {max_pump_time} секунд.")
        time.sleep(max_pump_time)

        # После запуска насосов ожидаем, пока они завершат работу, затем ждем стабилизации
        logger.info(f"Ожидание работы насосов и стабилизации в течение {self.stabilization_time} секунд.")
        time.sleep(self.stabilization_time)

        if self.expected_ec_change is not None:
            self.calculate_actual_density(float(get_parameter_value("Уровень EC")))
        if self.expected_ph_change is not None:
            self.calculate_actual_buffer_capacity(float(get_parameter_value("Уровень PH")))



    """===================================================================================================================================================================================="""
    """Проверка и регулирование EC."""
    def regulate_ec(self, current_ec):
        logger.info("=== Регулирование EC === === Регулирование EC === === Регулирование EC ===")
        logger.info(f"Объем бака (л): {self.tank_volume}")
        logger.info(f"Время стабилизации (сек): {self.stabilization_time}")
        logger.info(f"Скорость смешивания (%): {self.mixing_speed * 100}")
        logger.info(f"Максимальное время работы насосов (maxtime): {self.maxtime} секунд")
        logger.info(f"Мощность насосов (мл/мин): {self.pump_flow_rate}")
        logger.info(f"Плотность компонента A (г/л): {self.density_a}")
        logger.info(f"Плотность компонента B (г/л): {self.density_b}")
        logger.info(f"Целевое значение EC: {self.target_ec}")
        logger.info(f"Максимальное отклонение EC: {self.max_ec_deviation}")
        logger.info(f"Текущий уровень EC: {current_ec}")

        delta_ec = round(self.target_ec - current_ec, 3) # Считаем текущую разницу по ЕС

        if delta_ec > self.max_ec_deviation: # Если разница по ЕС больше установленного припуска - работаем!
            t_ec_full = self.calculate_pump_time_for_ec(delta_ec) # Рассчитываем полное время работы насоса
            t_ec_work = t_ec_full * self.mixing_speed # Рассчитываем время работы насоса с учетом заданной скорости
            relay_time_units = int(min(t_ec_work, self.maxtime)) # Выбираем минимальное время между расчетным и максимальным
            update_parameter_value("Время подачи А в бак", str(relay_time_units * 10)) # включаем насосы на заданное время
            update_parameter_value("Время подачи В в бак", str(relay_time_units * 10)) # включаем насосы на заданное время
            self.expected_ec_change = round(delta_ec * relay_time_units / t_ec_full,3) # Сохраняем ожидаемое изменение ЕС
            self.previous_ec = current_ec  # Сохраняем текущее значение EC как previous_ec
            logger.info(f"Реле 'Подача АВ в бак' включено на {relay_time_units} секунд.")
            insert_log_message(f"Реле 'Подача АВ в бак' включено на {relay_time_units} секунд.")
        else:
            logger.info("EC в пределах допустимого отклонения.")
            # insert_log_message("EC в пределах допустимого отклонения.")

    """Рассчитывает время работы насосов для изменения значения EC."""
    def calculate_pump_time_for_ec(self, delta):
        required_volume = round(1000*(delta * self.tank_volume) / (self.density_a + self.density_b),0)  # Объем раствора, который нужно добавить
        combined_pump_flow_rate = self.pump_flow_rate * 2 / 1000  # Общая мощность двух насосов в литрах/мин
        pump_time = round((required_volume / (1000 * combined_pump_flow_rate)) * 60, 0)  # Время работы в секундах
        logger.info(f"Изменение EC (delta): {delta}, Требуемый объем (мл): {required_volume}, Время работы насосов (сек): {pump_time}") # Логирование расчетов
        insert_log_message(f"Изменение EC (delta): {delta}, Требуемый объем (мл): {required_volume}, Время работы насосов (сек): {pump_time}") # Логирование расчетов
        return pump_time

    """Рассчитывает фактическую плотность компонентов после завершения работы насосов."""
    def calculate_actual_density(self, current_ec):
        actual_delta_ec = current_ec - self.previous_ec # Фактическое изменение EC
        if actual_delta_ec != 0:
            actual_density = round((self.density_a + self.density_b) * actual_delta_ec / self.expected_ec_change, 0) # Рассчитываем фактическую плотность
        else:
            actual_density = 0 # Фактическая плотность при отсутствии изменений
        effect_ec = round(actual_delta_ec / self.expected_ec_change, 1) * 100
        insert_density_record("actual_density", actual_density) # Фактическое изменение EC записали в БД
        logger.info(f"Ожидаемое изменение EC: {self.expected_ec_change}\nФактическое изменение EC: {actual_delta_ec}\nФактическая плотность компонентов: {actual_density}")
        insert_log_message(
            f"Ожидаемое изменение EC: {self.expected_ec_change}\nФактическое изменение EC: {actual_delta_ec}\nФактическая плотность компонентов: {actual_density}")
        if effect_ec < 50: insert_log_message(f"Регулирование EC не эффективно. Эффект: {effect_ec}%", "ERROR")
        self.expected_ec_change = None
        self.previous_ec = None

    """===================================================================================================================================================================================="""
    """Проверка и регулирование pH."""
    def regulate_ph(self, current_ph):
        logger.info("=== Регулирование pH === === Регулирование pH === === Регулирование pH ===")
        logger.info(f"Объем бака (л): {self.tank_volume}")
        logger.info(f"Время стабилизации (сек): {self.stabilization_time}")
        logger.info(f"Скорость смешивания (%): {self.mixing_speed * 100}")
        logger.info(f"Максимальное время работы насосов (maxtime): {self.maxtime} секунд")
        logger.info(f"Мощность насосов (мл/мин): {self.pump_flow_rate}")
        logger.info(f"Плотность кислоты (г/л): {self.density_acid}")
        logger.info(f"Буферность раствора (BF): {self.bf}")
        logger.info(f"Целевое значение pH: {self.target_ph}")
        logger.info(f"Максимальное отклонение pH: {self.max_ph_deviation}")
        logger.info(f"Текущий уровень PH: {current_ph}")

        delta_ph = round(current_ph - self.target_ph, 3) # считаем дельту ph на текущий момент

        if delta_ph > self.max_ph_deviation:
            t_ph_full = self.calculate_pump_time_for_ph(delta_ph) # Рассчитываем время работы насоса
            t_ph_work = t_ph_full * self.mixing_speed # Рассчитываем время работы насоса с учетом заданной скорости
            relay_time_units = int(min(t_ph_work, self.maxtime)) # Выбираем минимальное время между расчетным и максимальным
            update_parameter_value("Время подачи К в бак", str(relay_time_units * 10)) # Обновляем параметры в базе данных
            self.expected_ph_change =  round(delta_ph * relay_time_units / t_ph_full,3) # Сохраняем ожидаемое изменение
            self.previous_ph = current_ph
            logger.info(f"Реле 'Подача кислоты в бак' включено на {relay_time_units} секунд.")
            insert_log_message(f"Реле 'Подача кислоты в бак' включено на {relay_time_units} секунд.")
        else:
            logger.info("pH в пределах допустимого отклонения.")
            # insert_log_message("pH в пределах допустимого отклонения.")

    """Рассчитывает время работы насоса для изменения pH."""
    def calculate_pump_time_for_ph(self, delta_ph):
        required_volume = round((delta_ph * self.bf * self.tank_volume) / 1000,0)  # Требуемый объем кислоты в литрах
        pump_flow_rate_l_min = self.pump_flow_rate / 1000  # Мощность насоса в л/мин
        pump_time = round((required_volume / (1000 * pump_flow_rate_l_min)) * 60, 0)  # Время работы насоса в секундах
        logger.info(f"Изменение pH (delta): {delta_ph}, Требуемый объем кислоты (л): {required_volume}, Время работы насоса (сек): {pump_time}")
        insert_log_message(f"Изменение pH (delta): {delta_ph}\nТребуемый объем кислоты (мл): {required_volume}\nВремя работы насоса (сек): {pump_time}")
        return pump_time

    """Рассчитывает фактическую буферность после завершения работы насоса кислоты."""
    def calculate_actual_buffer_capacity(self, current_ph):
        actual_delta_ph = self.previous_ph - current_ph # Фактическое изменение pH
        if actual_delta_ph != 0:
            actual_bf = round((self.bf * self.expected_ph_change) / actual_delta_ph, 0)  # Рассчитываем фактическую буферность actual_delta_ph
        else:
            actual_bf = 999999 # Фактическая плотность при отсутствии изменений
        effect_ph = round(actual_delta_ph / self.expected_ph_change, 1)*100
        insert_buffer_capacity_record(actual_bf)
        logger.info(f"Ожидаемое изменение pH: {self.expected_ph_change}, Фактическое изменение pH: {actual_delta_ph}, Фактическая буферность: {actual_bf}")
        insert_log_message(f"Ожидаемое изменение pH: {self.expected_ph_change}, Фактическое изменение pH: {actual_delta_ph}, Фактическая буферность: {actual_bf}")
        if effect_ph < 50 : insert_log_message(f"Регулирование pH не эффективно. Эффект: {effect_ph}%", "ERROR")
        self.expected_ph_change = None
        self.previous_ph = None