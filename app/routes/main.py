# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from flask_login import current_user
from app.models import db, User, Sprint, Story, Task, Kriterium

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def seite_index():
    tasks = Task.query.filter_by(user=current_user, sprint=Sprint.get_aktiv()) \
        .order_by(Task.status) \
        .all()

    return render_template("dashboard.html", tasks=tasks)


@main_blueprint.route("/backlog", methods=["GET"])
def seite_backlog_get():
    return render_template("backlog.html", stories=Story.query.all(), sprints=Sprint.query.all())


@main_blueprint.route("/backlog", methods=["POST"])
def seite_backlog_post():
    data = json.loads(request.form.get("data"))
    story = Story.query.get(data.get("id"))
    sprint_id = data.get("sprint_id", "-1")
    if not story:
        return redirect("/backlog")

    story.titel = data.get("titel")
    story.beschreibung = data.get("beschreibung")
    story.sprint = Sprint.query.get(sprint_id)

    Kriterium.query.filter_by(story=story).delete()
    for kriterium in data.get("kriterien", []):
        k = Kriterium()
        k.beschreibung = kriterium.get("beschreibung")
        db.session.add(k)
        story.kriterien.append(k)

    db.session.commit()
    return redirect("/backlog")


@main_blueprint.route("/users", methods=["GET", "POST"])
def seite_users():
    if request.method == "GET":
        return render_template("users.html",
                               users=User.query.all(),
                               users_nach_rolle=lambda rolle: User.query.filter_by(rolle=rolle).all())

    user = User.query.get(request.form.get("id"))

    if request.form.get("delete", False):
        db.session.delete(user)
        db.session.commit()
        return redirect("/users")

    if not user:
        user = User()
        db.session.add(user)

    user.rolle = request.form.get("rolle")
    user.name = request.form.get("name")

    db.session.commit()
    return redirect("/users")


@main_blueprint.route("/sprints", methods=["GET", "POST"])
def seite_sprints():
    if request.method == "POST" and request.form.get("neu", False):
        sprint = Sprint()
        db.session.add(sprint)
        db.session.commit()
        return redirect("/sprints")

    return render_template("sprints.html", sprints=Sprint.query.all())



