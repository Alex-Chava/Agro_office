from app import db
from flask import render_template, flash, redirect, url_for, jsonify, request, current_app
from flask_login import current_user, login_user, logout_user, login_required
from models import User, Parameter, Scenario, Tray, Culture, MixingParameter, Log, DensityRecord, Planting
from .forms import LoginForm, CultureForm
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from functools import wraps

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('У вас недостаточно прав для выполнения этого действия')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@current_app.route('/')
@current_app.route('/index')
@login_required
def index():
    parameters = Parameter.query.all()
    # Приводим ключи и значения к строковому типу
    parameters_dict = {}
    for param in parameters:
        key = param.controlled_parameter_name
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        value = param.value
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        parameters_dict[key] = value

    logs_info = Log.query.filter(Log.level == 'INFO').order_by(Log.timestamp.desc()).all()
    logs_errors = Log.query.filter(Log.level == 'ERROR').order_by(Log.timestamp.desc()).all()
    records = DensityRecord.query.order_by(DensityRecord.timestamp.desc()).all()
    time_adjustment = timedelta(hours=3)
    return render_template('main.html',
                           parameters=parameters,
                           parameters_dict=parameters_dict,
                           logs_info=logs_info,
                           logs_errors=logs_errors,
                           records=records,
                           timedelta=time_adjustment,
                           title='Главная')

@current_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@current_app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@current_app.route('/scenarios')
@login_required
def scenarios():
    irrigation_scenarios = Scenario.query.filter_by(type='Полив').order_by(Scenario.time).all()
    light_scenarios = Scenario.query.filter_by(type='Свет').order_by(Scenario.time).all()
    return render_template('scenarios.html',
                           irrigation_scenarios=irrigation_scenarios,
                           light_scenarios=light_scenarios,
                           title='Сценарии')

@current_app.route('/add_scenario', methods=['POST'])
@login_required
def add_scenario():
    data = request.get_json()
    scenario_time = datetime.strptime(data['time'], '%H:%M').time()
    new_scenario = Scenario(
        type=data['type'],
        time=scenario_time,
        parameter=data['parameter'],
        value=data['value'],
        result='',
        last_execution=datetime.now() - timedelta(days=1)
    )
    db.session.add(new_scenario)
    db.session.commit()
    return jsonify(success=True)

@current_app.route('/delete_scenario', methods=['POST'])
@login_required
def delete_scenario():
    data = request.get_json()
    scenario = Scenario.query.get(data['id'])
    if scenario:
        db.session.delete(scenario)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 400

@current_app.route('/get_parameters')
@login_required
def get_parameters():
    parameters = Parameter.query.all()
    parameters_dict = {}
    for param in parameters:
        key = param.controlled_parameter_name
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        value = param.value
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        parameters_dict[key] = value
    if parameters and parameters[0].value_date:
        parameters_dict['дата'] = parameters[0].value_date.strftime('%d.%m.%Y %H:%M:%S')
    return jsonify(parameters_dict)

@current_app.route('/toggle_parameter', methods=['POST'])
@login_required
def toggle_parameter():
    data = request.get_json()
    parameter_name = data.get('parameter')
    parameter = Parameter.query.filter_by(controlled_parameter_name=parameter_name).first()
    if parameter:
        parameter.value = '0' if parameter.value == '1' else '1'
        parameter.value_date = datetime.now()
        db.session.commit()
    return jsonify({'status': 'success'})

@current_app.route('/set_parameter_value', methods=['POST'])
@login_required
def set_parameter_value():
    data = request.get_json()
    parameter_name = data['parameter']
    parameter_value = data['value']
    parameter = Parameter.query.filter_by(controlled_parameter_name=parameter_name).first()
    if parameter:
        parameter.value = parameter_value
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 400

@current_app.route('/cultures')
@login_required
def cultures():
    cultures = Culture.query.all()
    form = CultureForm()
    return render_template('cultures.html', cultures=cultures, form=form, title='Справочник культур')

