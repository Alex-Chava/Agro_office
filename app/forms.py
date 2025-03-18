from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, NumberRange
from wtforms import StringField, IntegerField, FloatField, DateField, SelectField, SubmitField, PasswordField, BooleanField

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Sign In')

# Форма для добавления новой культуры
class CultureForm(FlaskForm):
    name = StringField('Название культуры', validators=[DataRequired()])
    sprouting_in_chamber_days = IntegerField('Проращивание в камере (дней)', validators=[DataRequired()])
    sprouting_on_shelf_days = IntegerField('Проращивание на полке (дней)', validators=[DataRequired()])
    seedling_days = IntegerField('Рассада (дней)', validators=[DataRequired()])
    pots_at_sprouting = IntegerField('Горшков в проращивании', validators=[DataRequired()])
    pots_at_seedling = IntegerField('Горшков в рассаде', validators=[DataRequired()])
    pots_at_main_stage = IntegerField('Горшков на основном этапе', validators=[DataRequired()])
    min_days_from_planting = IntegerField('Мин. дней созревания (от посадки)', validators=[DataRequired()])
    min_weight_from_planting = FloatField('Мин. вес (г) (от посадки)', validators=[DataRequired()])
    max_days_from_planting = IntegerField('Макс. дней созревания (от посадки)', validators=[DataRequired()])
    max_weight_from_planting = FloatField('Макс. вес (г) (от посадки)', validators=[DataRequired()])
    min_days_from_cutting = IntegerField('Мин. дней созревания (после срезки)', validators=[DataRequired()])
    min_weight_from_cutting = FloatField('Мин. вес (г) (после срезки)', validators=[DataRequired()])
    max_days_from_cutting = IntegerField('Макс. дней созревания (после срезки)', validators=[DataRequired()])
    max_weight_from_cutting = FloatField('Макс. вес (г) (после срезки)', validators=[DataRequired()])
    submit = SubmitField('Сохранить культуру')