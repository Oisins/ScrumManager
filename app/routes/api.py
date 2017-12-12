# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, redirect, request
from app.models import Task, User, Story, Sprint, Meeting, db

api_blueprint = Blueprint('api', __name__, url_prefix="/api")


@api_blueprint.route("/tasks")
def api_get_tasks():
    tasks = Task.query.all()
    return jsonify([task.json() for task in tasks])


@api_blueprint.route("/users")
def api_get_users():
    users = User.query.all()
    return jsonify([user.json() for user in users])


@api_blueprint.route("/meetings")
def api_meetings():
    meetings = Meeting.query.all()
    return jsonify([meeting.json() for meeting in meetings])


@api_blueprint.route("/newuser", methods=["POST"])
def api_new_user():
    user = User()
    user.name = request.form.get("name", "Neuer Nutzer")
    user.rolle = request.form.get("rolle", "team")
    db.session.add(user)
    db.session.commit()

    return redirect("/")


@api_blueprint.route("/stories")
def api_stories():
    stories = Story.query.all()
    return jsonify([story.json() for story in stories])


@api_blueprint.route("/sprint/<s_id>")
def api_sprint(s_id):
    sprint = Sprint.query.get(s_id)
    return jsonify(sprint.json())


@api_blueprint.route("/burndown/<s_id>")
def api_burndown_data(s_id):
    sprint = Sprint.query.get(s_id)
    if not sprint:
        return jsonify({"error": "Sprint nicht gefunden"})
    tasks = sprint.get_tasks()
    tasks.sort(key=lambda x: x.fertig_datum)

    anzahl_unfertig = len(tasks)
    data = {}
    out = {"start": sprint._start.strftime('%Y-%m-%d'),
           "ende": sprint._ende.strftime('%Y-%m-%d'),
           "anzahl": anzahl_unfertig,
           "data": []}

    data[sprint._start.strftime('%Y-%m-%d')] = anzahl_unfertig
    for task in tasks:
        if not task.fertig_datum or task.status != 2:
            continue
        datum_formatiert = task._fertig_datum.strftime('%Y-%m-%d')
        anzahl_unfertig -= 1
        data[datum_formatiert] = anzahl_unfertig

    for datum, anzahl in data.items():
        out["data"].append((datum, anzahl))
    return jsonify(out)
