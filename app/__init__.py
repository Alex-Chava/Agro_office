import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'login'
login.login_message = None  # Убираем приветственное сообщение

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Установка папки для статических файлов
    package_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(package_dir, "static")
    app.static_folder = static_folder

    db.init_app(app)
    login.init_app(app)

    with app.app_context():
        from . import routes
        import models
        db.create_all()

    return app
