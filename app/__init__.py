# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect
from flask_login import LoginManager, current_user
from config import config
from flask_sqlalchemy import SQLAlchemy


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

    @app.context_processor
    def utility_processor():
        def get_aktiver_sprint():
            return Sprint.get_aktiv()

        return dict(get_aktiver_sprint=get_aktiver_sprint)

    for blueprint in routes.blueprints:
        app.register_blueprint(blueprint)

    return app
