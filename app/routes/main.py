# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from flask_login import current_user
from app.models import db, User, Sprint, Story, Task, Kriterium, Impediment

blueprint = Blueprint('main', __name__)


@blueprint.route("/")
def seite_index():
    tasks = Task.query.filter_by(user=current_user, sprint=Sprint.get_aktiv()) \
        .order_by(Task.status) \
        .all()

    return render_template("dashboard.html", tasks=tasks)


@blueprint.route("/backlog", methods=["GET"])
def seite_backlog_get():
    return render_template("backlog.html", stories=Story.query.all(), sprints=Sprint.query.all())


@blueprint.route("/backlog", methods=["POST"])
def seite_backlog_post():
    data = json.loads(request.form.get("data"))
    story = Story.query.get(data.get("id"))
    sprint_id = data.get("sprint_id", "-1")
    if data.get("to_delete"):
        if story:
            db.session.delete(story)
            db.session.commit()
        return redirect("/backlog")

    if not story:
        story = Story()
        db.session.add(story)

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


@blueprint.route("/users", methods=["GET", "POST"])
def seite_users():
    if request.method == "GET":
        return render_template("users.html",
                               users=User.query.all(),
                               users_nach_rolle=lambda rolle: User.query.filter_by(rolle=rolle).all())

    user = User.query.get(request.form.get("id"))

    if request.form.get("delete", False):
        if user:
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


@blueprint.route("/sprints", methods=["GET", "POST"])
def seite_sprints():
    if request.method == "POST" and request.form.get("neu", False):
        sprint = Sprint()
        db.session.add(sprint)
        db.session.commit()
        return redirect("/sprints")

    return render_template("sprints.html", sprints=Sprint.query.all())


@blueprint.route("/impediment", methods=["GET"])
def seite_impediment_get():
    impediment = Impediment.query.all()

    return render_template("impediment.html", impediments=impediment)


@blueprint.route("/impediment", methods=["POST"])
def seite_impediment_post():
    impediment_id = request.form.get("id", "")
    if not impediment_id:
        return redirect("/impediment")

    impediment = Impediment.query.get(impediment_id)

    if request.form.get("to_delete", False):
        if impediment:
            db.session.delete(impediment)
            db.session.commit()
        return redirect("/impediment")

    if not impediment:
        impediment = Impediment()
        db.session.add(impediment)

    impediment.beschreibung = request.form.get("beschreibung")
    impediment.status = request.form.get("status")
    impediment.prio = request.form.get("prio")
    impediment.verantwortlich = request.form.get("verantwortlich")
    impediment.behandlung = request.form.get("behandlung")

    db.session.commit()
    return redirect("/impediment")
