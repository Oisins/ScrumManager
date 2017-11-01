# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, request
from app.models import User
from flask_login import login_user, logout_user

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def index():
    return render_template("login.html")