@current_app.route('/save_culture', methods=['POST'])
@login_required
def save_culture():
    form = CultureForm()
    if form.validate_on_submit():
        culture_id = request.form.get('culture_id')
        if culture_id:
            culture = Culture.query.get(culture_id)
            if culture:
                culture.name = form.name.data
                culture.sprouting_in_chamber_days = form.sprouting_in_chamber_days.data
                culture.sprouting_on_shelf_days = form.sprouting_on_shelf_days.data
                culture.seedling_days = form.seedling_days.data
                culture.pots_at_sprouting = form.pots_at_sprouting.data
                culture.pots_at_seedling = form.pots_at_seedling.data
                culture.pots_at_main_stage = form.pots_at_main_stage.data
                culture.min_days_from_planting = form.min_days_from_planting.data
                culture.min_weight_from_planting = form.min_weight_from_planting.data
                culture.max_days_from_planting = form.max_days_from_planting.data
                culture.max_weight_from_planting = form.max_weight_from_planting.data
                culture.min_days_from_cutting = form.min_days_from_cutting.data
                culture.min_weight_from_cutting = form.min_weight_from_cutting.data
                culture.max_days_from_cutting = form.max_days_from_cutting.data
                culture.max_weight_from_cutting = form.max_weight_from_cutting.data
            else:
                flash('Культура не найдена.', 'error')
                return redirect(url_for('cultures'))
        else:
            new_culture = Culture(
                name=form.name.data,
                sprouting_in_chamber_days=form.sprouting_in_chamber_days.data,
                sprouting_on_shelf_days=form.sprouting_on_shelf_days.data,
                seedling_days=form.seedling_days.data,
                pots_at_sprouting=form.pots_at_sprouting.data,
                pots_at_seedling=form.pots_at_seedling.data,
                pots_at_main_stage=form.pots_at_main_stage.data,
                min_days_from_planting=form.min_days_from_planting.data,
                min_weight_from_planting=form.min_weight_from_planting.data,
                max_days_from_planting=form.max_days_from_planting.data,
                max_weight_from_planting=form.max_weight_from_planting.data,
                min_days_from_cutting=form.min_days_from_cutting.data,
                min_weight_from_cutting=form.min_weight_from_cutting.data,
                max_days_from_cutting=form.max_days_from_cutting.data,
                max_weight_from_cutting=form.max_weight_from_cutting.data
            )
            db.session.add(new_culture)
        db.session.commit()
        flash('Культура успешно сохранена!', 'success')
    else:
        flash('Ошибка при сохранении культуры. Пожалуйста, проверьте введенные данные.', 'error')
    return redirect(url_for('cultures'))

@current_app.route('/get_culture/<int:culture_id>')
@login_required
def get_culture(culture_id):
    culture = Culture.query.get(culture_id)
    if culture:
        return jsonify({
            'culture_id': culture.culture_id,
            'name': culture.name,
            'sprouting_in_chamber_days': culture.sprouting_in_chamber_days,
            'sprouting_on_shelf_days': culture.sprouting_on_shelf_days,
            'seedling_days': culture.seedling_days,
            'pots_at_sprouting': culture.pots_at_sprouting,
            'pots_at_seedling': culture.pots_at_seedling,
            'pots_at_main_stage': culture.pots_at_main_stage,
            'min_days_from_planting': culture.min_days_from_planting,
            'min_weight_from_planting': culture.min_weight_from_planting,
            'max_days_from_planting': culture.max_days_from_planting,
            'max_weight_from_planting': culture.max_weight_from_planting,
            'min_days_from_cutting': culture.min_days_from_cutting,
            'min_weight_from_cutting': culture.min_weight_from_cutting,
            'max_days_from_cutting': culture.max_days_from_cutting,
            'max_weight_from_cutting': culture.max_weight_from_cutting
        })
    return jsonify({'error': 'Культура не найдена'}), 404

@current_app.route('/delete_culture/<int:culture_id>', methods=['POST'])
@login_required
def delete_culture(culture_id):
    culture = Culture.query.get(culture_id)
    if culture:
        db.session.delete(culture)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Культура не найдена'}), 404

@current_app.route('/mixing_parameters')
@login_required
def mixing_parameters():
    mixing_params = MixingParameter.query.first()
    return render_template('mixing_parameters.html', mixing_params=mixing_params, title='Растворный узел')

