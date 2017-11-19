# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, request
from app.models import User
from flask_login import login_user, logout_user

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def index():
    return render_template("index.html")


@main_blueprint.route("/login")
def login_seite():
    users = User.query.all()
    return render_template("login.html", users=users, next=request.args.get('next', ''))


@main_blueprint.route("/login/<user_id>")
def login(user_id):
    user = User.query.get(user_id)
    next_url = request.args.get('next', '')
    if user:
        login_user(user)

        if next_url:
            return redirect(next_url)
        else:
            return redirect("/")
    else:

        return "Error"


@main_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect("/login")
