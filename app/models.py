# -*- coding: utf-8 -*-
from . import db
from flask_login import UserMixin
from datetime import datetime


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
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

    def json(self):
        return {"id": self.id,
                "name": self.name,
                "status": self.status,
                "story_id": self.story_id,
                "user": self.user.json()}


class Story(db.Model):
    __tablename__ = 'Story'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    beschreibung = db.Column(db.String(500))
    sprint_id = db.Column(db.Integer, db.ForeignKey('Sprint.id'), nullable=False)
    sprint = db.relationship('Sprint', backref=db.backref('stories', lazy=True))

    def nach_status(self, status):
        return Task.query.filter_by(story_id=self.id, status=status)

    def json(self):
        return {"id": self.id,
                "beschreibung": self.beschreibung}


class Sprint(db.Model):
    __tablename__ = 'Sprint'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    _start = db.Column("start", db.Date)
    _ende = db.Column("end", db.Date)

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
