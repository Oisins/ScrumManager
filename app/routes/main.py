# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from app.models import db, User, Sprint, Story, Task
from flask_login import current_user

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route("/")
def seite_index():
    tasks = []
    aktiver_sprint = None
    for sprint in Sprint.query.all():
        if sprint.ist_aktiv:
            tasks = sprint.get_tasks()
            aktiver_sprint = sprint
    else:
        # Kein aktiver Sprint
        # TODO Burndown chart verstecken
        pass

    tasks = [task for task in tasks if task.user == current_user]
    tasks.sort(key=lambda task: task.status)

    return render_template("dashboard.html", tasks=tasks, aktiver_sprint=aktiver_sprint)


@main_blueprint.route("/backlog")
def seite_backlog():
    return render_template("backlog.html")


@main_blueprint.route("/users", methods=["GET", "POST"])
def seite_users():
    if request.method == "POST":
        user_id = request.form.get("id")
        delete = request.form.get("delete")
        if delete:
            db.session.delete(User.query.get(user_id))
            db.session.commit()
            return redirect("/users")

        if user_id == "-1":
            user = User()
            db.session.add(user)
        else:
            user = User.query.get(user_id)

        if user:
            user.rolle = request.form.get("rolle")
            user.name = request.form.get("name")

            db.session.commit()
        return redirect("/users")

    def users_nach_rolle(rolle):
        return User.query.filter_by(rolle=rolle).all()

    users = User.query.all()  # "SELECT * FROM user;" => [User1, User2, ...]
    return render_template("users.html", users=users, users_nach_rolle=users_nach_rolle)


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

        story.beschreibung = story_data.get("beschreibung")

        Task.query.filter_by(story_id=story.id).delete()
        for task_data in story_data.get("tasks", []):
            task = Task()

            task.story = story
            task.status = task_data.get("status")
            if task.status == 2:
                task.fertig()
            task.name = task_data.get("name")
            task.user = User.query.get(task_data.get("user_id"))

            story.tasks.append(task)
            db.session.add(task)

    db.session.commit()

    return redirect(f"/sprints/{sprint_id}")
