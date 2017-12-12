# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, redirect, request
from app.models import db, User, Antwort, Meeting

meeting_blueprint = Blueprint('meeting', __name__)


@meeting_blueprint.route("/meetings")
def seite_meetings():
    return render_template("meetings.html", meetings=Meeting.query.all())


@meeting_blueprint.route("/meetings/neu")
def seite_meetings_neu():
    meeting = Meeting()
    db.session.add(meeting)
    db.session.commit()
    return redirect(f"/meetings/{meeting.id}")


@meeting_blueprint.route("/meetings/<meeting_id>")
def seite_meeting(meeting_id):
    return render_template("meeting.html", meeting=Meeting.query.get_or_404(meeting_id), users=User.query.all())


@meeting_blueprint.route("/meetings/<meeting_id>", methods=["POST"])
def seite_meeting_post(meeting_id):
    db.session.autoflush = False

    meeting = Meeting.query.get_or_404(meeting_id)
    meeting.datum = request.form.get("datum", "")
    meeting.typ = request.form.get("typ", "sonstiges")

    for antwort_data in json.loads(request.form.get("antworten")):
        antwort = Antwort.query.get(antwort_data.get("id"))
        if antwort_data.get("to_delete"):
            db.session.delete(antwort)
            continue

        if not antwort:
            antwort = Antwort(meeting=meeting)
            db.session.add(antwort)

        antwort.antwort1 = antwort_data.get("antwort1")
        antwort.antwort2 = antwort_data.get("antwort2")
        antwort.antwort3 = antwort_data.get("antwort3")
        antwort.user = User.query.get(antwort_data.get("user")["id"])
    db.session.commit()
    return redirect("/meetings/" + meeting_id)
