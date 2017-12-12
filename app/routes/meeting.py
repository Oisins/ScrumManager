# -*- coding: utf-8 -*-
import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, request
from flask_login import current_user
from app.models import db, User, Sprint, Story, Task, Kriterium, Meeting

meeting_blueprint = Blueprint('meeting', __name__)


@meeting_blueprint.route("/meetings")
def seite_meetings():
    return render_template("meetings.html", meetings=Meeting.query.all())


@meeting_blueprint.route("/meetings/<meeting_id>")
def seite_meeting(meeting_id):
    return render_template("meeting.html", meeting=Meeting.query.get_or_404(meeting_id))