@current_app.route('/update_mixing_parameter', methods=['POST'])
@admin_required
def update_mixing_parameter():
    data = request.get_json()
    parameter_name = data.get('parameter_name')
    parameter_value = data.get('parameter_value')
    if not parameter_name or parameter_value is None:
        return jsonify({'error': 'Неверные данные'}), 400
    try:
        mixing_param = MixingParameter.query.first()
        if not mixing_param:
            return jsonify({'error': 'Параметры не найдены'}), 404
        valid_parameters = [
            'target_ec', 'target_ph', 'ec_deviation', 'ph_deviation',
            'mixing_speed', 'stabilization_time', 'pump_flow_rate',
            'density_a', 'density_b', 'density_acid', 'tank_volume',
            'bf', 'maxtime'
        ]
        if parameter_name in valid_parameters:
            new_value = float(parameter_value)
            setattr(mixing_param, parameter_name, new_value)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Неверное имя параметра'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error("Ошибка обновления mixing_parameter: %s", e)
        return jsonify({'error': str(e)}), 500

def get_tray_status(tray, date):
    if not tray or not tray.culture_id or not tray.sprouting_date:
        status = 'пуст'
        background_image = url_for('static', filename='images/empty.jpg')
        return {'status': status, 'backgroundImage': background_image}
    if tray.harvest_date:
        cut_status = 'С'
        min_days = tray.culture.min_days_from_cutting
        max_days = tray.culture.max_days_from_cutting
        min_weight = tray.culture.min_weight_from_cutting
        max_weight = tray.culture.max_weight_from_cutting
        start_date = tray.harvest_date
    else:
        cut_status = 'М'
        min_days = tray.culture.min_days_from_planting
        max_days = tray.culture.max_days_from_planting
        min_weight = tray.culture.min_weight_from_planting
        max_weight = tray.culture.max_weight_from_planting
        start_date = tray.sprouting_date
    min_ready_date = start_date + timedelta(days=min_days)
    max_ready_date = start_date + timedelta(days=max_days)
    if date < min_ready_date:
        days_to_min_ready = (min_ready_date - date).days
        growth_stage = (tray.growth_stage[0].upper() if tray.growth_stage else '')
        status = f"{cut_status} {tray.culture.name} {days_to_min_ready}д. ({growth_stage})"
        background_image = url_for('static', filename='images/growing.jpg')
    elif min_ready_date <= date <= max_ready_date:
        total_days = (max_ready_date - min_ready_date).days
        days_into_period = (date - min_ready_date).days
        weight = min_weight + ((max_weight - min_weight) * days_into_period / total_days) if total_days > 0 else max_weight
        total_weight = weight * tray.pots_planted / 1000
        status = f"{cut_status} {tray.culture.name} {total_weight:.1f}кг"
        background_image = url_for('static', filename='images/ready.jpg')
    elif date > max_ready_date:
        days_over = (date - max_ready_date).days
        status = f"{cut_status} {tray.culture.name} -{days_over}д."
        background_image = url_for('static', filename='images/overgrown.png')
    else:
        status = 'ошибка'
        background_image = url_for('static', filename='images/error.png')
    return {'status': status, 'backgroundImage': background_image}

@current_app.route('/plantings')
@login_required
def plantings():
    plantings = Planting.query.all()
    cultures = Culture.query.all()
    total_trays = 12
    free_trays = 0
    ready_cultures = defaultdict(lambda: {'pots': 0, 'weight': 0})
    current_date = datetime.now().date()
    plantings_dict = {p.tray_name: p for p in plantings}
    for tray in plantings:
        if not tray.culture_id or not tray.sprouting_date:
            free_trays += 1
        else:
            tray_status_info = get_tray_status(tray, current_date)
            if "кг" in tray_status_info['status']:
                culture_name = tray.culture.name
                ready_cultures[culture_name]['pots'] += tray.pots_planted
                weight_text = tray_status_info['status'].split()[-1].replace('кг', '')
                ready_cultures[culture_name]['weight'] += float(weight_text)
    percent_occupied = ((total_trays - free_trays) / total_trays) * 100
    lines = []
    for i in range(1, 5):
        line = {'number': i, 'zones': []}
        for j in range(1, 4):
            zone_name = f'Лоток-{i}-{j}'
            zone = {'name': zone_name, 'shelves': []}
            shelf = {'number': 1, 'trays': []}
            tray = plantings_dict.get(zone_name)
            if tray:
                tray_status_info = get_tray_status(tray, current_date)
            else:
                tray_status_info = {
                    'status': 'пуст',
                    'backgroundImage': url_for('static', filename='images/empty.jpg')
                }
            shelf['trays'].append({
                'id': zone_name,
                'status': tray_status_info['status'],
                'backgroundImage': tray_status_info['backgroundImage']
            })
            zone['shelves'].append(shelf)
            line['zones'].append(zone)
        lines.append(line)
    return render_template('plantings.html',
                           lines=lines,
                           cultures=cultures,
                           default_date=current_date.strftime('%Y-%m-%d'),
                           free_trays=free_trays,
                           percent_occupied=percent_occupied,
                           ready_cultures=ready_cultures)

