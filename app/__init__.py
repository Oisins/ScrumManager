# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect
from flask_login import LoginManager, current_user
from config import config
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import find_modules, import_string


db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login.login_seite"

erlaubte_routen = ["static", "login", "api/newuser"]


def ist_erlaubt(route):
    for erlaubte_route in erlaubte_routen:
        if erlaubte_route in route:
            return True
    return False


def create_app(config_name):
    from app import routes
    from app.models import User, Sprint
    from app.utils import register_processors

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    db.app = app
    db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @app.before_request
    def check_login():
        if not current_user.is_authenticated and not ist_erlaubt(request.path):
            return login_manager.unauthorized()

    @app.errorhandler(404)
    def page_not_found(e):
        if not current_user.is_authenticated:
            return redirect("/"), 403
        return render_template('404.html'), 404

    for filename in find_modules('app.routes'):
        mod = import_string(filename)
        if hasattr(mod, 'blueprint'):
            app.register_blueprint(mod.blueprint)

    register_processors(app)

    return app
