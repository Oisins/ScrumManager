# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from app.models import db, User, Sprint, Story, Task
from flask_login import login_user, logout_user, current_user

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def index():
    return render_template("index.html")


@main_blueprint.route("/sprints")
def sprints_seite():
    return render_template("sprints.html", sprints=Sprint.query.all())


@main_blueprint.route("/login")
def login_seite():
    users = User.query.all()
    if current_user.is_authenticated:
        return redirect("/")
    return render_template("login.html", users=users, next=request.args.get('next', ''))


@main_blueprint.route("/login/<user_id>")
def login(user_id):
    user = User.query.get(user_id)
    next_url = request.args.get('next', '')
    if user:
        login_user(user)

        if next_url:
            return redirect(next_url)
    return redirect("/")


@main_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@main_blueprint.route("/sprints")
def all_sprints():
    sprints = Sprint.query.all()

    return render_template("sprints.html", sprints=sprints)


@main_blueprint.route("/sprints/<sprint_id>", methods=["GET", "POST"])
def view_sprint(sprint_id):
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

        story.beschreibung = story_data.get("beschreibung")

        Task.query.filter_by(story_id=story.id).delete()
        for task_data in story_data.get("tasks", []):
            task = Task()

            task.story = story
            task.status = task_data.get("status")
            task.name = task_data.get("name")
            task.user = User.query.get(task_data.get("user_id"))

            story.tasks.append(task)
            db.session.add(task)

    db.session.commit()

    return redirect(f"/sprints/{sprint_id}")