@current_app.route('/get_tray_status')
@login_required
def get_tray_status_route():
    date_str = request.args.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    logger.info("Выбранная дата: %s", date)
    plantings = Planting.query.all()
    tray_statuses = {}
    for tray in plantings:
        tray_status_info = get_tray_status(tray, date)
        tray_statuses[tray.tray_name] = {
            'status': tray_status_info['status'],
            'backgroundImage': tray_status_info['backgroundImage']
        }
    return jsonify(tray_statuses)

@current_app.route('/planting_action', methods=['POST'])
@login_required
def planting_action():
    data = request.get_json()
    culture_id = data['culture_id']
    trays = data['trays']
    growth_stage = data.get('growth_stage')
    sprouting_date_str = data.get('sprouting_date')
    sprouting_date = datetime.strptime(sprouting_date_str, '%Y-%m-%d').date() if sprouting_date_str else datetime.now().date()
    culture = Culture.query.get(culture_id)
    for tray_name in trays:
        tray = Planting.query.filter_by(tray_name=tray_name).first()
        if tray:
            tray.sprouting_date = sprouting_date
            tray.culture_id = culture_id
            tray.pots_planted = culture.pots_at_main_stage
            tray.growth_stage = growth_stage
            logger.info("Обновлен лоток %s с культурой %s", tray_name, culture.name)
        else:
            new_tray = Planting(
                tray_name=tray_name,
                culture_id=culture_id,
                sprouting_date=sprouting_date,
                pots_planted=culture.pots_at_main_stage,
                growth_stage=growth_stage
            )
            db.session.add(new_tray)
            logger.info("Создан новый лоток %s с культурой %s", tray_name, culture.name)
    db.session.commit()
    return jsonify(success=True)

@current_app.route('/collect_trays', methods=['POST'])
@login_required
def collect_trays():
    data = request.get_json()
    trays = data['trays']
    for tray_name in trays:
        tray = Planting.query.filter_by(tray_name=tray_name).first()
        if tray:
            tray.culture_id = None
            tray.pots_planted = 0
            tray.sprouting_date = None
            tray.harvest_date = None
            tray.previous_harvest_date = None
            tray.growth_stage = 'Unknown'
            logger.info("Лоток %s собран и очищен.", tray_name)
        else:
            logger.warning("Лоток %s не найден для сбора.", tray_name)
    db.session.commit()
    return jsonify(success=True)

@current_app.route('/harvest_action', methods=['POST'])
@login_required
def harvest_action():
    data = request.get_json()
    harvest_date_str = data['harvest_date']
    trays = data['trays']
    harvest_date = datetime.strptime(harvest_date_str, '%Y-%m-%d').date()
    for tray_name in trays:
        tray = Planting.query.filter_by(tray_name=tray_name).first()
        if tray:
            if tray.harvest_date:
                tray.previous_harvest_date = tray.harvest_date
            tray.harvest_date = harvest_date
            logger.info("Обновлена дата срезки для лотка %s", tray_name)
        else:
            logger.warning("Лоток %s не найден для срезки.", tray_name)
    db.session.commit()
    return jsonify(success=True)

@current_app.route('/get_tray/<string:tray_name>')
@login_required
def get_tray(tray_name):
    tray = Planting.query.filter_by(tray_name=tray_name).first()
    if tray:
        return jsonify({
            'tray_name': tray.tray_name,
            'culture_id': tray.culture_id,
            'pots_planted': tray.pots_planted,
            'sprouting_date': tray.sprouting_date.strftime('%Y-%m-%d') if tray.sprouting_date else '',
            'harvest_date': tray.harvest_date.strftime('%Y-%m-%d') if tray.harvest_date else '',
            'previous_harvest_date': tray.previous_harvest_date.strftime('%Y-%m-%d') if tray.previous_harvest_date else '',
            'growth_stage': tray.growth_stage
        })
    return jsonify({'error': 'Лоток не найден'}), 404

