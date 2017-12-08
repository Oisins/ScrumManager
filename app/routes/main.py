# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from app.models import db, User, Sprint, Story, Task, Kriterium
from flask_login import current_user
from datetime import datetime

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def seite_index():
    tasks = []
    sprint = Sprint.get_aktiv()
    if sprint:
        tasks = [task for task in sprint.get_tasks() if task.user == current_user]
        tasks.sort(key=lambda task: task.status)

    return render_template("dashboard.html", tasks=tasks)


@main_blueprint.route("/backlog", methods=["GET", "POST"])
def seite_backlog():
    if request.method == "POST":
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

    return render_template("backlog.html", stories=Story.query.all(), sprints=Sprint.query.all())


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


@main_blueprint.route("/sprints/<sprint_id>", methods=["GET", "POST"])
def seite_sprint(sprint_id):
    db.session.autoflush = False

    sprint = Sprint.query.get_or_404(sprint_id)

    if request.method == "GET":
        return render_template("sprint.html", sprint=sprint, users=User.query.all())

    sprint.start = request.form.get("start")
    sprint.ende = request.form.get("ende")

    for story_data in json.loads(request.form.get("data")):
        story = Story.query.get(story_data.get("id"))

        if not story:
            story = Story()
            story.sprint = sprint
            db.session.add(story)
        elif story_data.get("to_delete", False):
            db.session.delete(story)
            continue

        story.titel = story_data.get("titel")
        story.beschreibung = story_data.get("beschreibung")

        for task_data in story_data.get("tasks", []):
            task = Task.query.get(task_data.get("id"))
            if task and task_data.get("delete", False):
                db.session.delete(task)
                continue

            if not task:
                task = Task()

            task.story = story
            task.name = task_data.get("name")
            task.user = User.query.get(task_data.get("user_id"))

            neuer_status = task_data.get("status")
            if task.status != neuer_status and neuer_status == 2:
                task._fertig_datum = datetime.now()
            task.status = neuer_status

            story.tasks.append(task)
            db.session.add(task)

    db.session.commit()

    return redirect(f"/sprints/{sprint_id}")
