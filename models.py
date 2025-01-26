from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association tables for many-to-many relationships
user_competitions = db.Table('user_competitions',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dance_role = db.Column(db.String(20), nullable=False)  # leader, follower
    is_admin = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(200))  # Path to profile picture
    instagram = db.Column(db.String(50))  # Instagram username
    
    # Relationships
    competitions = db.relationship('Competition', secondary=user_competitions, back_populates='users')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.id)

    @property
    def username(self):
        return self.email

    def __repr__(self):
        return f'<User {self.email}>'

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    dance_style = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    banner = db.Column(db.String(200))
    registration_open = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='upcoming')  # 'upcoming', 'ongoing', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary=user_competitions, back_populates='competitions')
    rounds = db.relationship('Round', backref='competition', lazy=True)

    def __repr__(self):
        return f'<Competition {self.name}>'

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    round_type = db.Column(db.String(20))  # 'preliminary', 'semifinal', 'final'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'ongoing', 'completed'
    
    # Relationships
    pairings = db.relationship('Pairing', backref='round', lazy=True)

    def __repr__(self):
        return f'<Round {self.number} of Competition {self.competition_id}>'

class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    leader = db.relationship('User', foreign_keys=[leader_id])
    follower = db.relationship('User', foreign_keys=[follower_id])
    scores = db.relationship('Score', backref='pairing', lazy=True)

    def __repr__(self):
        return f'<Pairing {self.id} in Round {self.round_id}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairing.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    criteria = db.Column(db.String(50))  # e.g., 'technique', 'musicality', 'presentation'
    
    # Relationship
    judge = db.relationship('User')

    def __repr__(self):
        return f'<Score {self.value} by Judge {self.judge_id} for Pairing {self.pairing_id}>'
