# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
from app.models import Task, User, Story, Sprint

api_blueprint = Blueprint('api', __name__, url_prefix="/api")


@api_blueprint.route("/tasks")
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.json() for task in tasks])


@api_blueprint.route("/users")
def get_users():
    users = User.query.all()
    return jsonify([user.json() for user in users])


@api_blueprint.route("/stories")
def get_stories():
    stories = Story.query.all()
    return jsonify([story.json() for story in stories])


@api_blueprint.route("/sprint/<s_id>")
def get_sprint(s_id):
    sprint = Sprint.query.get(s_id)
    return jsonify(sprint.json())