@current_app.route('/update_tray', methods=['POST'])
@login_required
def update_tray():
    data = request.get_json()
    tray_name = data['tray_name']
    tray = Planting.query.filter_by(tray_name=tray_name).first()
    if tray:
        new_harvest_date = datetime.strptime(data.get('harvest_date'), '%Y-%m-%d').date() if data.get('harvest_date') else None
        if new_harvest_date and tray.harvest_date != new_harvest_date:
            tray.previous_harvest_date = tray.harvest_date
        tray.culture_id = data.get('culture_id') or None
        tray.pots_planted = data.get('pots_planted') or 0
        tray.sprouting_date = datetime.strptime(data.get('sprouting_date'), '%Y-%m-%d').date() if data.get('sprouting_date') else None
        tray.harvest_date = new_harvest_date
        tray.growth_stage = data.get('growth_stage') or None
        db.session.commit()
        logger.info("Лоток %s успешно обновлен, previous_harvest_date = %s", tray_name, tray.previous_harvest_date)
        return jsonify(success=True)
    logger.error("Лоток %s не найден", tray_name)
    return jsonify({'error': 'Лоток не найден'}), 404

@current_app.route('/check_trays_not_empty', methods=['POST'])
@login_required
def check_trays_not_empty():
    data = request.get_json()
    trays = data.get('trays', [])
    all_not_empty = True
    for tray_name in trays:
        tray = Planting.query.filter_by(tray_name=tray_name).first()
        if not tray or not tray.culture_id:
            all_not_empty = False
            logger.info("Лоток %s пустой или не существует.", tray_name)
            break
        else:
            logger.info("Лоток %s не пустой.", tray_name)
    return jsonify({'all_not_empty': all_not_empty})

@current_app.route('/check_trays_empty', methods=['POST'])
@login_required
def check_trays_empty():
    data = request.get_json()
    trays = data.get('trays', [])
    all_empty = True
    for tray_name in trays:
        tray = Planting.query.filter_by(tray_name=tray_name).first()
        if tray and tray.culture_id:
            all_empty = False
            logger.info("Лоток %s не пустой.", tray_name)
            break
        else:
            logger.info("Лоток %s пустой или не существует.", tray_name)
    return jsonify({'all_empty': all_empty})

@current_app.route('/check_tray_not_empty', methods=['POST'])
@login_required
def check_tray_not_empty():
    data = request.get_json()
    tray_name = data.get('tray')
    tray = Planting.query.filter_by(tray_name=tray_name).first()
    not_empty = bool(tray and tray.culture_id)
    logger.info("Лоток %s %s.", tray_name, "не пустой" if not_empty else "пустой или не существует")
    return jsonify({'not_empty': not_empty})

@current_app.route('/get_analysis')
@login_required
def get_analysis():
    date_str = request.args.get('date')
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    plantings = Planting.query.all()
    total_trays = 12
    free_trays = 0
    ready_cultures = defaultdict(lambda: {'pots': 0, 'weight': 0})
    for tray in plantings:
        if not tray.culture_id or not tray.sprouting_date:
            free_trays += 1
        else:
            tray_status_info = get_tray_status(tray, selected_date)
            if "кг" in tray_status_info['status']:
                culture_name = tray.culture.name
                ready_cultures[culture_name]['pots'] += tray.pots_planted
                weight_text = tray_status_info['status'].split()[-1].replace('кг', '')
                ready_cultures[culture_name]['weight'] += float(weight_text)
    percent_occupied = ((total_trays - free_trays) / total_trays) * 100
    analysis_data = {
        'free_trays': free_trays,
        'percent_occupied': round(percent_occupied, 2),
        'ready_cultures': [
            {'name': culture, 'pots': data['pots'], 'weight': round(data['weight'], 2)}
            for culture, data in ready_cultures.items()
        ]
    }
    return jsonify(analysis_data)

@current_app.route('/control')
@login_required
def control():
    trays = Tray.query.all()
    lines = [
        {
            'number': i,
            'zones': [
                {
                    'name': f'Лоток-{i}-{j}',
                    'shelves': [
                        {
                            'number': 1,
                            'trays': [
                                next((t for t in trays if t.shelf == f'Лоток-{i}-{j}'), Tray(shelf=f'Лоток-{i}-{j}', action='', plant_type='', growth_days=0))
                            ]
                        }
                    ]
                } for j in range(1, 4)
            ]
        } for i in range(1, 5)
    ]
    default_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('control.html', lines=lines, default_date=default_date, title='Контроль посадки')
