# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, request
from app.models import User
from flask_login import login_user, logout_user

dev_blueprint = Blueprint('dev', __name__, url_prefix="/dev")


@dev_blueprint.route("/")
def index():
    return render_template("index.html")


@dev_blueprint.route("/<fname>")
def page(fname):
    return render_template(f"{fname}.html")
