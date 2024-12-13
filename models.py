from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=True)  # Made nullable for initial creation
    role = db.Column(db.String(20), nullable=False)  # admin, judge, dancer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expiration = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)  # Account becomes active after setting password
    # For dancers
    dancer_profile = db.relationship('Dancer', backref='user', uselist=False, cascade='all, delete-orphan')
    # For judges
    judged_competitions = db.relationship('Competition', secondary='judge_competition', backref='judges')
    # Scores given by judges
    scores = db.relationship('Score', backref='judge', cascade='all, delete-orphan')

# Association table for judges and competitions
judge_competition = db.Table('judge_competition',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id', ondelete='CASCADE'), primary_key=True)
)

class Dancer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date, nullable=False)
    level = db.Column(db.String(20), nullable=False)  # Newcomer, Novice, Intermediate, Advanced, AllStar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Competitions this dancer is participating in
    competitions = db.relationship('Competition', secondary='dancer_competition', backref='dancers')
    # Leader pairings
    leader_pairings = db.relationship('Pairing', foreign_keys='Pairing.leader_id', backref='leader', cascade='all, delete-orphan')
    # Follower pairings
    follower_pairings = db.relationship('Pairing', foreign_keys='Pairing.follower_id', backref='follower', cascade='all, delete-orphan')

# Association table for dancers and competitions
dancer_competition = db.Table('dancer_competition',
    db.Column('dancer_id', db.Integer, db.ForeignKey('dancer.id', ondelete='CASCADE'), primary_key=True),
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id', ondelete='CASCADE'), primary_key=True)
)

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed
    registration_open = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rounds = db.relationship('Round', backref='competition', lazy=True, cascade='all, delete-orphan')

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id', ondelete='CASCADE'))
    round_type = db.Column(db.String(20))  # preliminary, semifinal, final
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pairings = db.relationship('Pairing', backref='round', lazy=True, cascade='all, delete-orphan')

class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id', ondelete='CASCADE'))
    leader_id = db.Column(db.Integer, db.ForeignKey('dancer.id', ondelete='CASCADE'))
    follower_id = db.Column(db.Integer, db.ForeignKey('dancer.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scores = db.relationship('Score', backref='pairing', lazy=True, cascade='all, delete-orphan')

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairing.id', ondelete='CASCADE'))
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    timing = db.Column(db.Float)
    technique = db.Column(db.Float)
    connection = db.Column(db.Float)
    musicality = db.Column(db.Float)
    presentation = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
