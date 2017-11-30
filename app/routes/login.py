# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, request
from app.models import User
from flask_login import login_user, logout_user, current_user

login_blueprint = Blueprint('login', __name__)


@login_blueprint.route("/login")
def login_seite():
    users = User.query.all()
    if current_user.is_authenticated:
        return redirect("/")
    return render_template("login.html", users=users, next=request.args.get('next', ''))


@login_blueprint.route("/login/<user_id>")
def login(user_id):
    user = User.query.get(user_id)
    next_url = request.args.get('next', '/')
    if user:
        login_user(user)

    return redirect(next_url)


@login_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect("/login")
