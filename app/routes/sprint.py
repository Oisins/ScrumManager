# -*- coding: utf-8 -*-
import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, request
from flask_login import current_user
from app.models import db, User, Sprint, Story, Task, Kriterium, Meeting

blueprint = Blueprint('sprint', __name__)


@blueprint.route("/sprints/<sprint_id>", methods=["GET"])
def seite_sprint_get(sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)

    return render_template("sprint.html", sprint=sprint, users=User.query.all())


@blueprint.route("/sprints/<sprint_id>", methods=["POST"])
def seite_sprint_post(sprint_id):
    db.session.autoflush = False
    sprint = Sprint.query.get_or_404(sprint_id)

    sprint.start = request.form.get("start")
    sprint.ende = request.form.get("ende")
    sprint.ziel = request.form.get("ziel")

    for story_data in json.loads(request.form.get("data")):
        story = Story.query.get(story_data.get("id"))
        if story_data.get("to_delete"):
            db.session.delete(story)
            continue

        if not story:
            story = Story(sprint=sprint)
            db.session.add(story)

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


@blueprint.route("/meetings/<meeting_id>")
def seite_meeting(meeting_id):
    return render_template("meeting.html", meeting=Meeting.query.get_or_404(meeting_id))