# -*- coding: utf-8 -*-
from flask import Flask, request
from flask_login import LoginManager, current_user
from config import config
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(config_name):
    from app import routes
    from app.models import User

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    db.init_app(app)
    db.app = app
    db.create_all()


    for blueprint in routes.blueprints:
        app.register_blueprint(blueprint)

    return app
