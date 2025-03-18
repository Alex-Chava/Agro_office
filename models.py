from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # Добавленный атрибут, по умолчанию 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Parameter(db.Model):
    __tablename__ = 'parameter'
    id = db.Column(db.Integer, primary_key=True)
    controlled_parameter_name = db.Column(db.String(64), index=True, unique=True)
    # Все остальные поля, включая те, что были в коде растворного узла
    scenario_belonging = db.Column(db.String(64))
    parameter_type = db.Column(db.String(64))
    operation_type = db.Column(db.String(64))
    device_type = db.Column(db.String(64))
    mode = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    port = db.Column(db.String(64))
    com = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    network_address = db.Column(db.String(64))
    register_type = db.Column(db.String(64))
    register_number = db.Column(db.String(64))
    acceptable_values = db.Column(db.String(128))
    register_name = db.Column(db.String(64))
    value = db.Column(db.String(64), default="0")
    value_date = db.Column(db.DateTime, default=datetime(2024, 8, 5, 0, 0))
    K = db.Column(db.Float, default=1.0)

    def __repr__(self):
        return f'<Parameter {self.controlled_parameter_name}>'
class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    time = db.Column(db.Time, nullable=False)
    parameter = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(64), nullable=False)
    result = db.Column(db.String(64))
    last_execution = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Scenario {self.type} {self.time} {self.parameter} {self.value}>'

class Tray(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shelf = db.Column(db.String(20), unique=True, nullable=False)
    action_date = db.Column(db.DateTime, default=datetime(2024, 8, 5, 0, 0))
    action = db.Column(db.String(50), nullable=False)
    plant_type = db.Column(db.String(50), nullable=False)
    growth_days = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Tray {self.shelf}>'

class Culture(db.Model):
    __tablename__ = 'cultures'

    culture_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Сроки пребывания в предварительных зонах
    sprouting_in_chamber_days = db.Column(db.Integer, nullable=False, default=0)  # Срок проращивания в камере, дней
    sprouting_on_shelf_days = db.Column(db.Integer, nullable=False, default=0)    # Срок проращивания на полке, дней
    seedling_days = db.Column(db.Integer, nullable=False, default=0)              # Срок в рассадном отделении, дней

    # Вместимость на полке
    pots_at_sprouting = db.Column(db.Integer, nullable=False, default=0)          # Количество на полке зоны проращивания
    pots_at_seedling = db.Column(db.Integer, nullable=False, default=0)           # Количество на полке рассадного отделения
    pots_at_main_stage = db.Column(db.Integer, nullable=False, default=0)         # Количество на полке основного этапа роста

    # Первичное созревание от посадки зерна
    min_days_from_planting = db.Column(db.Integer, nullable=False, default=0)     # Мин. срок созревания, дней
    min_weight_from_planting = db.Column(db.Float, nullable=False, default=0.0)   # Мин. масса одного растения, г
    max_days_from_planting = db.Column(db.Integer, nullable=False, default=0)     # Макс. срок созревания, дней
    max_weight_from_planting = db.Column(db.Float, nullable=False, default=0.0)   # Макс. масса одного растения, г

    # Повторное созревание после срезки
    min_days_from_cutting = db.Column(db.Integer, nullable=False, default=0)      # Мин. срок созревания, дней
    min_weight_from_cutting = db.Column(db.Float, nullable=False, default=0.0)    # Мин. масса одного растения, г
    max_days_from_cutting = db.Column(db.Integer, nullable=False, default=0)      # Макс. срок созревания, дней
    max_weight_from_cutting = db.Column(db.Float, nullable=False, default=0.0)    # Макс. масса одного растения, г

    def __repr__(self):
        return f'<Culture {self.name}>'

class MixingParameter(db.Model):
    __tablename__ = 'mixing_parameters'
    id = db.Column(db.Integer, primary_key=True)
    # Все поля, объединённые из двух версий
    tank_volume = db.Column(db.Float)
    density_a = db.Column(db.Float)
    density_b = db.Column(db.Float)
    density_acid = db.Column(db.Float)
    bf = db.Column(db.Float)
    pump_flow_rate = db.Column(db.Float)
    target_ec = db.Column(db.Float)
    target_ph = db.Column(db.Float)
    stabilization_time = db.Column(db.Integer)
    mixing_speed = db.Column(db.Integer)
    ec_deviation = db.Column(db.Float)
    ph_deviation = db.Column(db.Float)
    description = db.Column(db.Text)
    ec_rate_threshold = db.Column(db.Float, default=0.5)
    ph_rate_threshold = db.Column(db.Float, default=0.05)
    maxtime = db.Column(db.Integer)
    start_mix = db.Column(db.Integer, default=0)  # Новое поле для управления смешиванием

    def __repr__(self):
        return f'<MixingParameter id={self.id}>'

class Log(db.Model):
    __tablename__ = 'log'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(256))
    level = db.Column(db.String(16))
    timestamp = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Log id={self.id} level={self.level}>'

class DensityRecord(db.Model):
    __tablename__ = 'density_records'

    id = db.Column(db.Integer, primary_key=True)
    density_name = db.Column(db.String(64))
    value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

    def __repr__(self):
        return f'<DensityRecord id={self.id} parameter={self.parameter_name}>'

# Модель для таблицы 'plantings'
class Planting(db.Model):
    __tablename__ = 'plantings'  # Связываем с таблицей plantings

    tray_id = db.Column(db.Integer, primary_key=True)  # Идентификатор лотка (ключ)
    tray_name = db.Column(db.String(100), nullable=False)  # Имя лотка
    culture_id = db.Column(db.Integer, db.ForeignKey('cultures.culture_id'), nullable=True)  # Идентификатор культуры
    pots_planted = db.Column(db.Integer, nullable=True)  # Количество посаженных горшков
    sprouting_date = db.Column(db.Date, nullable=True)  # Дата начала проращивания
    harvest_date = db.Column(db.Date, nullable=True)  # Дата срезки
    previous_harvest_date = db.Column(db.Date, nullable=True)  # Дата предыдущей срезки
    growth_stage = db.Column(db.String(50), nullable=False)  # стадия роста

    # Связь с таблицей культур (обратная связь)
    culture = db.relationship('Culture', backref='plantings')  # Создаем связь с таблицей 'cultures'