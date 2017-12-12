# -*- coding: utf-8 -*-
from uuid import uuid4
from . import db
from flask_login import UserMixin, current_user
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), default="")
    rolle = db.Column(db.String(30), default="team")
    tasks = db.relationship('Task', backref=db.backref('user', lazy=True))
    impediments = db.relationship('Impediment', backref=db.backref('user', lazy=True))
    antworten = db.relationship('Antwort', backref=db.backref('user', lazy=True))

    def tasks_nach_status(self, status):
        return Task.query.filter_by(status=status, user_id=self.id).all()

    def json(self):
        return {"id": self.id,
                "name": self.name,
                "rolle": self.rolle}


class Task(db.Model):
    __tablename__ = 'Task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500), default="")
    status = db.Column(db.Integer, default=0)  # 0 - Backlog 1 - In Progress 2 - Fertig
    story_id = db.Column(db.Integer, db.ForeignKey('Story.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    sprint = association_proxy('story', 'sprint')
    _fertig_datum = db.Column(db.DateTime)

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
    titel = db.Column(db.String(150), default="")
    beschreibung = db.Column(db.String(500), default="")
    sprint_id = db.Column(db.Integer, db.ForeignKey('Sprint.id'))
    sprint = db.relationship('Sprint', backref=db.backref('stories', lazy=True))
    tasks = db.relationship('Task', backref='story', lazy='dynamic', cascade="all, delete-orphan")
    kriterien = db.relationship('Kriterium', backref=db.backref('story', lazy=True))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = str(uuid4())

    def nach_status(self, status):
        return Task.query.filter_by(story_id=self.id, status=status)

    def json(self):
        return {"id": self.id,
                "titel": self.titel,
                "beschreibung": self.beschreibung,
                "sprint_id": self.sprint_id,
                "kriterien": [kriterium.json() for kriterium in self.kriterien],
                "tasks": [task.json() for task in self.tasks]}


class Kriterium(db.Model):
    __tablename__ = 'Kriterium'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    beschreibung = db.Column(db.String(500), default="")
    story_id = db.Column(db.String(38), db.ForeignKey('Story.id'))

    def json(self):
        return {"id": self.id,
                "beschreibung": self.beschreibung}


class Sprint(db.Model):
    __tablename__ = 'Sprint'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ziel = db.Column(db.String(500), default="")
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
            self._ende = None

    def anzahl_status(self, status):
        data = db.session.query(func.count(Task.status)) \
            .group_by(Task.status) \
            .filter(Task.status == status, Task.sprint == self).scalar()

        if not data:
            return 0
        return data

    def get_tasks(self):
        tasks = []
        for story in self.stories:
            tasks += story.tasks
        return tasks

    @hybrid_property
    def aktiv(self):
        if not (self._ende and self._start):
            return False
        now = datetime.now().date()
        return (self._start <= now) & (now <= self._ende)

    @staticmethod
    def get_aktiv():
        return Sprint.query.filter_by(aktiv=True).first()

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
            delta = self._ende - now
            return f"Noch {delta.days} Tag(e)"


class Impediment(db.Model):
    __tablename__ = 'Impediment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    beschreibung = db.Column(db.String(500), default="")
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    _status = db.relationship('ImpedimentStatus', backref=db.backref('impediment', lazy=True))
    prio = db.Column(db.String(30))
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
        s = ImpedimentStatus(status=wert)
        s.status = wert
        self._status.append(s)
        db.session.add(s)
        db.session.commit()


class ImpedimentStatus(db.Model):
    __tablename__ = 'ImpedimentStatus'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    impediment_id = db.Column(db.Integer, db.ForeignKey('Impediment.id'))

    status = db.Column(db.Integer)
    _datum = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(**kwargs)
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


class Meeting(db.Model):
    __tablename__ = "Meeting"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    antworten = db.relationship('Antwort', backref=db.backref('meeting', lazy=True))
    _datum = db.Column("datum", db.Date)
    typ = db.Column(db.String(50))

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
        return {"id": self.id,
                "antworten": [antwort.json() for antwort in self.antworten],
                "typ": self.typ,
                "iso_datum": self._datum.strftime('%Y-%m-%d') if self._datum else "",
                "datum": self.datum}


class Antwort(db.Model):
    __tablename__ = "Antwort"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    antwort1 = db.Column(db.String(500), default="")
    antwort2 = db.Column(db.String(500), default="")
    antwort3 = db.Column(db.String(500), default="")
    typ = db.Column(db.String(50), default="sonstiges")
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    meeting_id = db.Column(db.Integer, db.ForeignKey('Meeting.id'))

    def json(self):
        return {"id": self.id,
                "antwort1": self.antwort1,
                "antwort2": self.antwort2,
                "antwort3": self.antwort3,
                "user": self.user.json()}
