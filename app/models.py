# -*- coding: utf-8 -*-
from uuid import uuid4
from . import db
from flask_login import UserMixin
from datetime import datetime, date


# Beispiel Tabelle
class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    rolle = db.Column(db.String(30))

    def json(self):
        return {"id": self.id,
                "name": self.name,
                "rolle": self.rolle}


class Task(db.Model):
    __tablename__ = 'Task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500))
    status = db.Column(db.Integer, default=0)  # 0 - Backlog 1 - In Progress 2 - Fertig
    story_id = db.Column(db.Integer, db.ForeignKey('Story.id'), nullable=False)
    story = db.relationship('Story', backref=db.backref('tasks', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

    def json(self):
        return {"id": self.id,
                "name": self.name,
                "status": self.status,
                "story_id": self.story_id,
                "user": self.user.json() if self.user else {"id": -1, "name": "Nicht zugewiesen"}}


class Story(db.Model):
    __tablename__ = 'Story'
    id = db.Column(db.String(38), primary_key=True)
    beschreibung = db.Column(db.String(500))
    sprint_id = db.Column(db.Integer, db.ForeignKey('Sprint.id'), nullable=False)
    sprint = db.relationship('Sprint', backref=db.backref('stories', lazy=True))

    def __init__(self):
        self.id = str(uuid4())

    def nach_status(self, status):
        return Task.query.filter_by(story_id=self.id, status=status)

    def json(self):
        return {"id": self.id,
                "beschreibung": self.beschreibung,
                "tasks": [task.json() for task in self.tasks]}


class Sprint(db.Model):
    __tablename__ = 'Sprint'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    _start = db.Column("start", db.Date)
    _ende = db.Column("end", db.Date)

    def json(self):
        return {"id": self.id,
                "start": self.start,
                "ende": self.ende,
                "stories": [story.json() for story in self.stories]}

    @property
    def start(self):
        if self._start:
            return self._start.strftime('%d.%m.%Y')
        return ""

    @start.setter
    def start(self, value):
        self._start = datetime.strptime(value, "%d.%m.%Y").date()

    @property
    def ende(self):
        if self._ende:
            return self._ende.strftime('%d.%m.%Y')
        return ""

    @ende.setter
    def ende(self, value):
        self._ende = datetime.strptime(value, "%d.%m.%Y").date()

    def count_status(self, status):
        tasks = []
        for story in self.stories:
            tasks += story.tasks

        return len([task for task in tasks if task.status == status])

    def status_desc(self):
        if not (self._ende and self._start):
            return "Unbekannt"

        now = datetime.now().date()

        if now < self._start:
            until = self._start - now
            return f"In {until.days} Tage(n)"

        elif now > self._ende:
            return "Beendet"

        elif self._start <= now <= self._ende:
            remaining = self._ende - now
            return f"Noch {remaining.days} Tag(e)"
