# -*- coding: utf-8 -*-
from uuid import uuid4
from . import db
from flask_login import UserMixin, current_user
from datetime import datetime, date
from sqlalchemy import func


# Beispiel Tabelle
class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    rolle = db.Column(db.String(30))

    def tasks_nach_status(self, status):
        return Task.query.filter_by(status=status, user_id=self.id).all()

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
    story = db.relationship('Story', backref=db.backref('tasks', cascade="all, delete-orphan", lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    _fertig_datum = db.Column(db.DateTime)

    def fertig(self):
        self._fertig_datum = datetime.now()

    @property
    def fertig_datum(self):
        if self._fertig_datum:
            return self._fertig_datum.strftime('%d.%m.%Y')
        return ""

    @fertig_datum.setter
    def fertig_datum(self, value):
        try:
            self._fertig_datum = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            self._fertig_datum = None

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
        try:
            self._start = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            self._start = None

    @property
    def ende(self):
        if self._ende:
            return self._ende.strftime('%d.%m.%Y')
        return ""

    @ende.setter
    def ende(self, value):
        try:
            self._ende = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            self._start = None

    def anzahl_status(self, status):
        data = db.session.query(func.count(Task.status), Task.status) \
            .group_by(Task.status) \
            .filter_by(status=status) \
            .first()
        if not data:
            return 0
        return data[0]

    def get_tasks(self):
        tasks = []
        for story in self.stories:
            tasks += story.tasks
        return tasks

    @property
    def ist_aktiv(self):
        if not (self._ende and self._start):
            return False
        now = datetime.now().date()
        return self._start <= now <= self._ende

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


class Impediment(db.Model):
    __tablename__ = 'Impediment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    beschreibung = db.Column(db.String(500), default="")
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    user = db.relationship('User', backref=db.backref('impediments', lazy=True))
    prio = db.Column(db.String(30))  # TODO: In INT umwandeln und GET, SETTER für String
    verantwortlich = db.Column(db.String(30), default="")
    behandlung = db.Column(db.String(500), default="")
    _datum = db.Column(db.DateTime)

    def __init__(self):
        self.datum = datetime.now()
        self.status = 0
        self.user = current_user

    @property
    def datum(self):
        if not self._datum:
            return ""
        return self._datum.strftime('%d.%m.%Y')

    @datum.setter
    def datum(self, value):
        try:
            self._datum = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            self._datum = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, wert):
        s = ImpedimentStatus()
        s.status = wert
        self._status.append(s)
        db.session.add(s)
        db.session.commit()

    def json(self):
        # todo
        return {"id": self.id,
                "name": self.name,
                "rolle": self.rolle}


class ImpedimentStatus(db.Model):
    __tablename__ = 'ImpedimentStatus'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    impediment_id = db.Column(db.Integer, db.ForeignKey('Impediment.id'))
    impediment = db.relationship('Impediment', backref=db.backref('_status', lazy=True))
    status = db.Column(db.Integer)
    _datum = db.Column(db.DateTime)

    def __init__(self):
        self._datum = datetime.now()

    @property
    def datum(self):
        if self._datum:
            return self._datum.strftime('%d.%m.%Y')
        return ""

    @datum.setter
    def datum(self, value):
        try:
            self._datum = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            self._datum = None

    def json(self):
        # todo
        return {"id": self.id,
                "name": self.name,
                "rolle": self.rolle}
